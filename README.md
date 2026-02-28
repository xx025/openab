<p align="center">
  <img src="https://raw.githubusercontent.com/xx025/openab/main/assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge** — Connect AI agents (Cursor, Codex, Gemini, Claude, OpenClaw) to chat platforms. One config, one bridge.

[中文](docs/zh-CN/README.md) · [Configuration & usage](docs/en/guide.md)

---

## What it does

OpenAB forwards messages from **chat platforms** to an agent backend you choose and sends the reply back. No per-agent bots — configure once and chat.

| Agents | Chats |
|--------|-------|
| Cursor, Codex, Gemini, Claude, OpenClaw | Telegram, Discord, _more planned_ |

---

## Quick start

**1. Install** (Python 3.10+)

```bash
pip install openab
# or: uv tool install openab
```

**2. Config** — Put a YAML/JSON config in `~/.config/openab/` (see [config.example.yaml](config.example.yaml)). You need at least a bot token and an allowlist of user IDs. Full options: [docs/en/guide.md](docs/en/guide.md).

**3. Run**

```bash
openab              # e.g. Telegram
openab run-discord  # e.g. Discord
```

Then open the bot in your chat app and send a message.

---

## Docs

- **[Configuration & usage](docs/en/guide.md)** — Config keys, agent setup, commands, security, i18n.

---

## License

MIT — [LICENSE](LICENSE)
