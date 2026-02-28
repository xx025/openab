**中文说明 / Chinese:** [docs/README.zh-CN.md](docs/README.zh-CN.md)

---

# OpenAB

**Open** **A**gent **B**ridge — a bridge between **agent backends** (CLIs, APIs, …) and **chat platforms** (Telegram, Discord, Slack, …). Plug in the agents and chats you want; OpenAB routes messages between them. Use your agents from any device and any supported chat app.

| Agents (backends) | Chats (frontends) |
|-------------------|-------------------|
| [Cursor](https://cursor.com) CLI ✓ | Telegram ✓        |
| [OpenAI Codex](https://github.com/openai/codex) ✓ | _more planned_    |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) ✓ |                   |
| Claude CLI ✓      |                   |
| _more planned_    |                   |

---

## Quick start: Agent × Telegram

The steps below run **one** built-in combination: one agent backend (Cursor or Codex) and Telegram.

### Requirements

1. **One agent CLI** installed and signed in:
   - **Cursor:** `agent status` / `agent login`
   - **Codex:** `npm i -g @openai/codex` or `brew install --cask codex`, then `codex` (or `CODEX_API_KEY`)
   - **Gemini:** `npm i -g @google/gemini-cli` or `brew install gemini-cli`, then `gemini` (or `GEMINI_API_KEY`)
   - **Claude:** use a CLI that supports `claude -p "prompt"` and set `OPENAB_AGENT=claude`, `CLAUDE_CLI_CMD` to the binary

2. **Telegram Bot Token**  
   Create a bot via [@BotFather](https://t.me/BotFather) and get the token.

3. **[uv](https://docs.astral.sh/uv/)**（推荐）或 Python 3.10+

### Install

```bash
git clone https://github.com/xx025/openab.git
cd openab
uv sync
```

（uv 会按 `.python-version` 创建虚拟环境并安装依赖；首次可先安装 [uv](https://docs.astral.sh/uv/)。）

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
| `OPENAB_AGENT` | No | Agent backend: `cursor` (default), `codex`, `gemini`, or `claude` |
| `OPENAB_WORKSPACE` | No | Working directory for the agent (default: current dir). `CURSOR_WORKSPACE` is also accepted. |
| `OPENAB_AGENT_TIMEOUT` | No | Timeout in seconds (default: 300) |
| `CURSOR_AGENT_CMD` | No | Path to Cursor `agent` (default: `agent` in PATH) |
| `CODEX_CMD` | No | Path to Codex CLI (default: `codex` in PATH). Uses `codex exec` non-interactively. |
| `CODEX_SKIP_GIT_CHECK` | No | Set to `1` to run Codex outside a Git repo |
| `GEMINI_CLI_CMD` | No | Path to Gemini CLI (default: `gemini` in PATH). Uses `gemini -p "prompt"`. |
| `CLAUDE_CLI_CMD` | No | Path to Claude CLI (default: `claude` in PATH). Uses `claude -p "prompt"`. |

### Run

```bash
uv run openab
# Or with options
uv run openab --token "YOUR_BOT_TOKEN" --workspace /path/to/project
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
