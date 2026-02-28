"""中英文文案适配。根据 Telegram 的 language_code 或 LANG 选择 zh / en。"""
from __future__ import annotations

from typing import Any

# 文案 key -> zh / en
MESSAGES = {
    "zh": {
        "unauthorized": (
            "您没有权限使用此机器人。\n\n"
            "【增加鉴权】请将你的 Telegram User ID 提供给管理员，由管理员将你的 ID 加入白名单（ALLOWED_USER_IDS）后即可使用。\n\n"
            "发送 /whoami 可查看你的 User ID。"
        ),
        "start_welcome": (
            "你好，这是 Cursor × Telegram 机器人。\n\n"
            "直接发送任意文字，我会把它交给 Cursor Agent 处理并回复你。\n\n"
            "输入 /whoami 可查看你的 Telegram User ID。"
        ),
        "your_user_id": "你的 User ID：",
        "whoami_id": "你的 Telegram User ID：",
        "whoami_username": "用户名：",
        "whoami_status": "鉴权状态：",
        "status_authorized": "已授权",
        "status_unauthorized": "未授权",
        "username_not_set": "(未设置)",
        "prompt_empty": "请发送一段文字作为给 Cursor Agent 的提示。",
        "agent_error": "执行出错：{error}",
        "agent_timeout": "⏱ 执行超时，请缩短问题或稍后重试。",
        "agent_no_output": "（无文本输出）",
        "auth_not_configured": (
            "管理员尚未配置鉴权白名单（ALLOWED_USER_IDS），机器人暂不可用。\n\n"
            "发送 /whoami 可查看你的 User ID，提供给管理员配置后即可开放使用。"
        ),
    },
    "en": {
        "unauthorized": (
            "You don't have permission to use this bot.\n\n"
            "[Get access] Ask the admin to add your Telegram User ID to the allowlist (ALLOWED_USER_IDS), then you can use the bot.\n\n"
            "Send /whoami to see your User ID."
        ),
        "start_welcome": (
            "Hi, this is the Cursor × Telegram bot.\n\n"
            "Send any text and I'll pass it to Cursor Agent and reply with the result.\n\n"
            "Send /whoami to see your Telegram User ID."
        ),
        "your_user_id": "Your User ID: ",
        "whoami_id": "Your Telegram User ID: ",
        "whoami_username": "Username: ",
        "whoami_status": "Auth status: ",
        "status_authorized": "Authorized",
        "status_unauthorized": "Not authorized",
        "username_not_set": "(not set)",
        "prompt_empty": "Please send some text as the prompt for Cursor Agent.",
        "agent_error": "Error: {error}",
        "agent_timeout": "⏱ Request timed out. Try a shorter prompt or try again later.",
        "agent_no_output": "(no text output)",
        "auth_not_configured": (
            "Auth allowlist (ALLOWED_USER_IDS) is not configured yet. The bot is not available.\n\n"
            "Send /whoami to see your User ID and ask the admin to configure it."
        ),
    },
}

# CLI 文案（按 LANG 环境变量）
CLI_MESSAGES = {
    "zh": {
        "cli_help": "Cursor CLI × Telegram 机器人",
        "opt_token": "Telegram Bot Token",
        "opt_workspace": "Cursor Agent 工作目录",
        "opt_verbose": "打印调试日志",
        "run_help": "启动机器人（长轮询）。",
        "err_no_token": "错误: 请设置 TELEGRAM_BOT_TOKEN 或使用 --token 传入。",
        "starting": "正在启动 Cursor × Telegram 机器人（长轮询）…",
    },
    "en": {
        "cli_help": "Cursor CLI × Telegram Bot",
        "opt_token": "Telegram Bot Token",
        "opt_workspace": "Cursor Agent workspace directory",
        "opt_verbose": "Enable verbose logging",
        "run_help": "Run the bot (long polling).",
        "err_no_token": "Error: Set TELEGRAM_BOT_TOKEN or pass --token.",
        "starting": "Starting Cursor × Telegram bot (long polling)…",
    },
}

DEFAULT_LANG = "en"


def _normalize_lang(code: str | None) -> str:
    """Telegram language_code 或 LANG → 'zh' | 'en'。"""
    if not code:
        return DEFAULT_LANG
    code = (code or "").strip().lower()
    if code.startswith("zh"):
        return "zh"
    return "en"


def lang_from_telegram(language_code: str | None) -> str:
    """根据 Telegram 用户的 language_code 返回 'zh' 或 'en'。"""
    return _normalize_lang(language_code)


def lang_from_env() -> str:
    """根据环境变量 LANG / LANGUAGE 返回 'zh' 或 'en'（用于 CLI）。"""
    import os
    for key in ("LANG", "LANGUAGE", "LC_ALL"):
        val = os.environ.get(key, "")
        if val:
            return _normalize_lang(val.split(":")[0].split(".")[0])
    return DEFAULT_LANG


def t(lang: str, key: str, **kwargs: Any) -> str:
    """取文案。lang 为 'zh' 或 'en'，key 为 MESSAGES 中的键，kwargs 用于 format。"""
    locale = "zh" if lang == "zh" else "en"
    msg = MESSAGES[locale].get(key, MESSAGES[DEFAULT_LANG].get(key, key))
    if kwargs:
        return msg.format(**kwargs)
    return msg


def cli_t(key: str, **kwargs: Any) -> str:
    """CLI 文案，按 LANG 环境变量。"""
    lang = lang_from_env()
    locale = "zh" if lang == "zh" else "en"
    msg = CLI_MESSAGES[locale].get(key, CLI_MESSAGES[DEFAULT_LANG].get(key, key))
    if kwargs:
        return msg.format(**kwargs)
    return msg
