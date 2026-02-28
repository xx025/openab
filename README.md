# Cursor CLI × Telegram 机器人

将 Cursor Agent CLI 对接到 Telegram，在手机或任意端通过对话使用 Cursor 的 AI 能力。

## 前置条件

1. **Cursor Agent CLI 已安装并登录**
   ```bash
   agent status   # 确认已登录
   agent login    # 未登录时执行
   ```

2. **Telegram Bot Token**
   - 在 [@BotFather](https://t.me/BotFather) 创建机器人，获取 token。

3. **Python 3.10+**

## 安装

```bash
cd cursor-telegram-bot
pip install -r requirements.txt
```

## 配置

复制环境变量示例并填写：

```bash
cp .env.example .env
# 编辑 .env，填入 TELEGRAM_BOT_TOKEN
```

或直接设置环境变量：

- `TELEGRAM_BOT_TOKEN`（必填）：Telegram 机器人 token。
- `CURSOR_AGENT_CMD`（可选）：默认 `agent`，若 agent 不在 PATH 可写绝对路径。
- `CURSOR_WORKSPACE`（可选）：Agent 工作目录，默认当前目录。
- `ALLOWED_USER_IDS`（可选）：鉴权白名单。逗号分隔的 Telegram 用户 ID；不填则允许所有人。用户发送 `/whoami` 可查看自己的 ID。

## 运行

```bash
# 长轮询模式（推荐，无需公网）
python -m cursor_telegram_bot run

# 或使用 typer CLI
python -m cursor_telegram_bot run --token "YOUR_BOT_TOKEN"
```

与机器人对话：在 Telegram 中给机器人发文字，内容会作为 prompt 传给 Cursor Agent，回复会流式/分片发回。

## 用户鉴权

- 在 `.env` 中设置 `ALLOWED_USER_IDS=用户ID1,用户ID2` 后，只有白名单内的用户可调用 Cursor Agent。
- 未授权用户发送任意文字会收到无权限提示；发送 `/whoami` 可查看自己的 Telegram User ID，提供给管理员加入白名单即可。
- 发送 `/start` 可查看欢迎语及当前鉴权状态。

## 安全建议

- 不要将 `.env` 或 token 提交到仓库。
- 生产环境建议设置 `ALLOWED_USER_IDS` 限制可用的 Telegram 用户。
