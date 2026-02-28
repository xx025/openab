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
            "你好，这是 OpenAB 机器人。\n\n"
            "直接发送任意文字，我会把它交给已配置的智能体处理并回复你。\n\n"
            "输入 /whoami 可查看你的 Telegram User ID。"
        ),
        "your_user_id": "你的 User ID：",
        "whoami_id": "你的 Telegram User ID：",
        "whoami_username": "用户名：",
        "whoami_status": "鉴权状态：",
        "status_authorized": "已授权",
        "status_unauthorized": "未授权",
        "username_not_set": "(未设置)",
        "prompt_empty": "请发送一段文字作为给智能体的提示。",
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
            "Hi, this is the OpenAB bot.\n\n"
            "Send any text and I'll pass it to the configured agent and reply with the result.\n\n"
            "Send /whoami to see your Telegram User ID."
        ),
        "your_user_id": "Your User ID: ",
        "whoami_id": "Your Telegram User ID: ",
        "whoami_username": "Username: ",
        "whoami_status": "Auth status: ",
        "status_authorized": "Authorized",
        "status_unauthorized": "Not authorized",
        "username_not_set": "(not set)",
        "prompt_empty": "Please send some text as the prompt for the agent.",
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
        "cli_help": "OpenAB — 开放智能体桥接",
        "opt_token": "Telegram Bot Token",
        "opt_token_discord": "Discord Bot Token",
        "opt_workspace": "智能体工作目录",
        "opt_verbose": "打印调试日志",
        "run_help": "启动 Telegram 机器人（长轮询）。",
        "run_discord_help": "启动 Discord 机器人。",
        "err_no_token": "错误: 请设置 TELEGRAM_BOT_TOKEN 或使用 --token 传入。",
        "err_no_token_discord": "错误: 请设置 DISCORD_BOT_TOKEN 或使用 --token 传入。",
        "starting": "正在启动 OpenAB Telegram 机器人（长轮询）…",
        "starting_discord": "正在启动 OpenAB Discord 机器人…",
        "install_service_help": "一键安装为 Linux 用户级 systemd 服务。",
        "install_service_linux_only": "仅支持 Linux 平台。",
        "install_service_done": "已安装并启用用户服务：{path}\n使用 systemctl --user start openab 启动，或加 --start 立即启动。",
        "install_service_done_discord": "已安装并启用用户服务：{path}\n使用 systemctl --user start openab-discord 启动，或加 --start 立即启动。",
        "install_wizard_title": "OpenAB 服务安装向导（仅 Linux）",
        "install_wizard_which": "要安装哪种机器人服务？ 1) Telegram  2) Discord  3) 两者",
        "install_wizard_which_prompt": "请选择 [1-3]（默认 1）：",
        "install_wizard_telegram_token": "Telegram Bot Token（留空则跳过，稍后编辑配置文件）：",
        "install_wizard_telegram_allowed": "允许的 Telegram 用户 ID（逗号分隔，留空则跳过）：",
        "install_wizard_discord_token": "Discord Bot Token（留空则跳过）：",
        "install_wizard_discord_allowed": "允许的 Discord 用户 ID（逗号分隔，留空则跳过）：",
        "install_wizard_config_saved": "配置已写入：{path}",
        "install_wizard_start_now": "是否立即启动服务？ [y/N]：",
        "install_wizard_installing_telegram": "正在安装 Telegram 服务…",
        "install_wizard_installing_discord": "正在安装 Discord 服务…",
        "install_wizard_done": "安装完成。",
        "install_wizard_skip_interactive": "跳过交互，直接按当前参数安装（需已配置好 token 等）。",
        "run_prompt_telegram_token": "配置中未设置 Telegram Bot Token，请输入（或 Ctrl+C 退出）：",
        "run_prompt_discord_token": "配置中未设置 Discord Bot Token，请输入（或 Ctrl+C 退出）：",
        "run_prompt_allowed_telegram": "允许的 Telegram 用户 ID（逗号分隔，可选，直接回车跳过）：",
        "run_prompt_allowed_discord": "允许的 Discord 用户 ID（逗号分隔，可选，直接回车跳过）：",
        "run_prompt_save_config": "是否保存到配置文件以便下次使用？ [Y/n]：",
    },
    "en": {
        "cli_help": "OpenAB — Open Agent Bridge",
        "opt_token": "Telegram Bot Token",
        "opt_token_discord": "Discord Bot Token",
        "opt_workspace": "Agent workspace directory",
        "opt_verbose": "Enable verbose logging",
        "run_help": "Run Telegram bot (long polling).",
        "run_discord_help": "Run Discord bot.",
        "err_no_token": "Error: Set TELEGRAM_BOT_TOKEN or pass --token.",
        "err_no_token_discord": "Error: Set DISCORD_BOT_TOKEN or pass --token.",
        "starting": "Starting OpenAB Telegram bot (long polling)…",
        "starting_discord": "Starting OpenAB Discord bot…",
        "install_service_help": "Install as a Linux user-level systemd service (one-shot).",
        "install_service_linux_only": "Only supported on Linux.",
        "install_service_done": "User service installed and enabled: {path}\nRun systemctl --user start openab to start, or use --start to start now.",
        "install_service_done_discord": "User service installed and enabled: {path}\nRun systemctl --user start openab-discord to start, or use --start to start now.",
        "install_wizard_title": "OpenAB service install wizard (Linux only)",
        "install_wizard_which": "Which bot service to install? 1) Telegram  2) Discord  3) Both",
        "install_wizard_which_prompt": "Select [1-3] (default 1): ",
        "install_wizard_telegram_token": "Telegram Bot Token (leave empty to skip, edit config later): ",
        "install_wizard_telegram_allowed": "Allowed Telegram user IDs (comma-separated, leave empty to skip): ",
        "install_wizard_discord_token": "Discord Bot Token (leave empty to skip): ",
        "install_wizard_discord_allowed": "Allowed Discord user IDs (comma-separated, leave empty to skip): ",
        "install_wizard_config_saved": "Config saved to: {path}",
        "install_wizard_start_now": "Start service(s) now? [y/N]: ",
        "install_wizard_installing_telegram": "Installing Telegram service…",
        "install_wizard_installing_discord": "Installing Discord service…",
        "install_wizard_done": "Installation complete.",
        "install_wizard_skip_interactive": "Skip interactive wizard; install with current options (config must already have tokens etc.).",
        "run_prompt_telegram_token": "Telegram Bot Token not set in config. Enter token (or Ctrl+C to exit): ",
        "run_prompt_discord_token": "Discord Bot Token not set in config. Enter token (or Ctrl+C to exit): ",
        "run_prompt_allowed_telegram": "Allowed Telegram user IDs (comma-separated, optional, press Enter to skip): ",
        "run_prompt_allowed_discord": "Allowed Discord user IDs (comma-separated, optional, press Enter to skip): ",
        "run_prompt_save_config": "Save to config file for next time? [Y/n]: ",
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
