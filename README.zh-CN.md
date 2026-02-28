**English:** [README.md](README.md)

---

# OpenAB

**Open** **A**gent **B**ridge（开放智能体桥接）—— 连接**智能体后端**（CLI、API 等）与**聊天平台**（Telegram、Discord、Slack 等）的桥接。接入你需要的智能体和聊天应用，由 OpenAB 在中间转发消息，在任意设备、任意支持的聊天应用里使用你的智能体。

| 智能体（后端） | 聊天（前端） |
|---------------|--------------|
| Cursor CLI ✓  | Telegram ✓   |
| _更多计划中_  | _更多计划中_ |

---

## 快速开始：智能体 × Telegram

以下步骤以**当前内置的一种组合**为例：一个智能体后端（Cursor CLI）+ Telegram。其他组合后续会陆续加入。

### 前置条件

1. **Cursor Agent CLI** 已安装并登录  
   ```bash
   agent status   # 确认已登录
   agent login    # 未登录时执行
   ```

2. **Telegram 机器人 Token**  
   在 [@BotFather](https://t.me/BotFather) 创建机器人并获取 token。

3. **Python 3.10+**

### 安装

```bash
git clone https://github.com/xx025/openab.git
cd openab
pip install -r requirements.txt
```

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
| `CURSOR_AGENT_CMD` | 否 | `agent` 可执行文件路径（默认使用 PATH 中的 `agent`） |
| `CURSOR_WORKSPACE` | 否 | Agent 工作目录（默认当前目录） |
| `CURSOR_AGENT_TIMEOUT` | 否 | 单次执行超时秒数（默认 300） |

### 运行

```bash
# 长轮询（无需公网）
python -m cursor_telegram_bot

# 或带参数
python -m cursor_telegram_bot --token "你的TOKEN" --workspace /path/to/project
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

MIT — 见 [LICENSE](LICENSE)。
