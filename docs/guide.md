# OpenAB — Configuration & usage

Technical reference for configuration, agent backends, commands, and security. Chat frontends currently include Telegram and Discord; more platforms may be added.

---

## Configuration

OpenAB uses a **YAML or JSON** config file. Default path: `~/.config/openab/config.yaml` (run `openab config-path` to print). Override with environment variable **`OPENAB_CONFIG`**.

Create `~/.config/openab/` and copy the repo’s [config.example.yaml](../config.example.yaml) or [config.example.json](../config.example.json) as `config.yaml` or `config.json`.

### Configuration reference

| Key | Required | Description |
|-----|----------|-------------|
| `telegram.bot_token` | For `run` | Bot token from [@BotFather](https://t.me/BotFather) |
| `telegram.allowed_user_ids` | For `run` | List of Telegram user IDs. Empty = nobody can use. Users get ID with `/whoami`. |
| `discord.bot_token` | For `run-discord` | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `discord.allowed_user_ids` | For `run-discord` | List of Discord user IDs. Empty = nobody. Users get ID with `!whoami` in DM. |
| `agent.backend` | No | `cursor`, `codex`, `gemini`, `claude`, `openclaw` (default: `cursor`) |
| `agent.workspace` | No | Agent working directory (default: **user home** `~`) |
| `agent.timeout` | No | Timeout in seconds (default: 300) |
| `cursor.cmd`, `codex.cmd`, `gemini.cmd`, `claude.cmd`, `openclaw.cmd` | No | CLI binary name for each backend |
| Backend-specific options | No | e.g. `openclaw.thinking` (off \| minimal \| low \| medium \| high \| xhigh), `claude.model`, `codex.skip_git_check`, etc. See [config.example.yaml](../config.example.yaml). |

---

## Agent backends (prerequisites)

- **Cursor:** Cursor CLI — `agent status` / `agent login`.
- **Codex:** `npm i -g @openai/codex` or `brew install --cask codex`; then `codex` or set API key.
- **Gemini:** `npm i -g @google/gemini-cli` or `brew install gemini-cli`; then `gemini`.
- **Claude:** CLI that supports `claude -p "prompt"`; set `agent.backend: claude` in config.
- **OpenClaw:** `npm install -g openclaw`, then `openclaw onboard` and run the Gateway (`openclaw gateway` or daemon); set `agent.backend: openclaw`.

---

## Commands

### CLI

| Command | Description |
|---------|-------------|
| `openab` / `openab run` | Run Telegram bot |
| `openab run-discord` | Run Discord bot |
| `openab config-path` | Print default config file path |

Options: `--token`, `--workspace`, `--verbose` (e.g. `openab --token "..." --workspace /path/to/dir`).

### Telegram bot

| Command | Description |
|---------|-------------|
| `/start` | Welcome and auth status |
| `/whoami` | Show your Telegram user ID (for allowlist) |

Any other message is sent to the agent.

### Discord bot

| Command | Description |
|---------|-------------|
| `!start` | Welcome and auth status |
| `!whoami` | Show your Discord user ID (for allowlist) |

Any other message is sent to the agent (DM or channel where the bot can read).

---

## Auth & security

- Only users listed in `telegram.allowed_user_ids` or `discord.allowed_user_ids` can send prompts; others get an “unauthorized” message.
- Do not commit config files that contain tokens. Keep `~/.config/openab/config.yaml` (or your `OPENAB_CONFIG` path) private.

---

## i18n

- **Bot:** Language follows the chat app (e.g. Telegram `language_code`). `zh*` → 中文; otherwise English.
- **CLI:** Follows `LANG` (e.g. `LANG=zh_CN.UTF-8` for 中文).
