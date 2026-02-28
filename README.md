**中文说明 / Chinese:** [README.zh-CN.md](README.zh-CN.md)

---

# OpenAB

**Open** **A**gent **B**ridge — a bridge between **agent backends** (CLIs, APIs, …) and **chat platforms** (Telegram, Discord, Slack, …). Plug in the agents and chats you want; OpenAB routes messages between them. Use your agents from any device and any supported chat app.

| Agents (backends) | Chats (frontends) |
|-------------------|-------------------|
| Cursor CLI ✓      | Telegram ✓        |
| _more planned_    | _more planned_    |

---

## Quick start: Agent × Telegram

The steps below run **one** built-in combination: one agent backend (Cursor CLI) and Telegram. Other combinations will be added later.

### Requirements

1. **Cursor Agent CLI** installed and logged in  
   ```bash
   agent status   # check login
   agent login    # if not logged in
   ```

2. **Telegram Bot Token**  
   Create a bot via [@BotFather](https://t.me/BotFather) and get the token.

3. **Python 3.10+**

### Install

```bash
git clone https://github.com/xx025/openab.git
cd openab
pip install -r requirements.txt
```

### Configuration

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

### Run

```bash
# Long polling (no public URL needed)
python -m cursor_telegram_bot

# Or with options
python -m cursor_telegram_bot --token "YOUR_BOT_TOKEN" --workspace /path/to/project
```

Open your bot in Telegram and send text; OpenAB forwards it to the configured agent and replies (long replies are split into multiple messages).

---

## Commands (Telegram)

| Command | Description |
|---------|-------------|
| `/start` | Welcome and auth status |
| `/whoami` | Show your Telegram User ID (for allowlist) |

---

## Auth (allowlist)

- **You must set** `ALLOWED_USER_IDS=id1,id2,...` in `.env` or the environment. If not set, everyone gets “Auth not configured” and cannot use the bot.
- Only users whose IDs are in the list can send prompts to the agent.
- Others get an “unauthorized” message. They can send `/whoami` to see their ID and ask you to add it.

---

## i18n (English / 中文)

- **Bot**: Language follows the user’s chat app language (e.g. Telegram `language_code`). Chinese (`zh*`) → 中文; otherwise English.
- **CLI**: Follows `LANG` (e.g. `LANG=zh_CN.UTF-8` for 中文).

---

## Security

- Do not commit `.env` or tokens to the repo. `.gitignore` already excludes `.env`.
- Always set `ALLOWED_USER_IDS` so only intended users can use the bot.

---

## License

MIT — see [LICENSE](LICENSE).
