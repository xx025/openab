**中文说明 / Chinese:** [README.zh-CN.md](README.zh-CN.md)

---

# Cursor CLI × Telegram Bot

Connect [Cursor Agent CLI](https://cursor.com) to Telegram. Use Cursor’s AI from your phone or any device by chatting with the bot.

---

## Requirements

1. **Cursor Agent CLI** installed and logged in  
   ```bash
   agent status   # check login
   agent login    # if not logged in
   ```

2. **Telegram Bot Token**  
   Create a bot via [@BotFather](https://t.me/BotFather) and get the token.

3. **Python 3.10+**

---

## Install

```bash
cd cursor-telegram-bot
pip install -r requirements.txt
```

---

## Configuration

Copy the example env file and edit:

```bash
cp .env.example .env
# Edit .env: TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
```

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from BotFather |
| `ALLOWED_USER_IDS` | Yes | Comma-separated Telegram user IDs. **If unset, no one can use the bot.** Users can send `/whoami` to get their ID. |
| `CURSOR_AGENT_CMD` | No | Path to `agent` (default: `agent` in PATH) |
| `CURSOR_WORKSPACE` | No | Working directory for the agent (default: current dir) |
| `CURSOR_AGENT_TIMEOUT` | No | Timeout in seconds (default: 300) |

---

## Run

```bash
# Long polling (no public URL needed)
python -m cursor_telegram_bot

# Or with options
python -m cursor_telegram_bot --token "YOUR_BOT_TOKEN" --workspace /path/to/project
```

Then open your bot in Telegram and send text; the bot forwards it to Cursor Agent and replies (long replies are split into multiple messages).

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome and auth status |
| `/whoami` | Show your Telegram User ID (for allowlist) |

---

## Auth (allowlist)

- **You must set** `ALLOWED_USER_IDS=id1,id2,...` in `.env` or the environment. If not set, everyone gets “Auth not configured” and cannot use the bot.
- Only users whose IDs are in the list can send prompts to Cursor Agent.
- Others get an “unauthorized” message. They can send `/whoami` to see their ID and ask you to add it.

---

## i18n (English / 中文)

- **Bot**: Language follows the user’s Telegram language (`language_code`). Chinese (`zh*`) → 中文; otherwise English.
- **CLI**: Follows `LANG` (e.g. `LANG=zh_CN.UTF-8` for 中文).

---

## Security

- Do not commit `.env` or tokens to the repo. `.gitignore` already excludes `.env`.
- Always set `ALLOWED_USER_IDS` so only intended users can use the bot.

---

## License

MIT — see [LICENSE](LICENSE).
