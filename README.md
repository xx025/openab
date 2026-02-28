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
# or: uv pip install -e .   (from repo)
# or: uv tool install openab
```

**2. Config** — Put a YAML/JSON config in `~/.config/openab/` (see [config.example.yaml](config.example.yaml)). You need at least a bot token (Telegram/Discord) or nothing for API-only; allowlist or `api.key` for auth. You can also pass tokens via CLI: `openab run telegram --token <token>`, `openab run serve --token <api_key>`. Full options: [docs/en/guide.md](docs/en/guide.md).

**3. Run**

```bash
openab run serve     # OpenAI-compatible API (optional: --token, --host, --port)
openab run telegram  # Telegram bot (optional: --token, --workspace, --verbose)
openab run discord   # Discord bot (optional: --token, --workspace, --verbose)
```

- No config? Run `openab` or `openab run` — you get a hint and the API server starts by default.
- Then open the bot in your chat app, or point any OpenAI-compatible client at `http://127.0.0.1:8000/v1` with the API key printed at startup.

---

## Docs

- **[Configuration & usage](docs/en/guide.md)** — Config keys, agent setup, commands, API server, security, i18n.
- **[中文说明](docs/zh-CN/guide.md)** — 配置与使用（中文）

---

## License

MIT — [LICENSE](LICENSE)
