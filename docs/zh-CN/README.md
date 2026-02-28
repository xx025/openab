<p align="center">
  <img src="../../assets/icon.png" width="256" alt="OpenAB" />
</p>

# OpenAB

**Open Agent Bridge（开放智能体桥接）** — 将智能体（Cursor、Codex、Gemini、Claude、OpenClaw）与聊天平台连接。一份配置、一座桥。

[English](../../README.md) · [配置与使用说明](guide.md)

---

## 做什么用

OpenAB 把**聊天平台**或 **HTTP API** 的请求转给你选的智能体后端，并把回复发回。一份配置、一座桥。

| 智能体 | 聊天 / API |
|--------|----------------|
| Cursor、Codex、Gemini、Claude、OpenClaw | Telegram、Discord、**OpenAI 兼容 HTTP API**（`openab run serve`）、_更多计划中_ |

---

## 快速开始

**1. 安装**（需 Python 3.10+）

```bash
pip install openab
# 或从仓库：uv pip install -e .
# 或：uv tool install openab
```

**2. 配置** — 在 `~/.config/openab/` 下放一份 YAML/JSON 配置（参考 [config.example.yaml](../../config.example.yaml)）。至少需要机器人 token（Telegram/Discord）或仅用 API 可不配；白名单或 `api.key` 用于鉴权。Bot token 也可通过 `--token` 传入（如 `openab run telegram --token <token>`）；API 服务可用 `openab run serve --token <key>` 指定本次 API key。完整选项见 [配置与使用说明](guide.md)。

**3. 运行**

```bash
openab run serve     # OpenAI 兼容 API（POST /v1/chat/completions、GET /v1/models、POST /v1/responses）
openab run telegram  # Telegram 机器人（可选 --token、--workspace、--verbose）
openab run discord   # Discord 机器人（可选 --token、--workspace、--verbose）
```

- 无配置时运行 `openab` 或 `openab run` 会提示并默认启动 API 服务。
- 在聊天应用里打开机器人发消息，或将任意 OpenAI 兼容客户端指向 `http://127.0.0.1:8000/v1`，使用启动时打印的 API key。

---

## 文档

- **[配置与使用说明](guide.md)** — 配置项、智能体前置、命令、API 服务、安全、中英文。

---

## 许可证

MIT — [LICENSE](../../LICENSE)
