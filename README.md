[**中文**](docs/zh-CN/README.md) · [**English**](README.md)

<p align="center">
  <img src="https://raw.githubusercontent.com/xx025/openab/main/assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge** — Connect AI agents to chat platforms. One config, one bridge. **Currently implemented:** Cursor, Codex. _Gemini, Claude, OpenClaw not yet implemented._

[Configuration & usage](docs/en/guide.md)

---

## What it does

OpenAB forwards messages from **chat platforms** (or HTTP API) to an agent backend you choose and sends the reply back. One config, one bridge.

| Agents | Chats / API |
|--------|----------------|
| **Cursor**, **Codex** (implemented)<br>_Gemini, Claude, OpenClaw not yet implemented_ | Telegram, Discord, **OpenAI-compatible HTTP API** (`openab run serve`), _more planned_ |

---

## Quick start

**1. Install** (Python 3.10+)

```bash
pip install openab
# or: uv tool install openab
# or from repo: uv pip install -e .
```

**2. Run and follow the prompts**

```bash
openab run
```

You’ll choose **serve** (API), **telegram**, or **discord**, enter bot token and allowlist when asked; choices are saved to `~/.config/openab/config.yaml`. Then open your bot in the app and chat, or use the API at `http://127.0.0.1:8000/v1` with the printed key. Use `/resume` or `!resume` in chat to switch sessions.

- **Tokens:** Telegram → [@BotFather](https://t.me/BotFather) `/newbot`; Discord → [Developer Portal](https://discord.com/developers/applications) → Bot → Reset Token.
- **Unauthorized?** Send `/whoami` or `!whoami` to get your ID, then `openab config set telegram.allowed_user_ids "ID"` (or send the API key to the bot to self-add).

Full options: [Configuration & usage](docs/en/guide.md).

---

## Docs

- **[Configuration & usage](docs/en/guide.md)** — Config keys, agent setup, commands, API server, security, i18n.
- **[中文说明](docs/zh-CN/guide.md)** — 配置与使用（中文）

---

## License

MIT — [LICENSE](LICENSE)
