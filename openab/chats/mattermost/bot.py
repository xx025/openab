"""Mattermost bot: WebSocket events → call agent → reply in thread (chunked). 配置通过参数传入，不读环境变量。"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

import aiohttp

from openab.agents import get_backend, run_agent_async
from openab.core.config import load_config, parse_allowed_user_ids_str, try_add_allowlist_by_api_token
from openab.core.codex_sessions import list_codex_sessions
from openab.core.cursor_chats import list_cursor_sessions
from openab.core.cursor_session_state import (
    set_new_session_next,
    set_resume_id,
    build_agent_config_with_session,
)
from openab.core.i18n import lang_from_env, t

logger = logging.getLogger(__name__)

# Server default max_post_size is 16383; leave headroom for the chunk prefix.
MAX_MESSAGE_LENGTH = 12000
PREFIX = "!"
_TYPING_INTERVAL = 4.0
_RECONNECT_MAX_SECONDS = 30


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


def _user_lang() -> str:
    return lang_from_env()


class OpenABMattermostBot:
    """Long-lived Mattermost connection: REST for posts, WebSocket for events.

    Reacts to direct messages and to channel messages that @mention the bot;
    everything else in a channel is other people's conversation and ignored.
    Replies always go into the post's thread, which is where Mattermost users
    expect a bot's answer.
    """

    def __init__(
        self,
        server_url: str,
        token: str,
        *,
        workspace: Path,
        timeout: int = 300,
        allowed_user_ids: frozenset[str],
        allow_all: bool = False,
        config_path: Optional[Path] = None,
        agent_config: Optional[dict[str, Any]] = None,
    ) -> None:
        self._base = server_url.rstrip("/")
        self._token = token
        self._workspace = workspace
        self._timeout = timeout
        self._allowed = allowed_user_ids
        self._allow_all = allow_all
        self._config_path = Path(config_path).resolve() if config_path else None
        self._agent_config = agent_config or {}
        self._me_id: str = ""
        self._username: str = ""
        self._mention_re: Optional[re.Pattern[str]] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_lock = asyncio.Lock()
        self._ws_seq = 1

    # ----- REST -----

    async def _api(self, method: str, path: str, payload: Optional[dict] = None) -> Any:
        assert self._session is not None
        async with self._session.request(
            method,
            f"{self._base}/api/v4{path}",
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status >= 400:
                body = (await resp.text())[:200]
                raise RuntimeError(f"Mattermost {method} {path}: HTTP {resp.status} {body}")
            return await resp.json()

    async def _reply(self, channel_id: str, root_id: str, text: str) -> None:
        for chunk in _split_message(text):
            await self._api("POST", "/posts", {
                "channel_id": channel_id,
                "message": chunk,
                "root_id": root_id,
            })

    # ----- WebSocket -----

    async def _ws_send(self, payload: dict) -> None:
        """Serialised: agent tasks send typing indicators while the read loop owns the socket."""
        async with self._ws_lock:
            ws = self._ws
            if ws is None or ws.closed:
                return
            payload = {**payload, "seq": self._ws_seq}
            self._ws_seq += 1
            await ws.send_json(payload)

    async def _typing_until_done(self, channel_id: str, root_id: str, done: asyncio.Event) -> None:
        while not done.is_set():
            try:
                await self._ws_send({
                    "action": "user_typing",
                    "data": {"channel_id": channel_id, "parent_id": root_id},
                })
            except Exception as e:  # noqa: BLE001 - typing is cosmetic, never fatal
                logger.debug("user_typing: %s", e)
            try:
                await asyncio.wait_for(done.wait(), timeout=_TYPING_INTERVAL)
            except asyncio.TimeoutError:
                continue

    # ----- Auth -----

    def _refresh_allow_from_config(self) -> None:
        """从配置文件重新读取白名单与 allow_all，使 allowlist add 动态生效。"""
        if self._config_path is None or not self._config_path.is_file():
            return
        try:
            cfg = load_config(self._config_path)
            mm = cfg.get("mattermost") or {}
            self._allowed = parse_allowed_user_ids_str(mm.get("allowed_user_ids"))
            self._allow_all = mm.get("allow_all") is True
        except Exception:
            pass

    def _is_user_allowed(self, user_id: str) -> bool:
        self._refresh_allow_from_config()
        if self._allow_all:
            return True
        return user_id in self._allowed

    def _is_auth_enabled(self) -> bool:
        self._refresh_allow_from_config()
        return len(self._allowed) > 0

    def _unauthorized_message(self, lang: str, user_id: str) -> str:
        key = "auth_not_configured" if not self._is_auth_enabled() else "unauthorized"
        msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + f"`{user_id}`"
        msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add --mattermost {user_id}")
        msg += "\n\n" + t(lang, "auth_allow_all_hint_mattermost")
        return msg

    # ----- Commands -----

    async def _handle_command(self, command: str, channel_id: str, root_id: str, user_id: str, username: str) -> bool:
        lang = _user_lang()
        parts = command.split(maxsplit=1)
        name = parts[0].lower()
        if name == "start":
            if self._is_user_allowed(user_id):
                await self._reply(channel_id, root_id, t(lang, "start_welcome_mattermost"))
            else:
                await self._reply(channel_id, root_id, self._unauthorized_message(lang, user_id))
            return True
        if name == "whoami":
            status = t(lang, "status_authorized") if self._is_user_allowed(user_id) else t(lang, "status_unauthorized")
            await self._reply(channel_id, root_id, (
                f"{t(lang, 'whoami_id_mattermost')}`{user_id}`\n"
                f"{t(lang, 'whoami_username')}@{username}\n"
                f"{t(lang, 'whoami_status')}{status}"
            ))
            return True
        if name == "new":
            if not self._is_user_allowed(user_id):
                await self._reply(channel_id, root_id, t(lang, "unauthorized"))
                return True
            set_new_session_next("mm", channel_id, user_id)
            await self._reply(channel_id, root_id, t(lang, "session_new_created"))
            return True
        if name == "resume":
            if not self._is_user_allowed(user_id):
                await self._reply(channel_id, root_id, t(lang, "unauthorized"))
                return True
            session_id = parts[1].strip() if len(parts) > 1 else None
            if session_id:
                set_resume_id("mm", channel_id, user_id, session_id)
                await self._reply(channel_id, root_id, t(lang, "session_resume_switched", id=session_id))
            else:
                # Mattermost interactive buttons need a server-reachable callback
                # URL, which a locally running bot does not have, so the list is
                # text and the switch is `!resume <id>`.
                backend = get_backend(self._agent_config)
                sessions = list_codex_sessions(max_sessions=12) if backend == "codex" else list_cursor_sessions(max_sessions=12)
                lines = [t(lang, "session_resume_usage_mattermost")]
                for sid, display in sessions:
                    lines.append(f"- `{sid}` — {display}")
                await self._reply(channel_id, root_id, "\n".join(lines))
            return True
        if name == "sessions":
            if not self._is_user_allowed(user_id):
                await self._reply(channel_id, root_id, t(lang, "unauthorized"))
                return True
            await self._reply(channel_id, root_id, t(lang, "session_resume_usage_mattermost"))
            return True
        return False

    # ----- Messages -----

    def _strip_mention(self, text: str) -> str:
        if self._mention_re is None:
            return text.strip()
        return self._mention_re.sub(" ", text).strip()

    async def _on_posted(self, payload: dict) -> None:
        data = payload.get("data") or {}
        try:
            post = json.loads(data.get("post") or "{}")
        except json.JSONDecodeError:
            logger.warning("Ignored a posted event with invalid post JSON")
            return
        user_id = str(post.get("user_id") or "")
        if not user_id or user_id == self._me_id:
            return
        if post.get("type"):
            return  # system messages (joins, headers, …), never work
        message = post.get("message") or ""
        mentioned = bool(self._mention_re and self._mention_re.search(message))
        if data.get("channel_type") != "D" and not mentioned:
            return

        channel_id = str(post.get("channel_id") or "")
        root_id = str(post.get("root_id") or "") or str(post.get("id") or "")
        username = str(data.get("sender_name") or "").lstrip("@") or user_id
        text = self._strip_mention(message)
        lang = _user_lang()

        if try_add_allowlist_by_api_token(self._config_path, "mattermost", user_id, text):
            await self._reply(channel_id, root_id, t(lang, "allowlist_added_by_token"))
            return
        stripped = text.strip()
        if stripped.startswith(PREFIX) and await self._handle_command(
            stripped[len(PREFIX):], channel_id, root_id, user_id, username
        ):
            return
        if not self._is_user_allowed(user_id):
            await self._reply(channel_id, root_id, self._unauthorized_message(lang, user_id))
            return
        if not stripped:
            await self._reply(channel_id, root_id, t(lang, "prompt_empty"))
            return

        done = asyncio.Event()
        typing_task = asyncio.create_task(self._typing_until_done(channel_id, root_id, done))
        agent_config = build_agent_config_with_session(self._agent_config, "mm", channel_id, user_id)
        try:
            reply = await run_agent_async(
                stripped,
                workspace=self._workspace,
                timeout=self._timeout,
                lang=lang,
                agent_config=agent_config,
            )
        except Exception as e:  # noqa: BLE001 - the requester still gets an answer
            logger.exception("agent run error")
            reply = t(lang, "agent_error", error=str(e))
        finally:
            done.set()
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

        await self._reply(channel_id, root_id, reply)

    # ----- Lifecycle -----

    async def _listen(self) -> None:
        assert self._session is not None
        ws_url = re.sub(r"^http", "ws", self._base, count=1) + "/api/v4/websocket"
        async with self._session.ws_connect(ws_url, heartbeat=30) as ws:
            self._ws = ws
            await self._ws_send({
                "action": "authentication_challenge",
                "data": {"token": self._token},
            })
            logger.info("Mattermost websocket connected as @%s", self._username)
            try:
                async for msg in ws:
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        continue
                    try:
                        payload = json.loads(msg.data)
                    except json.JSONDecodeError:
                        continue
                    if payload.get("event") == "posted":
                        task = asyncio.create_task(self._on_posted(payload))
                        task.add_done_callback(_log_task_error)
            finally:
                self._ws = None

    async def run(self) -> None:
        backoff = 1
        async with aiohttp.ClientSession() as session:
            self._session = session
            me = await self._api("GET", "/users/me")
            self._me_id = str(me["id"])
            self._username = str(me["username"])
            self._mention_re = re.compile(
                rf"(?:^|\s)@{re.escape(self._username)}(?=$|[\s,.;:!?，。；：！？])",
                re.IGNORECASE,
            )
            logger.info("Mattermost bot logged in as @%s (%s)", self._username, self._me_id)
            while True:
                started = asyncio.get_event_loop().time()
                try:
                    await self._listen()
                    logger.warning("Mattermost websocket closed; reconnecting in %ss", backoff)
                except asyncio.CancelledError:
                    raise
                except Exception as e:  # noqa: BLE001 - reconnect instead of dying
                    logger.warning("Mattermost websocket error: %s; reconnecting in %ss", e, backoff)
                # A connection that lived a while earns a fresh backoff.
                if asyncio.get_event_loop().time() - started > 60:
                    backoff = 1
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _RECONNECT_MAX_SECONDS)


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.exception("Message handler failed", exc_info=exc)


def run_bot(
    server_url: str,
    token: str,
    *,
    workspace: Path,
    timeout: int = 300,
    allowed_user_ids: Optional[frozenset[str]] = None,
    allow_all: bool = False,
    config_path: Optional[Path] = None,
    agent_config: Optional[dict[str, Any]] = None,
) -> None:
    bot = OpenABMattermostBot(
        server_url,
        token,
        workspace=workspace,
        timeout=timeout,
        allowed_user_ids=allowed_user_ids or frozenset(),
        allow_all=allow_all,
        config_path=config_path,
        agent_config=agent_config,
    )
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass
