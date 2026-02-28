# OpenAB

**Open Agent Bridge** — Connect AI agent backends (Cursor, Codex, Gemini, Claude, OpenClaw) to chat platforms (Telegram, Discord). One config, one bridge; use your agents from any supported chat app.

[中文说明](docs/README.zh-CN.md)

---

## What is OpenAB?

OpenAB sits between **agent backends** (CLIs / APIs you already use) and **chat frontends** (Telegram, Discord). You pick one agent and one or more chats; OpenAB forwards messages and returns agent replies. No need to run separate bots per agent — configure once and talk from Telegram or Discord.

---

## Supported backends & chats

| Agent backends | Chat frontends |
|----------------|----------------|
| [Cursor](https://cursor.com) CLI | **Telegram** |
| [OpenAI Codex](https://github.com/openai/codex) | **Discord** |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | _more planned_ |
| Claude CLI | |
| [OpenClaw](https://github.com/openclaw/openclaw) | |

---

## Quick start

### 1. Install

**Python 3.10+** required.

```bash
# Option A: pip (recommended)
pip install openab

# Option B: uv tool (isolated env)
uv tool install openab
```

From source (dev/unreleased):

```bash
git clone https://github.com/xx025/openab.git && cd openab && uv sync
# Then: uv run openab
```

### 2. Configure

OpenAB uses a **YAML or JSON** config file under your user directory. Only one env var is used for config: **`OPENAB_CONFIG`** (optional, to override config path).

- Default config path: `~/.config/openab/config.yaml` (run `openab config-path` to print it).
- Create `~/.config/openab/` and copy [config.example.yaml](config.example.yaml) or [config.example.json](config.example.json) as `config.yaml` or `config.json`.
- Fill in at least:
  - **Telegram:** `telegram.bot_token` (from [@BotFather](https://t.me/BotFather)), `telegram.allowed_user_ids` (list of user IDs; users get theirs with `/whoami`).
  - **Discord:** `discord.bot_token` (from [Discord Developer Portal](https://discord.com/developers/applications)), `discord.allowed_user_ids` (users get ID with `!whoami` in DM).
- **Agent:** `agent.backend` — `cursor` (default), `codex`, `gemini`, `claude`, or `openclaw`. Leave `agent.workspace` unset to use your **home directory**; use `--workspace` on the CLI to override.

### 3. Run

**Telegram:**

```bash
openab
# or: openab run
# With overrides: openab --token "YOUR_TOKEN" --workspace /path/to/dir
```

**Discord:**

```bash
openab run-discord
# With overrides: openab run-discord --token "YOUR_TOKEN" --workspace /path/to/dir
```

From source use `uv run openab` / `uv run openab run-discord`.

Open the bot in Telegram or Discord and send a message; OpenAB sends it to the configured agent and replies (long replies are split into multiple messages).

---

## Configuration reference

| Key | Required | Description |
|-----|----------|-------------|
| `telegram.bot_token` | For `run` | Bot token from BotFather |
| `telegram.allowed_user_ids` | For `run` | List of Telegram user IDs. Empty = nobody can use. |
| `discord.bot_token` | For `run-discord` | Bot token from Discord Developer Portal |
| `discord.allowed_user_ids` | For `run-discord` | List of Discord user IDs. Empty = nobody. |
| `agent.backend` | No | `cursor`, `codex`, `gemini`, `claude`, `openclaw` (default: `cursor`) |
| `agent.workspace` | No | Agent working directory (default: **user home** `~`) |
| `agent.timeout` | No | Timeout in seconds (default: 300) |
| `*.cmd` per backend | No | CLI binary name (e.g. `cursor.cmd`, `openclaw.cmd`). Optional backend options in config (e.g. `openclaw.thinking`). |

Override config file path with env **`OPENAB_CONFIG`**.

---

## Agent backends (prerequisites)

- **Cursor:** `agent status` / `agent login` (Cursor CLI).
- **Codex:** `npm i -g @openai/codex` or `brew install --cask codex`; then `codex` or set API key.
- **Gemini:** `npm i -g @google/gemini-cli` or `brew install gemini-cli`; then `gemini`.
- **Claude:** CLI that supports `claude -p "prompt"`; set `agent.backend: claude`.
- **OpenClaw:** `npm install -g openclaw`, then `openclaw onboard` and run the Gateway (`openclaw gateway` or daemon); set `agent.backend: openclaw`.

---

## Commands

**CLI**

| Command | Description |
|---------|-------------|
| `openab` / `openab run` | Run Telegram bot |
| `openab run-discord` | Run Discord bot |
| `openab config-path` | Print default config path |

**Telegram bot:** `/start` — welcome & auth; `/whoami` — show your user ID (for allowlist).

**Discord bot:** `!start` — welcome & auth; `!whoami` — show your user ID. Any other message is sent to the agent (DM or channel where the bot can read).

---

## Auth & security

- Only users listed in `telegram.allowed_user_ids` or `discord.allowed_user_ids` can send prompts; others get an “unauthorized” message.
- Do not commit config files that contain tokens. Keep `~/.config/openab/config.yaml` (or your `OPENAB_CONFIG` path) private.

---

## i18n

- **Bot:** Language follows the chat app (e.g. Telegram `language_code`). `zh*` → 中文; otherwise English.
- **CLI:** Follows `LANG` (e.g. `LANG=zh_CN.UTF-8` for 中文).

---

## License

MIT — see [LICENSE](LICENSE).
