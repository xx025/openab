**English:** [../README.md](../README.md)

---

# OpenAB

**Open** **A**gent **B**ridge（开放智能体桥接）—— 连接**智能体后端**（CLI、API 等）与**聊天平台**（Telegram、Discord、Slack 等）的桥接。接入你需要的智能体和聊天应用，由 OpenAB 在中间转发消息，在任意设备、任意支持的聊天应用里使用你的智能体。

| 智能体（后端） | 聊天（前端） |
|---------------|--------------|
| [Cursor](https://cursor.com) CLI ✓ | Telegram ✓   |
| [OpenAI Codex](https://github.com/openai/codex) ✓ | _更多计划中_ |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) ✓ |               |
| Claude CLI ✓  |               |
| _更多计划中_  |               |

---

## 快速开始：智能体 × Telegram

以下步骤以**当前内置的一种组合**为例：一个智能体后端（Cursor 或 Codex）+ Telegram。

### 前置条件

1. **任选一种智能体 CLI** 并完成登录：
   - **Cursor：** `agent status` / `agent login`
   - **Codex：** `npm i -g @openai/codex` 或 `brew install --cask codex`，然后 `codex`（或 `CODEX_API_KEY`）
   - **Gemini：** `npm i -g @google/gemini-cli` 或 `brew install gemini-cli`，然后 `gemini`（或 `GEMINI_API_KEY`）
   - **Claude：** 使用支持 `claude -p "prompt"` 的 CLI，设置 `OPENAB_AGENT=claude` 和 `CLAUDE_CLI_CMD`

2. **Telegram 机器人 Token**  
   在 [@BotFather](https://t.me/BotFather) 创建机器人并获取 token。

3. **[uv](https://docs.astral.sh/uv/)**（推荐）或 Python 3.10+

### 安装

```bash
git clone https://github.com/xx025/openab.git
cd openab
uv sync
```

（uv 会按 `.python-version` 创建虚拟环境并安装依赖；首次需先安装 [uv](https://docs.astral.sh/uv/)。）

### 配置

复制示例环境文件并编辑：

```bash
cp .env.example .env
# 编辑 .env：填写 TELEGRAM_BOT_TOKEN、ALLOWED_USER_IDS
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | 是 | BotFather 提供的 token |
| `ALLOWED_USER_IDS` | 是 | 逗号分隔的 Telegram 用户 ID。**不配置则无人可使用。** 用户可发送 `/whoami` 查看自己的 ID。 |
| `OPENAB_AGENT` | 否 | 智能体后端：`cursor`（默认）、`codex`、`gemini` 或 `claude` |
| `OPENAB_WORKSPACE` | 否 | 智能体工作目录（默认当前目录）。也可使用 `CURSOR_WORKSPACE`。 |
| `OPENAB_AGENT_TIMEOUT` | 否 | 单次执行超时秒数（默认 300） |
| `CURSOR_AGENT_CMD` | 否 | Cursor `agent` 可执行文件路径（默认 PATH 中的 `agent`） |
| `CODEX_CMD` | 否 | Codex CLI 路径（默认 `codex`）。非交互模式 `codex exec`。 |
| `CODEX_SKIP_GIT_CHECK` | 否 | 设为 `1` 可在非 Git 目录运行 Codex |
| `GEMINI_CLI_CMD` | 否 | Gemini CLI 路径（默认 `gemini`）。使用 `gemini -p "prompt"`。 |
| `CLAUDE_CLI_CMD` | 否 | Claude CLI 路径（默认 `claude`）。使用 `claude -p "prompt"`。 |

### 运行

```bash
uv run openab
# 或带参数
uv run openab --token "你的TOKEN" --workspace /path/to/project
```

在 Telegram 中打开机器人并发送文字即可；OpenAB 会将内容交给已配置的智能体处理，回复会分条发回。

---

## 命令（Telegram）

| 命令 | 说明 |
|------|------|
| `/start` | 欢迎语与鉴权状态 |
| `/whoami` | 显示你的 Telegram User ID（用于加入白名单） |

---

## 鉴权（白名单）

- **必须**在 `.env` 或环境中设置 `ALLOWED_USER_IDS=id1,id2,...`。未配置时所有人会看到「鉴权未配置」且无法使用。
- 只有白名单内的用户可向智能体发送内容。
- 其他用户会收到「未授权」提示，可发送 `/whoami` 查看自己的 ID 并请管理员加入白名单。

---

## 中英文

- **机器人**：按用户聊天应用语言（如 Telegram 的 `language_code`）自动选择，中文（`zh*`）显示中文，否则英文。
- **命令行**：按环境变量 `LANG`（如 `LANG=zh_CN.UTF-8` 为中文）。

---

## 安全

- 不要将 `.env` 或 token 提交到仓库；`.gitignore` 已排除 `.env`。
- 务必设置 `ALLOWED_USER_IDS` 限制可使用机器人的用户。

---

## 许可证

MIT — 见 [LICENSE](../LICENSE)。
