[**中文**](README.md) · [**English**](../../README.md)

<p align="center">
  <img src="../../assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge（开放智能体桥接）** — 将智能体与聊天平台连接。一份配置、一座桥。**当前已实现：** Cursor、Codex。_Gemini、Claude、OpenClaw 尚未实现。_

[配置与使用说明](guide.md)

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

**2. 运行并按提示操作**

```bash
openab run
```

按提示选择 **serve**（API）、**telegram** 或 **discord**，需要时输入 Bot Token 和白名单；选择会自动写入 `~/.config/openab/config.yaml`。然后在应用里打开机器人即可聊天，或使用 API：`http://127.0.0.1:8000/v1` 配合打印的 key。聊天里输入 `/resume` 或 `!resume` 可切换会话。

- **Token 获取：** Telegram 找 [@BotFather](https://t.me/BotFather) 发 `/newbot`；Discord 到 [开发者门户](https://discord.com/developers/applications) → Bot → 重置 Token。
- **未授权？** 在聊天里发 `/whoami` 或 `!whoami` 得到 ID，再执行 `openab config set telegram.allowed_user_ids "ID"`，或把 API key 发给机器人自助加白。

完整选项见 [配置与使用说明](guide.md)。

---

## 文档

- **[配置与使用说明](guide.md)** — 配置项、智能体前置、命令、API 服务、安全、中英文。

---

## 许可证

MIT — [LICENSE](../../LICENSE)
