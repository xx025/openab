# OpenAB 项目目录结构

为后续扩展 CLI、多智能体、多聊天平台预留的目录规划。环境与依赖由 **uv** 管理（`.python-version` + `uv.lock`，`uv sync` 安装）。

[English](../en/STRUCTURE.md) · **中文**

---

```
openab/                    # 主包
├── __init__.py            # 版本等
├── __main__.py            # python -m openab 入口
├── core/                  # 公共能力
│   ├── __init__.py
│   ├── config.py          # YAML/JSON 配置读写
│   ├── detect_cli.py      # 检测可用 agent 后端
│   └── i18n/              # 中英文文案（按用途分文件）
│       ├── __init__.py    # t, cli_t, lang_from_*
│       ├── bot.py         # 机器人端文案 MESSAGES
│       └── cli.py         # CLI 文案 CLI_MESSAGES
├── agents/                # 智能体后端（按 agent.backend 选择）
│   ├── __init__.py        # run_agent_async, run_agent, get_backend
│   ├── cursor.py          # Cursor CLI
│   ├── codex.py           # OpenAI Codex CLI
│   ├── gemini.py          # Gemini CLI
│   ├── claude.py          # Claude CLI
│   └── openclaw.py        # OpenClaw CLI
├── chats/                 # 聊天前端
│   ├── __init__.py
│   ├── telegram/          # Telegram 机器人
│   │   ├── __init__.py
│   │   └── bot.py
│   └── discord/           # Discord 机器人
│       ├── __init__.py
│       └── bot.py
├── api/                   # OpenAI API 兼容 HTTP 服务
│   ├── __init__.py        # create_app(config_path=...)
│   └── app.py             # FastAPI: /v1/chat/completions, /v1/models
└── cli/                   # OpenAB 命令行
    ├── __init__.py
    ├── main.py            # typer: run (serve|telegram|discord), config, allowlist, install-service
    └── service_linux.py   # Linux systemd 用户服务（install-service）

docs/                      # 文档（按语言分目录）
├── README.md              # 文档索引
├── en/
│   ├── guide.md
│   └── STRUCTURE.md      # 本文件英文版
└── zh-CN/
    ├── README.md
    ├── guide.md
    └── STRUCTURE.md      # 本文件

config.example.yaml
uv.lock
.python-version
README.md
LICENSE
```

## 扩展约定

- **新增智能体**：在 `openab/agents/` 下新增 `xxx.py`，实现 `async def run_async(prompt, *, workspace, timeout, lang) -> str`，并在 `agents/__init__.py` 的 `run_agent_async` 中按 `agent.backend` / `OPENAB_AGENT` 分发。
- **新增聊天前端**：在 `openab/chats/` 下新增子包（如 `discord/`），实现 bot 或 webhook，在 `openab/cli/main.py` 的 `run_app` 下增加子命令（如 `openab run discord`）。
- **CLI 子命令**：在 `openab/cli/main.py` 用 `@app.command()` 或在 `run_app` 下增加，或拆成 `openab/cli/run.py`、`openab/cli/config.py` 等再在 `main.py` 中挂载。
- **OpenAI API 服务**：`openab run serve` 使用 `openab/api/app.py`（FastAPI）经 uvicorn 启动；可选配置 `api.key` 做 Bearer 鉴权。
