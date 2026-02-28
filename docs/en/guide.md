# OpenAB — Configuration & usage

Technical reference for configuration, agent backends, commands, and security. Chat frontends currently include Telegram and Discord; more platforms may be added.

[中文](../zh-CN/guide.md) · **English**

---

**Platforms:** OpenAB runs on **Linux** and **macOS**. All CLI commands (`openab run serve`, `openab run telegram`, `openab run discord`, `openab config`, agent backends) work on both. The **install-service** command (systemd user unit) is **Linux-only**; on macOS run the bot directly with `openab run telegram` or `openab run discord`.

---

## Configuration

OpenAB uses a **YAML or JSON** config file. Default path: `~/.config/openab/config.yaml`. Override with environment variable **`OPENAB_CONFIG`**.

Create `~/.config/openab/` and copy the repo’s [config.example.yaml](../../config.example.yaml) or [config.example.json](../../config.example.json) as `config.yaml` or `config.json`. You can also edit the config from the CLI:

| Command | Description |
|---------|-------------|
| `openab config path` | Print config file path (current or default) |
| `openab config get [key]` | Show full config or value at dot key (e.g. `agent.backend`) |
| `openab config set <key> <value>` | Set key and save (e.g. `openab config set agent.backend openclaw`; use comma for list IDs: `openab config set telegram.allowed_user_ids "123,456"`) |

New keys are written to the existing config file (YAML or JSON by path); if no file exists, the default path is used and created on first `set`.

### Configuration reference

| Key | Required | Description |
|-----|----------|-------------|
| `telegram.bot_token` | For `run` | Bot token from [@BotFather](https://t.me/BotFather) |
| `telegram.allowed_user_ids` | For `run` | List of Telegram user IDs. Empty = nobody can use. Users get ID with `/whoami`. |
| `discord.bot_token` | For `run discord` | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `discord.allowed_user_ids` | For `run discord` | List of Discord user IDs. Empty = nobody. Users get ID with `!whoami` in DM. |
| `agent.backend` | No | `cursor`, `codex`, `gemini`, `claude`, `openclaw` (default: `cursor`) |
| `agent.workspace` | No | Agent working directory (default: **user home** `~`) |
| `agent.timeout` | No | Timeout in seconds (default: 300) |
| `cursor.cmd`, `codex.cmd`, `gemini.cmd`, `claude.cmd`, `openclaw.cmd` | No | CLI binary name for each backend |
| Backend-specific options | No | e.g. `openclaw.thinking` (off \| minimal \| low \| medium \| high \| xhigh), `claude.model`, `codex.skip_git_check`, etc. See [config.example.yaml](../../config.example.yaml). |
| `api.key` | No | If set, requests to `openab run serve` must send `Authorization: Bearer <api.key>`. Omit for local/unprotected use. |
| `api.host` | No | Bind host for `openab run serve` (default: `127.0.0.1`). Overridable with `--host`. |
| `api.port` | No | Bind port for `openab run serve` (default: `8000`). Overridable with `--port`. |

---

## OpenAI API compatible server

Run `openab run serve` to expose an HTTP API compatible with OpenAI:

- **Endpoints:** `POST /v1/chat/completions`, `GET /v1/models`, `POST /v1/responses`
- **Auth:** If `api.key` is set in config, requests must send `Authorization: Bearer <api.key>`. If `api.key` is missing, the server generates one at first start, writes it to config, and prints it (and prints it again on every start).
- **Clients:** Use `base_url=http://127.0.0.1:8000/v1` and the API key. The last user message is sent to your configured agent; the reply is returned as `choices[0].message.content` (chat) or `output_text` / `output[].content` (responses). **Streaming:** `stream: true` is supported for chat completions (single-chunk SSE).
- **Self-add allowlist:** In Telegram or Discord, any user can send the exact `api.key` (as a message) to be added to that platform’s allowlist automatically; the config is updated and no restart is needed.

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
| `openab` | No subcommand: check config; if empty → prompt and start API server (run serve); else show help. |
| `openab run serve` | Start OpenAI API compatible HTTP server (`POST /v1/chat/completions`, `GET /v1/models`). Optional: `--host`, `--port` or config `api.host` / `api.port`. |
| `openab run telegram` | Run Telegram bot |
| `openab run discord` | Run Discord bot |
| `openab run` | No run target: same as `openab` (check config; if empty → run serve, else show run help). |
| `openab config path` | Print config file path |
| `openab config get [key]` | Show config or value at key |
| `openab config set <key> <value>` | Set config key and save |
| `openab install-service` | Install as a **Linux user-level systemd service** (optional: `--discord` for Discord, `--start` to start now). **Linux only.** On macOS run `openab run telegram` or `openab run discord` in the terminal (or configure launchd yourself). |

Options: `--config` / `-c` for config path; for `run telegram` / `run discord` use `--token`, `--workspace`, `--verbose`; for `run serve` use `--host`, `--port`.

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

- Only users listed in `telegram.allowed_user_ids` or `discord.allowed_user_ids` can send prompts; others get an "unauthorized" message. Alternatively, set `telegram.allow_all` or `discord.allow_all` to `true` (use with caution).
- **Token = allowlist:** In Telegram or Discord, sending a message whose content is exactly the configured `api.key` adds that user to the allowlist and saves the config (no restart needed).
- Do not commit config files that contain tokens. Keep `~/.config/openab/config.yaml` (or your `OPENAB_CONFIG` path) private.

---

## i18n

- **Bot:** Language follows the chat app (e.g. Telegram `language_code`). `zh*` → 中文; otherwise English.
- **CLI:** Follows `LANG` (e.g. `LANG=zh_CN.UTF-8` for 中文).
