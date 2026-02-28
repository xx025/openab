"""机器人端文案（Telegram/Discord 等），按 language_code 选 zh / en。"""

# key -> zh / en
MESSAGES = {
    "zh": {
        "unauthorized": (
            "您没有权限使用此机器人。\n\n"
            "【增加鉴权】请将你的 User ID 提供给管理员，由管理员将你的 ID 加入白名单后即可使用。\n\n"
            "发送 /whoami 可查看你的 User ID。"
        ),
        "unauthorized_cli_hint": "管理员可运行：{cmd}",
        "auth_allow_all_hint": "管理员也可在配置中设置 telegram.allow_all: true 开放给所有人使用。",
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
            "管理员尚未配置鉴权白名单，机器人暂不可用。\n\n"
            "发送 /whoami 可查看你的 User ID，提供给管理员。"
        ),
        "auth_allow_all_hint_discord": "管理员也可在配置中设置 discord.allow_all: true 开放给所有人使用。",
        "allowlist_added_by_token": "已加入白名单，之后可直接发消息使用。",
        "session_new_created": "已创建新会话，下一条消息将在新会话中处理。",
        "session_resume_switched": "已切换到会话 {id}。",
        "session_resume_latest": "已恢复为延续上一会话。",
        "session_resume_usage": "用法：/resume [会话ID]\n不填 ID 则恢复为延续上一会话；填 ID 则切换到该会话。",
        "session_resume_usage_discord": "用法：!resume [会话ID]\n不填 ID 则恢复为延续上一会话；填 ID 则切换到该会话。",
        "sessions_list_unavailable": "当前无法在机器人中列出会话列表。请在 Cursor 中查看会话 ID，使用 /resume <ID>（Discord：!resume <ID>）切换。",
    },
    "en": {
        "unauthorized": (
            "You don't have permission to use this bot.\n\n"
            "[Get access] Ask the admin to add your User ID to the allowlist, then you can use the bot.\n\n"
            "Send /whoami to see your User ID."
        ),
        "unauthorized_cli_hint": "Admin can run: {cmd}",
        "auth_allow_all_hint": "Admin can also set telegram.allow_all: true in config to open to everyone.",
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
            "Auth allowlist is not configured yet. The bot is not available.\n\n"
            "Send /whoami to see your User ID and ask the admin."
        ),
        "auth_allow_all_hint_discord": "Admin can also set discord.allow_all: true in config to open to everyone.",
        "allowlist_added_by_token": "Added to allowlist. You can send messages now.",
        "session_new_created": "New session created. Your next message will start a new conversation.",
        "session_resume_switched": "Switched to session {id}.",
        "session_resume_latest": "Resuming previous (latest) session.",
        "session_resume_usage": "Usage: /resume [session ID]. Omit ID to resume latest; include ID to switch to that session.",
        "session_resume_usage_discord": "Usage: !resume [session ID]. Omit ID to resume latest; include ID to switch to that session.",
        "sessions_list_unavailable": "Session list is not available here. Get the session ID from Cursor, then use /resume <ID> (Discord: !resume <ID>) to switch.",
    },
}
