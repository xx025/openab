"""Discord bot: receive messages → call agent → reply (chunked). 配置通过参数传入，不读环境变量。"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import discord
from discord import Intents

from openab.agents import run_agent_async
from openab.core.config import load_config, parse_allowed_user_ids, try_add_allowlist_by_api_token
from openab.core.i18n import lang_from_env, t

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2000
PREFIX = "!"


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


class OpenABDiscordBot(discord.Client):
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
        super().__init__(intents=intents)
        self._openab_allowed = allowed_user_ids
        self._openab_allow_all = allow_all
        self._openab_config_path = Path(config_path).resolve() if config_path else None
        self._openab_workspace = workspace
        self._openab_timeout = timeout
        self._openab_agent_config = agent_config or {}

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

        try:
            reply = await run_agent_async(
                prompt,
                workspace=self._openab_workspace,
                timeout=self._openab_timeout,
                lang=lang,
                agent_config=self._openab_agent_config,
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
