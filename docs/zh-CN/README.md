<p align="center">
  <img src="../../assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge（开放智能体桥接）** — 将智能体（Cursor、Codex、Gemini、Claude、OpenClaw）与聊天平台连接。一份配置、一座桥。

[English](../../README.md) · [配置与使用说明](guide.md)

---

## 做什么用

OpenAB 把**聊天平台**的消息转给你选的智能体后端，并把回复发回。不用为每个智能体各起一个机器人 — 配置一次即可聊天。

| 智能体 | 聊天 |
|--------|------|
| Cursor、Codex、Gemini、Claude、OpenClaw | Telegram、Discord、_更多计划中_ |

---

## 快速开始

**1. 安装**（需 Python 3.10+）

```bash
pip install openab
# 或：uv tool install openab
```

**2. 配置** — 在 `~/.config/openab/` 下放一份 YAML/JSON 配置（参考 [config.example.yaml](../../config.example.yaml)）。至少需要机器人 token 和用户 ID 白名单。完整选项见 [配置与使用说明](guide.md)。

**3. 运行**

```bash
openab              # 如 Telegram
openab run-discord  # 如 Discord
```

然后在对应聊天应用里打开机器人发消息即可。

---

## 文档

- **[配置与使用说明](guide.md)** — 配置项、智能体前置、命令、安全、中英文。

---

## 许可证

MIT — [LICENSE](../../LICENSE)
