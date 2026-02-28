"""机器人端文案（Telegram/Discord 等），按 language_code 选 zh / en。"""

# key -> zh / en
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
