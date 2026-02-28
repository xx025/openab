<p align="center">
  <img src="https://raw.githubusercontent.com/xx025/openab/main/assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge** — Connect AI agents (Cursor, Codex, Gemini, Claude, OpenClaw) to chat platforms. One config, one bridge.

[中文](docs/zh-CN/README.md) · [Configuration & usage](docs/en/guide.md)

---

## What it does

OpenAB forwards messages from **chat platforms** (or HTTP API) to an agent backend you choose and sends the reply back. One config, one bridge.

| Agents | Chats / API |
|--------|----------------|
| Cursor, Codex, Gemini, Claude, OpenClaw | Telegram, Discord, **OpenAI-compatible HTTP API** (`openab run serve`), _more planned_ |

---

## Quick start

**1. Install** (Python 3.10+)

```bash
pip install openab
# or: uv tool install openab
# or from repo: uv pip install -e .
```

**2. Create config** — Copy the example and edit:

```bash
mkdir -p ~/.config/openab
cp config.example.yaml ~/.config/openab/config.yaml
# then edit: set telegram.bot_token and/or discord.bot_token
```

**3. Get a bot token** (for Telegram or Discord)

- **Telegram:** Open [@BotFather](https://t.me/BotFather) → send `/newbot` → follow prompts → copy the token into `telegram.bot_token` in config (or pass with `openab run telegram --token <token>`).
- **Discord:** [Discord Developer Portal](https://discord.com/developers/applications) → New Application → Bot → Reset Token → copy into `discord.bot_token` (or use `--token` when running).

**4. Allow yourself** — After the bot is running, send `/whoami` (Telegram) or `!whoami` (Discord) to get your user ID. Then either:

- Add your ID to config: `openab config set telegram.allowed_user_ids "YOUR_ID"` (or `discord.allowed_user_ids`), **or**
- Send the API key (printed when you run `openab run serve` once) as a message to the bot; it will add you to the allowlist automatically.

**5. Run and chat**

```bash
openab run telegram   # or: openab run discord
# In Telegram/Discord: open your bot, send any message. Use /resume to see session buttons (resume latest, new session, or pick a history session).
```

- **API only:** Run `openab run serve` — no bot token needed. Point clients at `http://127.0.0.1:8000/v1` with the printed API key.
- No config? Running `openab` or `openab run` will start the API server by default and show a hint.

Full options: [Configuration & usage](docs/en/guide.md).

---

## Docs

- **[Configuration & usage](docs/en/guide.md)** — Config keys, agent setup, commands, API server, security, i18n.
- **[中文说明](docs/zh-CN/guide.md)** — 配置与使用（中文）

---

## License

MIT — [LICENSE](LICENSE)
