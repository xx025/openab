# OpenAB 项目目录结构

为后续扩展 CLI、多智能体、多聊天平台预留的目录规划。环境与依赖由 **uv** 管理（`.python-version` + `uv.lock`，`uv sync` 安装）。

```
openab/                    # 主包
├── __init__.py            # 版本等
├── __main__.py            # python -m openab 入口
├── core/                  # 公共能力
│   ├── __init__.py
│   └── i18n.py            # 中英文文案
├── agents/                # 智能体后端（按 OPENAB_AGENT 选择）
│   ├── __init__.py        # run_agent_async, run_agent, get_backend
│   ├── cursor.py          # Cursor CLI
│   ├── codex.py           # OpenAI Codex CLI
│   ├── gemini.py          # Gemini CLI
│   └── claude.py          # Claude CLI
├── chats/                 # 聊天前端
│   ├── __init__.py
│   └── telegram/          # Telegram 机器人
│       ├── __init__.py
│       └── bot.py
└── cli/                   # OpenAB 命令行
    ├── __init__.py
    └── main.py            # typer: openab run, (未来: config, agent, …)

cursor_telegram_bot/       # 兼容层：python -m cursor_telegram_bot → openab
├── __init__.py
└── __main__.py

docs/                      # 文档
├── README.md              # 文档索引
├── README.zh-CN.md        # 中文说明
└── STRUCTURE.md           # 本文件

.env.example
uv.lock
.python-version
README.md
LICENSE
```

## 扩展约定

- **新增智能体**：在 `openab/agents/` 下新增 `xxx.py`，实现 `async def run_async(prompt, *, workspace, timeout, lang) -> str`，并在 `agents/__init__.py` 的 `run_agent_async` 中按 `OPENAB_AGENT` 分发。
- **新增聊天前端**：在 `openab/chats/` 下新增子包（如 `discord/`），实现 bot 或 webhook，在 `openab/cli/main.py` 中可增加子命令（如 `openab run --chat discord`）。
- **CLI 子命令**：在 `openab/cli/main.py` 用 `@app.command()` 增加，或拆成 `openab/cli/run.py`、`openab/cli/config.py` 等再在 `main.py` 中挂载。
