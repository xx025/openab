# OpenAB — Configuration & usage

Technical reference for configuration, agent backends, commands, and security. Chat frontends currently include Telegram, Discord, and Mattermost; more platforms may be added.

[中文](../zh-CN/guide.md) · **English**

---

## Quick start (first-time)

1. **Install** — `pip install openab` (Python 3.10+).
2. **Run** — Run `openab run` and follow the prompts:
   - Choose run target: **1) serve (API)**, **2) telegram**, **3) discord**, **4) mattermost**
   - If you pick telegram/discord/mattermost, enter Bot Token (and server URL for Mattermost) and allowed user IDs when asked (or self-add later by sending the API key in chat)
   - If `agent.backend` is not set, the CLI will detect backends and let you choose (e.g. Cursor/Codex)
   - All choices are **saved automatically** to `~/.config/openab/config.yaml`
3. **Use it** — With serve, the API is up; with telegram/discord/mattermost, open your bot in the app and send a message (on Mattermost, DM the bot or @mention it in a channel). Use `/resume` (Telegram) or `!resume` (Discord/Mattermost) to resume or switch sessions.

**Where to get tokens:** Telegram → [@BotFather](https://t.me/BotFather) send `/newbot`; Discord → [Developer Portal](https://discord.com/developers/applications) → New Application → Bot → Reset Token; Mattermost → System Console → Integrations → Bot Accounts → Add Bot Account (enable bot account creation first), and note your server URL. If you see “unauthorized”, send `/whoami` or `!whoami` in chat to get your ID, then `openab config set telegram.allowed_user_ids "ID"` (or discord; for Mattermost `openab allowlist add --mattermost <ID>`), or send the API key to the bot to self-add. See [Auth & security](#auth--security).

---

**Platforms:** OpenAB runs on **Linux** and **macOS**. All CLI commands (`openab run serve`, `openab run telegram`, `openab run discord`, `openab config`, agent backends) work on both. The **install-service** command (systemd user unit) is **Linux-only**; on macOS run the bot directly with `openab run telegram`, `openab run discord`, or `openab run mattermost`.

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
| `telegram.bot_token` | For `run telegram` | Bot token from [@BotFather](https://t.me/BotFather); or pass with `openab run telegram --token <token>`. |
| `telegram.allowed_user_ids` | For `run` | List of Telegram user IDs. Empty = nobody can use. Users get ID with `/whoami`. |
| `discord.bot_token` | For `run discord` | Bot token from [Discord Developer Portal](https://discord.com/developers/applications); or pass with `openab run discord --token <token>`. |
| `discord.allowed_user_ids` | For `run discord` | List of Discord user IDs. Empty = nobody. Users get ID with `!whoami` in DM. |
| `mattermost.server_url` | For `run mattermost` | Base URL of your Mattermost server, e.g. `https://mattermost.example.com`; or pass with `openab run mattermost --server-url <url>`. |
| `mattermost.bot_token` | For `run mattermost` | Bot token from System Console → Integrations → Bot Accounts; or pass with `openab run mattermost --token <token>`. |
| `mattermost.allowed_user_ids` | For `run mattermost` | List of Mattermost user IDs (26-char **strings**, not numbers). Empty = nobody. Users get ID with `!whoami`. |
| `agent.backend` | No | `cursor`, `agent` (alias for cursor, Cursor CLI is `agent`), `codex` (implemented); `gemini`, `claude`, `openclaw` _not yet implemented_ (default: `cursor`) |
| `agent.workspace` | No | Agent working directory (default: **user home** `~`) |
| `agent.timeout` | No | Timeout in seconds (default: 300) |
| `cursor.cmd`, `codex.cmd`, `gemini.cmd`, `claude.cmd`, `openclaw.cmd` | No | CLI binary name for each backend |
| Backend-specific options | No | e.g. `openclaw.thinking` (off \| minimal \| low \| medium \| high \| xhigh), `claude.model`, `codex.skip_git_check`, etc. See [config.example.yaml](../../config.example.yaml). |
| `api.key` | No | If set, requests to `openab run serve` must send `Authorization: Bearer <api.key>`. Omit for local/unprotected use. You can override with `openab run serve --token <key>` for a single run. |
| `api.host` | No | Bind host for `openab run serve` (default: `127.0.0.1`). Overridable with `--host`. |
| `api.port` | No | Bind port for `openab run serve` (default: `8000`). Overridable with `--port`. |
| `service.run` | No | Run target for `openab run` (no subcommand) and **install-service** systemd unit, **parsed only from this key**: `serve` \| `telegram` \| `discord` \| `mattermost`. Defaults to `serve` if unset or invalid. |

---

## OpenAI API compatible server

Run `openab run serve` to expose an HTTP API compatible with OpenAI:

- **Endpoints:** `POST /v1/chat/completions`, `GET /v1/models`, `POST /v1/responses`
- **Auth:** If `api.key` is set in config, requests must send `Authorization: Bearer <api.key>`. Use `openab run serve --token <key>` to override the API key for that run only. If neither is set, the server generates one at first start, writes it to config, and prints it (and prints it again on every start).
- **Clients:** Use `base_url=http://127.0.0.1:8000/v1` and the API key. The last user message is sent to your configured agent; the reply is returned as `choices[0].message.content` (chat) or `output_text` / `output[].content` (responses). **Streaming:** `stream: true` is supported for chat completions (single-chunk SSE).
- **Self-add allowlist:** In Telegram, Discord, or Mattermost, any user can send the exact `api.key` (as a message) to be added to that platform’s allowlist automatically; the config is updated and no restart is needed.

---

## Agent backends (prerequisites)

**Currently implemented:** Cursor, Codex. **Not yet implemented:** Gemini, Claude, OpenClaw (config keys exist but may not work end-to-end).

- **Cursor:** Cursor CLI — `agent status` / `agent login`. By default uses `--continue` to resume the previous session; set `cursor.continue_session: false` in config to start a new session each time.
- **Codex:** `npm i -g @openai/codex` or `brew install --cask codex`; then `codex` or set API key. Supports session resume and history list like Cursor.
- **Gemini:** _Not yet implemented._ Intended: `npm i -g @google/gemini-cli` or `brew install gemini-cli`; then `gemini`.
- **Claude:** _Not yet implemented._ Intended: CLI that supports `claude -p "prompt"`; set `agent.backend: claude` in config.
- **OpenClaw:** _Not yet implemented._ Intended: `npm install -g openclaw`, then `openclaw onboard` and run the Gateway (`openclaw gateway` or daemon); set `agent.backend: openclaw`.

---

## Commands

### CLI

| Command | Description |
|---------|-------------|
| `openab` | With no arguments: show help (same as `openab --help`). Use `openab run` to start a service. |
| `openab run serve` | Start OpenAI API compatible HTTP server (`POST /v1/chat/completions`, `GET /v1/models`). Optional: `--token` (API key), `--host`, `--port` or config `api.key` / `api.host` / `api.port`. |
| `openab run telegram` | Run Telegram bot. Optional: `--token`, `--workspace`, `--verbose`. |
| `openab run discord` | Run Discord bot. Optional: `--token`, `--workspace`, `--verbose`. |
| `openab run mattermost` | Run Mattermost bot (WebSocket). Optional: `--server-url`, `--token`, `--workspace`, `--verbose`. |
| `openab run` | No target: if **service.run** is set, use it; otherwise **interactive guide** to choose serve/telegram/discord/mattermost and save to config. |
| `openab config path` | Print config file path |
| `openab config get [key]` | Show config or value at key |
| `openab config set <key> <value>` | Set config key and save |
| `openab install-service` | Install as a **Linux user-level systemd service**; the service runs `openab run`, with target **parsed only from config** `service.run`. Optional: `--discord` / `--mattermost` to add a platform-only unit, `--start` to start now. **Linux only.** |

**Global options** (e.g. `openab -c /path/config.yaml run telegram`): `--config` / `-c` config path; `--workspace` / `-w` workspace; `--verbose` / `-v` verbose logging. **Per-command options:** `run telegram` / `run discord` / `run mattermost` support `--token` / `-t` (bot token), `--workspace`, `--verbose` (`run mattermost` also `--server-url` / `-s`); `run serve` supports `--token` / `-t` (API key, overrides config), `--host`, `--port`.

### Telegram bot

| Command | Description |
|---------|-------------|
| `/start` | Welcome and auth status |
| `/whoami` | Show your Telegram user ID (for allowlist) |
| `/new` | Create a new session (next message in new conversation; Cursor backend only) |
| `/resume` | **Recommended:** With no argument, shows buttons to **Resume latest**, **New session**, or pick a **history session** from your local Cursor chats (click to switch) |
| `/resume [session ID]` | Switch directly to the given session (IDs come from `~/.cursor/chats`) |
| `/sessions` | How to view and switch sessions |

Any other message is sent to the agent.

### Discord bot

| Command | Description |
|---------|-------------|
| `!start` | Welcome and auth status |
| `!whoami` | Show your Discord user ID (for allowlist) |
| `!new` | Create a new session (next message in new conversation; Cursor backend only) |
| `!resume` | **Recommended:** With no argument, shows buttons to **Resume latest**, **New session**, or pick a **history session** (click to switch) |
| `!resume [session ID]` | Switch directly to the given session |
| `!sessions` | How to view and switch sessions |

Any other message is sent to the agent (DM or channel where the bot can read).

### Mattermost bot

The bot answers **direct messages**, and **channel messages that @mention it**; other channel traffic is ignored. Replies are posted into the message's thread.

| Command | Description |
|---------|-------------|
| `!start` | Welcome and auth status |
| `!whoami` | Show your Mattermost user ID (for allowlist) |
| `!new` | Create a new session (next message in new conversation) |
| `!resume` | With no argument, lists recent sessions with their IDs (Mattermost buttons need a server-reachable callback URL, so the list is text) |
| `!resume [session ID]` | Switch directly to the given session |
| `!sessions` | How to view and switch sessions |

---

## Auth & security

- Only users listed in `telegram.allowed_user_ids`, `discord.allowed_user_ids`, or `mattermost.allowed_user_ids` can send prompts; others get an "unauthorized" message. Alternatively, set the platform's `allow_all` to `true` (use with caution).
- **Token = allowlist:** In Telegram, Discord, or Mattermost, sending a message whose content is exactly the configured `api.key` adds that user to the allowlist and saves the config (no restart needed).
- Do not commit config files that contain tokens. Keep `~/.config/openab/config.yaml` (or your `OPENAB_CONFIG` path) private.

---

## i18n

- **Bot:** Language follows the chat app (e.g. Telegram `language_code`). `zh*` → 中文; otherwise English.
- **CLI:** Follows `LANG` (e.g. `LANG=zh_CN.UTF-8` for 中文).

---

## FAQ

| Issue | What to do |
|-------|------------|
| "Unauthorized" when sending messages | Send `/whoami` or `!whoami` in chat to get your ID, then `openab config set telegram.allowed_user_ids "ID"` (or `discord.allowed_user_ids`); or send the exact `api.key` (or the key printed when running `openab run serve`) as a message to the bot to self-add. |
| Cursor says not logged in or unavailable | Run `agent status` or `agent login` in a terminal; ensure Cursor CLI is logged in and on PATH. |
| No history session buttons on `/resume` | History comes from `~/.cursor/chats` on the machine running OpenAB. If you’ve never chatted in Cursor or the dir is empty, only "Resume latest" and "New session" are shown. |
| Want a new session every time | Set `cursor.continue_session: false` in config. |
| Need to restart after config change? | Allowlist and API key (when set via self-add or `config set`) are written to config and don’t require restart; changing `agent.backend`, `workspace`, or token does require restarting the `openab run` process. |
