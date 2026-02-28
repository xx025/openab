"""Telegram bot: receive messages → call agent → reply (chunked). 配置通过参数传入，不读环境变量。"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

from openab.agents import run_agent_async
from openab.core.i18n import lang_from_telegram, t

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096


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
    from openab.core.i18n import lang_from_env
    return lang_from_env()


def _allowed(context: ContextTypes.DEFAULT_TYPE) -> frozenset[int]:
    return context.bot_data.get("openab_allowed_user_ids") or frozenset()


def _is_auth_enabled(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return len(_allowed(context)) > 0


def _is_user_allowed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    allowed = _allowed(context)
    if len(allowed) == 0:
        return True  # 未设置白名单时允许所有人（启动时已警告）
    return user_id in allowed


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = _user_lang(update)
    if _is_user_allowed(user_id, context):
        msg = t(lang, "start_welcome")
    else:
        msg = t(lang, "unauthorized") + "\n\n" + t(lang, "your_user_id") + f"<code>{user_id}</code>"
        msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add {user_id}")
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = _user_lang(update)
    raw_username = update.effective_user.username
    username_display = ("@" + raw_username) if raw_username else t(lang, "username_not_set")
    status = t(lang, "status_authorized") if _is_user_allowed(user_id, context) else t(lang, "status_unauthorized")
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
    if not _is_user_allowed(user_id, context):
        msg = t(lang, "unauthorized") + "\n\n" + t(lang, "your_user_id") + f"<code>{user_id}</code>"
        msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add {user_id}")
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    prompt = update.message.text.strip()
    if not prompt:
        await update.message.reply_text(t(lang, "prompt_empty"))
        return

    chat_id = update.effective_chat.id if update.effective_chat else 0
    done = asyncio.Event()
    typing_task = asyncio.create_task(_send_typing_until_done(chat_id, context, done))

    workspace: Optional[Path] = context.bot_data.get("openab_workspace")
    timeout: int = context.bot_data.get("openab_timeout", 300)
    agent_config: Optional[dict[str, Any]] = context.bot_data.get("openab_agent_config")

    try:
        reply = await run_agent_async(
            prompt,
            workspace=workspace,
            timeout=timeout,
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
        await update.message.reply_text(chunk)


def build_application(
    token: str,
    *,
    workspace: Path,
    timeout: int = 300,
    allowed_user_ids: frozenset[int],
    agent_config: Optional[dict[str, Any]] = None,
) -> Application:
    app = Application.builder().token(token).build()
    app.bot_data["openab_workspace"] = workspace
    app.bot_data["openab_timeout"] = timeout
    app.bot_data["openab_allowed_user_ids"] = allowed_user_ids
    app.bot_data["openab_agent_config"] = agent_config or {}
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


def run_bot(
    token: str,
    *,
    workspace: Path,
    timeout: int = 300,
    allowed_user_ids: Optional[frozenset[int]] = None,
    agent_config: Optional[dict[str, Any]] = None,
) -> None:
    ids = allowed_user_ids or frozenset()
    app = build_application(
        token,
        workspace=workspace,
        timeout=timeout,
        allowed_user_ids=ids,
        agent_config=agent_config,
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)
