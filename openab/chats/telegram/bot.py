"""Telegram bot: receive messages → call agent → reply (chunked)."""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Set

from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

from openab.agents import run_agent_async
from openab.core.i18n import lang_from_telegram, t

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096


def _allowed_user_ids() -> Set[int]:
    raw = os.environ.get("ALLOWED_USER_IDS", "").strip()
    if not raw:
        return set()
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


def _is_auth_enabled() -> bool:
    return len(_allowed_user_ids()) > 0


def _is_user_allowed(user_id: int) -> bool:
    allowed = _allowed_user_ids()
    if not allowed:
        return False
    return user_id in allowed


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


async def _send_typing_until_done(chat_id: int, context: ContextTypes.DEFAULT_TYPE, done: asyncio.Event) -> None:
    while not done.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception as e:
            logger.debug("send_chat_action: %s", e)
        try:
            await asyncio.wait_for(done.wait(), timeout=4.0)
        except asyncio.TimeoutError:
            continue


def _user_lang(update: Update) -> str:
    if update.effective_user and update.effective_user.language_code:
        return lang_from_telegram(update.effective_user.language_code)
    return "en"


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = _user_lang(update)
    if _is_user_allowed(user_id):
        msg = t(lang, "start_welcome")
    else:
        key = "auth_not_configured" if not _is_auth_enabled() else "unauthorized"
        msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + f"<code>{user_id}</code>"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = _user_lang(update)
    raw_username = update.effective_user.username
    username_display = ("@" + raw_username) if raw_username else t(lang, "username_not_set")
    status = t(lang, "status_authorized") if _is_user_allowed(user_id) else t(lang, "status_unauthorized")
    msg = (
        f"{t(lang, 'whoami_id')}<code>{user_id}</code>\n"
        f"{t(lang, 'whoami_username')}{username_display}\n"
        f"{t(lang, 'whoami_status')}{status}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id if update.effective_user else 0
    lang = _user_lang(update)
    if not _is_user_allowed(user_id):
        key = "auth_not_configured" if not _is_auth_enabled() else "unauthorized"
        msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + f"<code>{user_id}</code>"
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text(t(lang, "prompt_empty"))
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    done = asyncio.Event()
    typing_task = asyncio.create_task(_send_typing_until_done(chat_id, context, done))

    workspace = os.environ.get("OPENAB_WORKSPACE") or os.environ.get("CURSOR_WORKSPACE")
    workspace_path = Path(workspace).resolve() if workspace else None
    timeout = int(os.environ.get("OPENAB_AGENT_TIMEOUT") or os.environ.get("CURSOR_AGENT_TIMEOUT", "300"))

    try:
        reply = await run_agent_async(
            prompt,
            workspace=workspace_path,
            timeout=timeout,
            lang=lang,
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
        await update.message.reply_text(chunk)


def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


def run_bot(
    token: str,
    *,
    workspace: Optional[Path] = None,
) -> None:
    if workspace is not None:
        os.environ["OPENAB_WORKSPACE"] = str(workspace)
    app = build_application(token)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
