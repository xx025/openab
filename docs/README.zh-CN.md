# OpenAB

**Open Agent Bridge（开放智能体桥接）** — 将智能体后端（Cursor、Codex、Gemini、Claude、OpenClaw）与聊天平台（Telegram、Discord）连接起来。一份配置、一座桥；在任意支持的聊天应用里使用你的智能体。

[English](../README.md)

---

## OpenAB 是什么？

OpenAB 介于**智能体后端**（你已在用的 CLI/API）与**聊天前端**（Telegram、Discord）之间。你选择一种智能体和一种或多种聊天方式；OpenAB 转发消息并返回智能体回复。无需为每个智能体单独起机器人 — 配置一次，即可在 Telegram 或 Discord 中对话。

---

## 支持的后端与聊天

| 智能体后端 | 聊天前端 |
|------------|----------|
| [Cursor](https://cursor.com) CLI | **Telegram** |
| [OpenAI Codex](https://github.com/openai/codex) | **Discord** |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | _更多计划中_ |
| Claude CLI | |
| [OpenClaw](https://github.com/openclaw/openclaw) | |

---

## 快速开始

### 1. 安装

需要 **Python 3.10+**。

```bash
# 方式一：pip（推荐）
pip install openab

# 方式二：uv 工具模式（独立环境）
uv tool install openab
```

从源码运行（开发或未发布版本）：

```bash
git clone https://github.com/xx025/openab.git && cd openab && uv sync
# 之后执行：uv run openab
```

### 2. 配置

OpenAB 使用用户目录下的 **YAML 或 JSON** 配置文件。仅使用一个环境变量 **`OPENAB_CONFIG`**（可选，用于覆盖配置文件路径）。

- 默认配置路径：`~/.config/openab/config.yaml`（执行 `openab config-path` 可打印）。
- 创建目录 `~/.config/openab/`，将仓库中的 [config.example.yaml](../config.example.yaml) 或 [config.example.json](../config.example.json) 复制为 `config.yaml` 或 `config.json`。
- 至少填写：
  - **Telegram：** `telegram.bot_token`（来自 [@BotFather](https://t.me/BotFather)）、`telegram.allowed_user_ids`（用户 ID 列表；用户发送 `/whoami` 获取自己的 ID）。
  - **Discord：** `discord.bot_token`（来自 [Discord 开发者门户](https://discord.com/developers/applications)）、`discord.allowed_user_ids`（用户私聊发送 `!whoami` 获取 ID）。
- **智能体：** `agent.backend` — `cursor`（默认）、`codex`、`gemini`、`claude` 或 `openclaw`。不设置 `agent.workspace` 时使用**用户家目录**；命令行可用 `--workspace` 覆盖。

### 3. 运行

**Telegram：**

```bash
openab
# 或：openab run
# 带覆盖：openab --token "你的TOKEN" --workspace /path/to/dir
```

**Discord：**

```bash
openab run-discord
# 带覆盖：openab run-discord --token "你的TOKEN" --workspace /path/to/dir
```

从源码运行时请使用 `uv run openab` / `uv run openab run-discord`。

在 Telegram 或 Discord 中打开机器人并发送消息；OpenAB 会将其交给已配置的智能体处理并回复（长回复会分多条发送）。

---

## 配置说明

| 配置键 | 必填 | 说明 |
|--------|------|------|
| `telegram.bot_token` | 运行 `run` 时 | BotFather 提供的 token |
| `telegram.allowed_user_ids` | 运行 `run` 时 | Telegram 用户 ID 列表，空则无人可用 |
| `discord.bot_token` | 运行 `run-discord` 时 | Discord 开发者门户中的 Bot Token |
| `discord.allowed_user_ids` | 运行 `run-discord` 时 | Discord 用户 ID 列表，空则无人可用 |
| `agent.backend` | 否 | `cursor`、`codex`、`gemini`、`claude`、`openclaw`（默认 `cursor`） |
| `agent.workspace` | 否 | 智能体工作目录（默认**用户家目录** `~`） |
| `agent.timeout` | 否 | 超时秒数（默认 300） |
| 各后端 `*.cmd` | 否 | CLI 可执行文件名（如 `cursor.cmd`、`openclaw.cmd`）；可选参数见示例配置 |

通过环境变量 **`OPENAB_CONFIG`** 可覆盖配置文件路径。

---

## 智能体后端（前置条件）

- **Cursor：** `agent status` / `agent login`（Cursor CLI）。
- **Codex：** `npm i -g @openai/codex` 或 `brew install --cask codex`，然后 `codex` 或配置 API key。
- **Gemini：** `npm i -g @google/gemini-cli` 或 `brew install gemini-cli`，然后 `gemini`。
- **Claude：** 使用支持 `claude -p "prompt"` 的 CLI；配置中设置 `agent.backend: claude`。
- **OpenClaw：** `npm install -g openclaw`，然后 `openclaw onboard` 并运行 Gateway（`openclaw gateway` 或守护进程）；配置中设置 `agent.backend: openclaw`。

---

## 命令

**命令行**

| 命令 | 说明 |
|------|------|
| `openab` / `openab run` | 启动 Telegram 机器人 |
| `openab run-discord` | 启动 Discord 机器人 |
| `openab config-path` | 打印默认配置文件路径 |

**Telegram 机器人：** `/start` — 欢迎与鉴权；`/whoami` — 显示你的用户 ID（用于白名单）。

**Discord 机器人：** `!start` — 欢迎与鉴权；`!whoami` — 显示你的用户 ID。其他消息会发给智能体（私聊或机器人可读的频道均可）。

---

## 鉴权与安全

- 仅列入 `telegram.allowed_user_ids` 或 `discord.allowed_user_ids` 的用户可发送提示；其他用户会收到「未授权」提示。
- 请勿提交含 token 的配置文件；保持 `~/.config/openab/config.yaml`（或你的 `OPENAB_CONFIG` 路径）私有。

---

## 中英文

- **机器人：** 随聊天应用语言（如 Telegram 的 `language_code`）切换；`zh*` 为中文，否则英文。
- **命令行：** 随环境变量 `LANG`（如 `LANG=zh_CN.UTF-8` 为中文）。

---

## 许可证

MIT — 见 [LICENSE](../LICENSE)。
