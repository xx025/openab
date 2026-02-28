<p align="center">
  <img src="../../assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge（开放智能体桥接）** — 将智能体与聊天平台连接。一份配置、一座桥。**当前已实现：** Cursor、Codex。_Gemini、Claude、OpenClaw 尚未实现。_

[English](../../README.md) · [配置与使用说明](guide.md)

---

## 做什么用

OpenAB 把**聊天平台**或 **HTTP API** 的请求转给你选的智能体后端，并把回复发回。一份配置、一座桥。

| 智能体 | 聊天 / API |
|--------|----------------|
| **Cursor**、**Codex**（已实现）<br>_Gemini、Claude、OpenClaw 尚未实现_ | Telegram、Discord、**OpenAI 兼容 HTTP API**（`openab run serve`）、_更多计划中_ |

---

## 快速开始

**1. 安装**（需 Python 3.10+）

```bash
pip install openab
# 或：uv tool install openab
# 或从仓库：uv pip install -e .
```

**2. 创建配置**

```bash
mkdir -p ~/.config/openab
cp config.example.yaml ~/.config/openab/config.yaml
# 编辑 config.yaml：填写 telegram.bot_token 和/或 discord.bot_token
```

**3. 获取机器人 Token**

- **Telegram：** 打开 [@BotFather](https://t.me/BotFather) → 发送 `/newbot` → 按提示操作 → 把得到的 token 填进配置的 `telegram.bot_token`（或用 `openab run telegram --token <token>` 传入）。
- **Discord：** 打开 [Discord 开发者门户](https://discord.com/developers/applications) → 新建应用 → Bot → 重置 Token → 复制到配置的 `discord.bot_token`（或运行时加 `--token`）。

**4. 把自己加入白名单** — 启动机器人后，在聊天里发送 `/whoami`（Telegram）或 `!whoami`（Discord）得到你的用户 ID。然后任选其一：

- 写入配置：`openab config set telegram.allowed_user_ids "你的ID"`（或 `discord.allowed_user_ids`），**或**
- 把 API key（先运行一次 `openab run serve` 会打印）作为一条消息发给机器人，会自动把你加入白名单。

**5. 运行并开始聊天**

```bash
openab run telegram   # 或：openab run discord
# 在 Telegram/Discord 里打开你的机器人，发任意消息即可。输入 /resume 可看到会话按钮（延续上一会话、创建新会话、或选择历史会话）。
```

- **仅用 API：** 运行 `openab run serve`，无需机器人 token。将客户端指向 `http://127.0.0.1:8000/v1`，鉴权用启动时打印的 API key。
- 没有配置时，直接运行 `openab` 或 `openab run` 会默认启动 API 服务并给出提示。

完整选项见 [配置与使用说明](guide.md)。

---

## 文档

- **[配置与使用说明](guide.md)** — 配置项、智能体前置、命令、API 服务、安全、中英文。

---

## 许可证

MIT — [LICENSE](../../LICENSE)
