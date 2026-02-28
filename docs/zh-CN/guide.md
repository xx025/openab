# OpenAB — 配置与使用说明

配置、智能体后端、命令与安全的技术参考。当前聊天前端包括 Telegram 与 Discord，后续可能增加更多平台。

[English](../en/guide.md) · **中文**

---

**运行环境：** OpenAB 支持 **Linux** 与 **macOS**。所有 CLI 命令（`openab run serve`、`openab run telegram`、`openab run discord`、`openab config`、各智能体后端）在两者上均可使用。**install-service**（systemd 用户服务）**仅支持 Linux**；在 macOS 上请直接运行 `openab run telegram` 或 `openab run discord`。

---

## 配置

OpenAB 使用 **YAML 或 JSON** 配置文件。默认路径：`~/.config/openab/config.yaml`。可通过环境变量 **`OPENAB_CONFIG`** 覆盖。

创建 `~/.config/openab/` 并将仓库中的 [config.example.yaml](../../config.example.yaml) 或 [config.example.json](../../config.example.json) 复制为 `config.yaml` 或 `config.json`。也可通过 CLI 编辑配置：

| 命令 | 说明 |
|------|------|
| `openab config path` | 打印配置文件路径（当前或默认） |
| `openab config get [key]` | 显示完整配置或点号键对应值（如 `agent.backend`） |
| `openab config set <key> <value>` | 设置键并保存（如 `openab config set agent.backend openclaw`；用户 ID 列表用逗号：`openab config set telegram.allowed_user_ids "123,456"`） |

新键会写入已有配置文件（按路径的 YAML 或 JSON）；若尚无文件，首次 `set` 时使用并创建默认路径。

### 配置项说明

| 键 | 是否必填 | 说明 |
|----|----------|------|
| `telegram.bot_token` | 运行 `run` 时 | 来自 [@BotFather](https://t.me/BotFather) 的 Bot Token |
| `telegram.allowed_user_ids` | 运行 `run` 时 | Telegram 用户 ID 列表。空则无人可用。用户可用 `/whoami` 查看自己的 ID。 |
| `discord.bot_token` | 运行 `run discord` 时 | 来自 [Discord 开发者门户](https://discord.com/developers/applications) 的 Bot Token |
| `discord.allowed_user_ids` | 运行 `run discord` 时 | Discord 用户 ID 列表。空则无人可用。用户可在私信中用 `!whoami` 查看 ID。 |
| `agent.backend` | 否 | `cursor`、`codex`、`gemini`、`claude`、`openclaw`（默认：`cursor`） |
| `agent.workspace` | 否 | 智能体工作目录（默认：**用户家目录** `~`） |
| `agent.timeout` | 否 | 超时秒数（默认：300） |
| `cursor.cmd`、`codex.cmd`、`gemini.cmd`、`claude.cmd`、`openclaw.cmd` | 否 | 各后端对应的 CLI 可执行文件名 |
| 各后端专用选项 | 否 | 如 `openclaw.thinking`（off \| minimal \| low \| medium \| high \| xhigh）、`claude.model`、`codex.skip_git_check` 等，见 [config.example.yaml](../../config.example.yaml)。 |
| `api.key` | 否 | 若设置，访问 `openab run serve` 的请求需携带 `Authorization: Bearer <api.key>`。不设则仅限本地/无鉴权使用。 |
| `api.host` | 否 | `openab run serve` 监听地址（默认 `127.0.0.1`），可用 `--host` 覆盖。 |
| `api.port` | 否 | `openab run serve` 监听端口（默认 `8000`），可用 `--port` 覆盖。 |

---

## OpenAI API 兼容服务

运行 `openab run serve` 可启动与 OpenAI 兼容的 HTTP 接口：

- **端点：** `POST /v1/chat/completions`、`GET /v1/models`、`POST /v1/responses`
- **鉴权：** 若在配置中设置了 `api.key`，请求需携带 `Authorization: Bearer <api.key>`。若未设置 `api.key`，首次启动时会自动生成并写入配置并打印（每次启动也会打印当前 key）。
- **客户端：** 使用 `base_url=http://127.0.0.1:8000/v1` 与打印的 API key。最后一条用户消息会发给当前配置的智能体，回复以 `choices[0].message.content`（chat）或 `output_text` / `output[].content`（responses）返回。**流式：** chat completions 支持 `stream: true`（单块 SSE）。
- **自助加白名单：** 在 Telegram 或 Discord 中，任何人发送与 `api.key` 完全一致的一条消息即可被加入该平台白名单并写回配置，无需重启。

---

## 智能体后端（前置要求）

- **Cursor：** Cursor CLI — `agent status` / `agent login`。
- **Codex：** `npm i -g @openai/codex` 或 `brew install --cask codex`；然后使用 `codex` 或配置 API key。
- **Gemini：** `npm i -g @google/gemini-cli` 或 `brew install gemini-cli`；然后使用 `gemini`。
- **Claude：** 支持 `claude -p "prompt"` 的 CLI；在配置中设置 `agent.backend: claude`。
- **OpenClaw：** `npm install -g openclaw`，然后执行 `openclaw onboard` 并运行 Gateway（`openclaw gateway` 或守护进程）；配置中设置 `agent.backend: openclaw`。

---

## 命令

### CLI

| 命令 | 说明 |
|------|------|
| `openab` | 无子命令时：先检查配置；若配置为空则提示并默认启动 API 服务（run serve），否则显示帮助。 |
| `openab run serve` | 启动 OpenAI API 兼容 HTTP 服务（`POST /v1/chat/completions`、`GET /v1/models`）。可选 `--host`、`--port` 或配置 `api.host` / `api.port`。 |
| `openab run telegram` | 运行 Telegram 机器人 |
| `openab run discord` | 运行 Discord 机器人 |
| `openab run` | 未指定 run 目标时：同 `openab`（检查配置，空则 run serve，否则显示 run 帮助）。 |
| `openab config path` | 打印配置文件路径 |
| `openab config get [key]` | 显示配置或指定键的值 |
| `openab config set <key> <value>` | 设置配置键并保存 |
| `openab install-service` | 安装为 **Linux 用户级 systemd 服务**（可选 `--discord` 装 Discord、`--start` 立即启动）。**仅 Linux。** 在 macOS 上请直接运行 `openab run telegram` 或 `openab run discord`（或自行配置 launchd）。 |

选项：`--config` / `-c` 指定配置文件；`run telegram` / `run discord` 可用 `--token`、`--workspace`、`--verbose`；`run serve` 可用 `--host`、`--port`。

### Telegram 机器人

| 命令 | 说明 |
|------|------|
| `/start` | 欢迎语与鉴权状态 |
| `/whoami` | 显示你的 Telegram 用户 ID（用于白名单） |

其他消息会转发给智能体。

### Discord 机器人

| 命令 | 说明 |
|------|------|
| `!start` | 欢迎语与鉴权状态 |
| `!whoami` | 显示你的 Discord 用户 ID（用于白名单） |

其他消息会转发给智能体（私信或机器人可读的频道）。

---

## 鉴权与安全

- 仅列入 `telegram.allowed_user_ids` 或 `discord.allowed_user_ids` 的用户可发送提示；其他用户会收到「未授权」提示。也可设置 `telegram.allow_all` 或 `discord.allow_all` 为 `true`（请谨慎使用）。
- **用 token 加白名单：** 在 Telegram 或 Discord 中，发送内容与配置里 `api.key` 完全一致的一条消息，即可将发送者加入该平台白名单并写回配置（无需重启）。
- 请勿将含 token 的配置文件提交到仓库。保持 `~/.config/openab/config.yaml`（或你设置的 `OPENAB_CONFIG` 路径）私密。

---

## 多语言（i18n）

- **机器人：** 语言随聊天应用（如 Telegram 的 `language_code`）。`zh*` → 中文；其余为英文。
- **CLI：** 随环境变量 `LANG`（如 `LANG=zh_CN.UTF-8` 为中文）。
