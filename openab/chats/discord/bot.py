"""Discord bot: receive messages → call agent → reply (chunked). 配置通过参数传入，不读环境变量。"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import discord
from discord import Intents
from discord.ext import commands

from openab.agents import run_agent_async
from openab.core.config import load_config, parse_allowed_user_ids, try_add_allowlist_by_api_token
from openab.core.cursor_chats import list_cursor_sessions
from openab.core.cursor_session_state import (
    set_new_session_next,
    set_resume_id,
    build_agent_config_with_session,
)
from openab.core.i18n import lang_from_env, t

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2000
PREFIX = "!"


class _ResumeChoiceView(discord.ui.View):
    """Resume 按钮：延续上一会话、创建新会话、以及历史会话列表（从 ~/.cursor/chats 读取）。"""

    def __init__(
        self,
        bot: "OpenABDiscordBot",
        lang: str,
        *,
        timeout: float = 60.0,
        sessions: Optional[list[tuple[str, str]]] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self._openab_bot = bot
        self._lang = lang
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "openab_resume_latest":
                    child.label = t(lang, "btn_resume_latest")
                elif child.custom_id == "openab_new_session":
                    child.label = t(lang, "btn_new_session")
        for row_idx, (session_id, display_name) in enumerate(sessions or [], start=0):
            btn = discord.ui.Button(
                label=(display_name[:80] if len(display_name) > 80 else display_name),
                custom_id=f"openab_resume:{session_id}",
                row=min(1 + row_idx // 5, 4),
            )
            btn.callback = self._make_resume_session_callback(session_id)
            self.add_item(btn)

    def _make_resume_session_callback(self, session_id: str):
        async def callback(interaction: discord.Interaction) -> None:
            if not interaction.user:
                return
            if not self._openab_bot._is_user_allowed(interaction.user.id):
                await interaction.response.send_message(t(self._lang, "unauthorized"), ephemeral=True)
                return
            set_resume_id("dc", interaction.channel_id or 0, interaction.user.id, session_id)
            await interaction.response.send_message(t(self._lang, "session_resume_switched", id=session_id))
        return callback

    @discord.ui.button(label=".", custom_id="openab_resume_latest", row=0)
    async def btn_resume_latest(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.user:
            return
        if not self._openab_bot._is_user_allowed(interaction.user.id):
            await interaction.response.send_message(t(self._lang, "unauthorized"), ephemeral=True)
            return
        set_resume_id("dc", interaction.channel_id or 0, interaction.user.id, None)
        await interaction.response.send_message(t(self._lang, "session_resume_latest"))

    @discord.ui.button(label=".", custom_id="openab_new_session", row=0)
    async def btn_new_session(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not interaction.user:
            return
        if not self._openab_bot._is_user_allowed(interaction.user.id):
            await interaction.response.send_message(t(self._lang, "unauthorized"), ephemeral=True)
            return
        set_new_session_next("dc", interaction.channel_id or 0, interaction.user.id)
        await interaction.response.send_message(t(self._lang, "session_new_created"))


def _split_message(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> list[str]:
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        cut = text.rfind("\n", 0, max_len + 1)
        if cut <= 0:
            cut = text.rfind(" ", 0, max_len + 1)
        if cut <= 0:
            cut = max_len
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    return chunks


def _user_lang(_message: discord.Message) -> str:
    return lang_from_env()


async def _typing_until_done(channel: discord.abc.Messageable, done: asyncio.Event) -> None:
    while not done.is_set():
        try:
            async with channel.typing():
                await asyncio.wait_for(done.wait(), timeout=4.0)
        except (asyncio.TimeoutError, discord.DiscordException):
            continue


class OpenABDiscordBot(commands.Bot):
    def __init__(
        self,
        *,
        intents: Intents,
        allowed_user_ids: frozenset[int],
        allow_all: bool = False,
        config_path: Optional[Path] = None,
        workspace: Path,
        timeout: int = 300,
        agent_config: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents)
        self._openab_allowed = allowed_user_ids
        self._openab_allow_all = allow_all
        self._openab_config_path = Path(config_path).resolve() if config_path else None
        self._openab_workspace = workspace
        self._openab_timeout = timeout
        self._openab_agent_config = agent_config or {}

    async def setup_hook(self) -> None:
        """注册斜杠命令，使用户输入 / 时显示命令列表。"""
        tree = self.tree

        @tree.command(name="start", description="Welcome and auth status")
        async def slash_start(interaction: discord.Interaction) -> None:
            await self._slash_start(interaction)

        @tree.command(name="whoami", description="Show your Discord user ID")
        async def slash_whoami(interaction: discord.Interaction) -> None:
            await self._slash_whoami(interaction)

        @tree.command(name="new", description="Create new session (next message in new conversation)")
        async def slash_new(interaction: discord.Interaction) -> None:
            await self._slash_new(interaction)

        @tree.command(name="resume", description="Resume previous session or switch to session by ID")
        @discord.app_commands.describe(session_id="Optional session ID to switch to (omit to resume latest)")
        async def slash_resume(interaction: discord.Interaction, session_id: Optional[str] = None) -> None:
            await self._slash_resume(interaction, session_id)

        @tree.command(name="sessions", description="How to view and switch sessions")
        async def slash_sessions(interaction: discord.Interaction) -> None:
            await self._slash_sessions(interaction)

        try:
            synced = await tree.sync()
            logger.info("Discord slash commands synced: %s", len(synced))
        except Exception as e:
            logger.warning("Discord tree.sync failed: %s", e)

    def _refresh_allow_from_config(self) -> None:
        """从配置文件重新读取白名单与 allow_all，使 allowlist add 动态生效。"""
        if self._openab_config_path is None or not self._openab_config_path.is_file():
            return
        try:
            cfg = load_config(self._openab_config_path)
            dc = cfg.get("discord") or {}
            self._openab_allowed = parse_allowed_user_ids(dc.get("allowed_user_ids"))
            self._openab_allow_all = dc.get("allow_all") is True
        except Exception:
            pass

    def _is_user_allowed(self, user_id: int) -> bool:
        self._refresh_allow_from_config()
        if self._openab_allow_all:
            return True
        return user_id in self._openab_allowed

    def _is_auth_enabled(self) -> bool:
        self._refresh_allow_from_config()
        return len(self._openab_allowed) > 0

    async def handle_command_start(self, message: discord.Message) -> None:
        lang = _user_lang(message)
        user_id = message.author.id
        if self._is_user_allowed(user_id):
            msg = t(lang, "start_welcome")
        else:
            key = "auth_not_configured" if not self._is_auth_enabled() else "unauthorized"
            msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + str(user_id)
            msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add --discord {user_id}")
            msg += "\n\n" + t(lang, "auth_allow_all_hint_discord")
        await message.reply(msg)

    async def handle_command_whoami(self, message: discord.Message) -> None:
        lang = _user_lang(message)
        user_id = message.author.id
        name = message.author.display_name or str(message.author)
        status = t(lang, "status_authorized") if self._is_user_allowed(user_id) else t(lang, "status_unauthorized")
        msg = (
            f"{t(lang, 'whoami_id')}{user_id}\n"
            f"{t(lang, 'whoami_username')}{name}\n"
            f"{t(lang, 'whoami_status')}{status}"
        )
        await message.reply(msg)

    async def handle_command_new(self, message: discord.Message) -> None:
        """创建新会话（下一条消息在新会话中处理）。"""
        if not self._is_user_allowed(message.author.id):
            await message.reply(t(_user_lang(message), "unauthorized"))
            return
        set_new_session_next("dc", message.channel.id, message.author.id)
        await message.reply(t(_user_lang(message), "session_new_created"))

    async def handle_command_resume(self, message: discord.Message) -> None:
        """!resume [会话ID] 或点击按钮选择。"""
        if not self._is_user_allowed(message.author.id):
            await message.reply(t(_user_lang(message), "unauthorized"))
            return
        lang = _user_lang(message)
        parts = (message.content or "").strip().split(maxsplit=1)
        session_id = parts[1].strip() if len(parts) > 1 else None
        if session_id:
            set_resume_id("dc", message.channel.id, message.author.id, session_id)
            await message.reply(t(lang, "session_resume_switched", id=session_id))
        else:
            sessions = list_cursor_sessions(max_sessions=12)
            view = _ResumeChoiceView(self, lang, sessions=sessions)
            await message.reply(t(lang, "session_resume_choose"), view=view)

    async def handle_command_sessions(self, message: discord.Message) -> None:
        """列出会话说明。"""
        if not self._is_user_allowed(message.author.id):
            await message.reply(t(_user_lang(message), "unauthorized"))
            return
        lang = _user_lang(message)
        await message.reply(t(lang, "sessions_list_unavailable") + "\n\n" + t(lang, "session_resume_usage_discord"))

    # ----- 斜杠命令实现（/ 命令列表用）-----
    async def _slash_start(self, interaction: discord.Interaction) -> None:
        lang = lang_from_env()
        user_id = interaction.user.id if interaction.user else 0
        if self._is_user_allowed(user_id):
            msg = t(lang, "start_welcome")
        else:
            key = "auth_not_configured" if not self._is_auth_enabled() else "unauthorized"
            msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + str(user_id)
            msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add --discord {user_id}")
            msg += "\n\n" + t(lang, "auth_allow_all_hint_discord")
        await interaction.response.send_message(msg)

    async def _slash_whoami(self, interaction: discord.Interaction) -> None:
        lang = lang_from_env()
        user = interaction.user
        user_id = user.id if user else 0
        name = user.display_name if user else ""
        status = t(lang, "status_authorized") if self._is_user_allowed(user_id) else t(lang, "status_unauthorized")
        msg = f"{t(lang, 'whoami_id')}{user_id}\n{t(lang, 'whoami_username')}{name}\n{t(lang, 'whoami_status')}{status}"
        await interaction.response.send_message(msg)

    async def _slash_new(self, interaction: discord.Interaction) -> None:
        if not interaction.user:
            return
        if not self._is_user_allowed(interaction.user.id):
            await interaction.response.send_message(t(lang_from_env(), "unauthorized"))
            return
        set_new_session_next("dc", interaction.channel_id or 0, interaction.user.id)
        await interaction.response.send_message(t(lang_from_env(), "session_new_created"))

    async def _slash_resume(self, interaction: discord.Interaction, session_id: Optional[str] = None) -> None:
        if not interaction.user:
            return
        if not self._is_user_allowed(interaction.user.id):
            await interaction.response.send_message(t(lang_from_env(), "unauthorized"))
            return
        lang = lang_from_env()
        sid = (session_id or "").strip() or None
        ch_id = interaction.channel_id or 0
        if sid:
            set_resume_id("dc", ch_id, interaction.user.id, sid)
            await interaction.response.send_message(t(lang, "session_resume_switched", id=sid))
        else:
            sessions = list_cursor_sessions(max_sessions=12)
            view = _ResumeChoiceView(self, lang, sessions=sessions)
            await interaction.response.send_message(t(lang, "session_resume_choose"), view=view)

    async def _slash_sessions(self, interaction: discord.Interaction) -> None:
        if not interaction.user:
            return
        if not self._is_user_allowed(interaction.user.id):
            await interaction.response.send_message(t(lang_from_env(), "unauthorized"))
            return
        lang = lang_from_env()
        await interaction.response.send_message(
            t(lang, "sessions_list_unavailable") + "\n\n" + t(lang, "session_resume_usage_discord")
        )

    async def handle_agent_message(self, message: discord.Message) -> None:
        user_id = message.author.id
        lang = _user_lang(message)
        content = (message.content or "").strip()
        if try_add_allowlist_by_api_token(self._openab_config_path, "discord", user_id, content):
            await message.reply(t(lang, "allowlist_added_by_token"))
            return
        if not self._is_user_allowed(user_id):
            key = "auth_not_configured" if not self._is_auth_enabled() else "unauthorized"
            msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + str(user_id)
            msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add --discord {user_id}")
            msg += "\n\n" + t(lang, "auth_allow_all_hint_discord")
            await message.reply(msg)
            return

        prompt = (message.content or "").strip()
        if not prompt:
            await message.reply(t(lang, "prompt_empty"))
            return

        done = asyncio.Event()
        typing_task = asyncio.create_task(_typing_until_done(message.channel, done))

        agent_config = build_agent_config_with_session(
            self._openab_agent_config,
            "dc",
            message.channel.id,
            message.author.id,
        )
        try:
            reply = await run_agent_async(
                prompt,
                workspace=self._openab_workspace,
                timeout=self._openab_timeout,
                lang=lang,
                agent_config=agent_config,
            )
        except Exception as e:
            logger.exception("agent run error")
            reply = t(lang, "agent_error", error=str(e))
        finally:
            done.set()
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

        for chunk in _split_message(reply):
            await message.reply(chunk)

    async def on_ready(self) -> None:
        logger.info("Discord bot logged in as %s", self.user)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        content = (message.content or "").strip()
        if content == f"{PREFIX}start":
            await self.handle_command_start(message)
            return
        if content == f"{PREFIX}whoami":
            await self.handle_command_whoami(message)
            return
        if content == f"{PREFIX}new":
            await self.handle_command_new(message)
            return
        if content.startswith(f"{PREFIX}resume"):
            await self.handle_command_resume(message)
            return
        if content == f"{PREFIX}sessions":
            await self.handle_command_sessions(message)
            return
        await self.handle_agent_message(message)


def run_bot(
    token: str,
    *,
    workspace: Path,
    timeout: int = 300,
    allowed_user_ids: Optional[frozenset[int]] = None,
    allow_all: bool = False,
    config_path: Optional[Path] = None,
    agent_config: Optional[dict[str, Any]] = None,
) -> None:
    ids = allowed_user_ids or frozenset()
    intents = Intents.default()
    intents.message_content = True
    client = OpenABDiscordBot(
        intents=intents,
        allowed_user_ids=ids,
        allow_all=allow_all,
        config_path=config_path,
        workspace=workspace,
        timeout=timeout,
        agent_config=agent_config,
    )
    client.run(token)
