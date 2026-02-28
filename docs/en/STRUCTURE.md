# OpenAB project structure

Directory layout for CLI, multiple agents, and multiple chat platforms. Environment and dependencies are managed by **uv** (`.python-version` + `uv.lock`, `uv sync` to install).

[中文](../zh-CN/STRUCTURE.md) · **English**

---

```
openab/                    # Main package
├── __init__.py            # Version etc.
├── __main__.py            # python -m openab entry
├── core/                  # Shared utilities
│   ├── __init__.py
│   ├── config.py          # YAML/JSON config, load/save
│   ├── detect_cli.py      # Detect available agent backends
│   └── i18n/              # i18n (by domain)
│       ├── __init__.py    # t, cli_t, lang_from_*
│       ├── bot.py         # Bot messages MESSAGES
│       └── cli.py         # CLI messages CLI_MESSAGES
├── agents/                # Agent backends (selected by agent.backend)
│   ├── __init__.py        # run_agent_async, run_agent, get_backend
│   ├── cursor.py          # Cursor CLI
│   ├── codex.py           # OpenAI Codex CLI
│   ├── gemini.py          # Gemini CLI
│   ├── claude.py          # Claude CLI
│   └── openclaw.py        # OpenClaw CLI
├── chats/                 # Chat frontends
│   ├── __init__.py
│   ├── telegram/          # Telegram bot
│   │   ├── __init__.py
│   │   └── bot.py
│   └── discord/           # Discord bot
│       ├── __init__.py
│       └── bot.py
├── api/                   # OpenAI API compatible HTTP server
│   ├── __init__.py        # create_app(config_path=...)
│   └── app.py             # FastAPI: /v1/chat/completions, /v1/models
└── cli/                   # OpenAB CLI
    ├── __init__.py
    ├── main.py            # typer: run (serve|telegram|discord), config, allowlist, install-service
    └── service_linux.py   # Linux systemd user service (install-service)

docs/                      # Docs (by language)
├── README.md              # Doc index
├── en/
│   ├── guide.md
│   └── STRUCTURE.md      # This file
└── zh-CN/
    ├── README.md
    ├── guide.md
    └── STRUCTURE.md

config.example.yaml
uv.lock
.python-version
README.md
LICENSE
```

## Extension conventions

- **Add an agent:** Add `xxx.py` under `openab/agents/` with `async def run_async(prompt, *, workspace, timeout, lang) -> str`, and wire it in `agents/__init__.py` inside `run_agent_async` (by `agent.backend` / `OPENAB_AGENT`).
- **Add a chat frontend:** Add a subpackage under `openab/chats/` (e.g. `discord/`), implement the bot or webhook, and add a subcommand under `run_app` in `openab/cli/main.py` (e.g. `openab run discord`).
- **CLI subcommands:** Add with `@app.command()` or under `run_app` in `openab/cli/main.py`, or split into `openab/cli/run.py`, `openab/cli/config.py`, etc. and mount in `main.py`.
- **OpenAI API server:** `openab run serve` runs `openab/api/app.py` (FastAPI) with uvicorn; auth via config `api.key` or `--token` (API key override); `create_app(api_key_override=...)` for CLI override.
