"""Telegram bot: receive messages → call agent → reply (chunked). 配置通过参数传入，不读环境变量。"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import Conflict

from openab.agents import get_backend, run_agent_async
from openab.core.config import load_config, parse_allowed_user_ids, try_add_allowlist_by_api_token
from openab.core.codex_sessions import list_codex_sessions
from openab.core.cursor_chats import list_cursor_sessions
from openab.core.cursor_session_state import (
    set_new_session_next,
    set_resume_id,
    build_agent_config_with_session,
)
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
    """白名单：若配置了 config_path 则每次从文件重新读取，实现动态生效。"""
    path = context.bot_data.get("openab_config_path")
    if path is not None and path.is_file():
        try:
            cfg = load_config(path)
            return parse_allowed_user_ids((cfg.get("telegram") or {}).get("allowed_user_ids"))
        except Exception:
            pass
    return context.bot_data.get("openab_allowed_user_ids") or frozenset()


def _allow_all(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """若配置了 config_path 则每次从文件重新读取。"""
    path = context.bot_data.get("openab_config_path")
    if path is not None and path.is_file():
        try:
            cfg = load_config(path)
            return (cfg.get("telegram") or {}).get("allow_all") is True
        except Exception:
            pass
    return context.bot_data.get("openab_allow_all") is True


def _is_auth_enabled(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return len(_allowed(context)) > 0


def _is_user_allowed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if _allow_all(context):
        return True
    return user_id in _allowed(context)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = _user_lang(update)
    if _is_user_allowed(user_id, context):
        msg = t(lang, "start_welcome")
    else:
        key = "auth_not_configured" if not _is_auth_enabled(context) else "unauthorized"
        msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + f"<code>{user_id}</code>"
        msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add {user_id}")
        msg += "\n\n" + t(lang, "auth_allow_all_hint")
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


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """创建新会话：下一条消息将在新会话中处理（Cursor/Codex 后端生效）。"""
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    lang = _user_lang(update)
    if not _is_user_allowed(user_id, context):
        await update.message.reply_text(t(lang, "unauthorized"))
        return
    set_new_session_next("tg", chat_id, user_id)
    await update.message.reply_text(t(lang, "session_new_created"))


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """切换/恢复会话：/resume [会话ID] 或点击下方按钮。"""
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    lang = _user_lang(update)
    if not _is_user_allowed(user_id, context):
        await update.message.reply_text(t(lang, "unauthorized"))
        return
    args = (update.message.text or "").strip().split()
    session_id = args[1].strip() if len(args) > 1 else None
    if session_id:
        set_resume_id("tg", chat_id, user_id, session_id)
        await update.message.reply_text(t(lang, "session_resume_switched", id=session_id))
    else:
        keyboard = [
            [
                InlineKeyboardButton(t(lang, "btn_resume_latest"), callback_data="resume_latest"),
                InlineKeyboardButton(t(lang, "btn_new_session"), callback_data="new_session"),
            ],
        ]
        backend = get_backend(context.bot_data.get("openab_agent_config"))
        sessions = list_codex_sessions(max_sessions=12) if backend == "codex" else list_cursor_sessions(max_sessions=12)
        for session_id, display_name in sessions:
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"resume:{session_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(t(lang, "session_resume_choose"), reply_markup=reply_markup)


async def handle_resume_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /resume 下方的按钮点击。"""
    query = update.callback_query
    if not query or not query.data or not query.from_user or not query.message:
        return
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat.id if query.message.chat else 0
    lang = _user_lang(update)
    if not _is_user_allowed(user_id, context):
        await query.edit_message_text(t(lang, "unauthorized"))
        return
    if query.data == "resume_latest":
        set_resume_id("tg", chat_id, user_id, None)
        await query.edit_message_text(t(lang, "session_resume_latest"))
    elif query.data == "new_session":
        set_new_session_next("tg", chat_id, user_id)
        await query.edit_message_text(t(lang, "session_new_created"))
    elif query.data.startswith("resume:"):
        session_id = query.data[7:].strip()
        if session_id:
            set_resume_id("tg", chat_id, user_id, session_id)
            await query.edit_message_text(t(lang, "session_resume_switched", id=session_id))


async def cmd_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """列出会话说明（当前无法在机器人中列出，提示用 /resume <ID>）。"""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    lang = _user_lang(update)
    if not _is_user_allowed(user_id, context):
        await update.message.reply_text(t(lang, "unauthorized"))
        return
    await update.message.reply_text(t(lang, "sessions_list_unavailable") + "\n\n" + t(lang, "session_resume_usage"))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id if update.effective_user else 0
    lang = _user_lang(update)
    config_path = context.bot_data.get("openab_config_path")
    if try_add_allowlist_by_api_token(config_path, "telegram", user_id, update.message.text):
        await update.message.reply_text(t(lang, "allowlist_added_by_token"))
        return
    if not _is_user_allowed(user_id, context):
        key = "auth_not_configured" if not _is_auth_enabled(context) else "unauthorized"
        msg = t(lang, key) + "\n\n" + t(lang, "your_user_id") + f"<code>{user_id}</code>"
        msg += "\n\n" + t(lang, "unauthorized_cli_hint", cmd=f"openab allowlist add {user_id}")
        msg += "\n\n" + t(lang, "auth_allow_all_hint")
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
    base_agent_config = context.bot_data.get("openab_agent_config") or {}
    agent_config = build_agent_config_with_session(base_agent_config, "tg", chat_id, user_id)

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


def _error_handler(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """统一错误处理：Conflict 时提示并退出，其余记录日志。"""
    err = context.error
    if isinstance(err, Conflict):
        logger.error(
            "Telegram Conflict: another bot instance is running with the same token. "
            "Stop other instances (e.g. pkill -f 'openab run'), wait a few seconds, then start again."
        )
        sys.exit(1)
    logger.exception("Bot error: %s", err, exc_info=err)


# 命令菜单：用户输入 / 时 Telegram 会显示该列表（需通过 set_my_commands 注册）
TELEGRAM_COMMANDS_EN = [
    BotCommand("start", "Welcome and auth status"),
    BotCommand("whoami", "Show your Telegram user ID"),
    BotCommand("new", "Create new session (next message in new conversation)"),
    BotCommand("resume", "Resume previous or switch to session: /resume [ID]"),
    BotCommand("sessions", "How to view and switch sessions"),
]
TELEGRAM_COMMANDS_ZH = [
    BotCommand("start", "欢迎与鉴权状态"),
    BotCommand("whoami", "查看你的 Telegram 用户 ID"),
    BotCommand("new", "创建新会话（下一条消息在新会话中）"),
    BotCommand("resume", "恢复上一会话或切换：/resume [会话ID]"),
    BotCommand("sessions", "如何查看与切换会话"),
]


async def _post_init_set_commands(application: Application) -> None:
    """Bot 启动后向 Telegram 注册命令菜单，使输入 / 时显示命令列表。"""
    bot = application.bot
    await bot.set_my_commands(TELEGRAM_COMMANDS_EN)
    try:
        await bot.set_my_commands(TELEGRAM_COMMANDS_ZH, language_code="zh-hans")
    except Exception as e:
        logger.debug("Set commands for zh-hans skipped: %s", e)


def build_application(
    token: str,
    *,
    workspace: Path,
    timeout: int = 300,
    allowed_user_ids: frozenset[int],
    allow_all: bool = False,
    config_path: Optional[Path] = None,
    agent_config: Optional[dict[str, Any]] = None,
) -> Application:
    app = (
        Application.builder()
        .token(token)
        .post_init(_post_init_set_commands)
        .build()
    )
    app.bot_data["openab_workspace"] = workspace
    app.bot_data["openab_timeout"] = timeout
    app.bot_data["openab_allowed_user_ids"] = allowed_user_ids
    app.bot_data["openab_allow_all"] = allow_all
    app.bot_data["openab_config_path"] = Path(config_path).resolve() if config_path else None
    app.bot_data["openab_agent_config"] = agent_config or {}
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("whoami", cmd_whoami))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("sessions", cmd_sessions))
    app.add_handler(CallbackQueryHandler(handle_resume_callback, pattern="^resume_latest$|^new_session$|^resume:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(_error_handler)
    return app


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
    app = build_application(
        token,
        workspace=workspace,
        timeout=timeout,
        allowed_user_ids=ids,
        allow_all=allow_all,
        config_path=config_path,
        agent_config=agent_config,
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)
