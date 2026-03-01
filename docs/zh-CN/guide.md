# OpenAB — 配置与使用说明

配置、智能体后端、命令与安全的技术参考。当前聊天前端包括 Telegram 与 Discord，后续可能增加更多平台。

[English](../en/guide.md) · **中文**

---

## 新手上路（第一次使用）

按下面步骤即可在几分钟内用上机器人或 API：

1. **安装** — `pip install openab`（需 Python 3.10+）。
2. **选平台** — 用 **Telegram** 或 **Discord** 聊天，或只用 **HTTP API**（`openab run serve`，无需机器人）。
3. **拿 Token**  
   - Telegram： [@BotFather](https://t.me/BotFather) → `/newbot` → 复制 Bot Token。  
   - Discord： [开发者门户](https://discord.com/developers/applications) → 新建应用 → Bot → 重置 Token。
4. **写配置** — `mkdir -p ~/.config/openab`，把仓库里的 [config.example.yaml](../../config.example.yaml) 复制为 `config.yaml`，填上 `telegram.bot_token` 或 `discord.bot_token`（也可用 `openab run telegram --token <token>` 传入，不写进文件）。
5. **加白名单** — 启动机器人后，在聊天里发 `/whoami`（Telegram）或 `!whoami`（Discord）得到你的 ID，然后执行 `openab config set telegram.allowed_user_ids "你的ID"`（或 `discord.allowed_user_ids`）；**或者** 先运行一次 `openab run serve` 记下打印的 API key，再在聊天里把这条 key 原样发给机器人，会自动加白并写回配置。
6. **运行** — `openab run telegram` 或 `openab run discord`。在应用里打开你的机器人，发任意消息即可与智能体对话。
7. **会话切换** — 输入 `/resume`（Telegram）或 `!resume`（Discord）会弹出按钮：**延续上一会话**、**创建新会话**、以及从本机 Cursor 会话列表里选一个历史会话（点击即可切换）。

遇到「未授权」：确认你的用户 ID 已在对应平台的 `allowed_user_ids` 中，或已通过发送 API key 自助加白。更多见下方 [鉴权与安全](#鉴权与安全)。

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
| `telegram.bot_token` | 运行 `run telegram` 时 | 来自 [@BotFather](https://t.me/BotFather) 的 Bot Token；也可用 `openab run telegram --token <token>` 传入。 |
| `telegram.allowed_user_ids` | 运行 `run` 时 | Telegram 用户 ID 列表。空则无人可用。用户可用 `/whoami` 查看自己的 ID。 |
| `discord.bot_token` | 运行 `run discord` 时 | 来自 [Discord 开发者门户](https://discord.com/developers/applications) 的 Bot Token；也可用 `openab run discord --token <token>` 传入。 |
| `discord.allowed_user_ids` | 运行 `run discord` 时 | Discord 用户 ID 列表。空则无人可用。用户可在私信中用 `!whoami` 查看 ID。 |
| `agent.backend` | 否 | `cursor`、`agent`（与 cursor 等价，Cursor CLI 名为 agent）、`codex`（已实现）；`gemini`、`claude`、`openclaw` _尚未实现_（默认：`cursor`） |
| `agent.workspace` | 否 | 智能体工作目录（默认：**用户家目录** `~`） |
| `agent.timeout` | 否 | 超时秒数（默认：300） |
| `cursor.cmd`、`codex.cmd`、`gemini.cmd`、`claude.cmd`、`openclaw.cmd` | 否 | 各后端对应的 CLI 可执行文件名 |
| 各后端专用选项 | 否 | 如 `openclaw.thinking`（off \| minimal \| low \| medium \| high \| xhigh）、`claude.model`、`codex.skip_git_check` 等，见 [config.example.yaml](../../config.example.yaml)。 |
| `api.key` | 否 | 若设置，访问 `openab run serve` 的请求需携带 `Authorization: Bearer <api.key>`。不设则仅限本地/无鉴权使用。也可用 `openab run serve --token <key>` 覆盖本次启动的 API key。 |
| `api.host` | 否 | `openab run serve` 监听地址（默认 `127.0.0.1`），可用 `--host` 覆盖。 |
| `api.port` | 否 | `openab run serve` 监听端口（默认 `8000`），可用 `--port` 覆盖。 |
| `service.run` | 否 | `openab run`（无子命令）及 **install-service** 安装的 systemd 服务启动目标，**仅从本项解析**：`serve` \| `telegram` \| `discord`。不设或无效时默认为 `serve`。 |

---

## OpenAI API 兼容服务

运行 `openab run serve` 可启动与 OpenAI 兼容的 HTTP 接口：

- **端点：** `POST /v1/chat/completions`、`GET /v1/models`、`POST /v1/responses`
- **鉴权：** 若在配置中设置了 `api.key`，请求需携带 `Authorization: Bearer <api.key>`。使用 `openab run serve --token <key>` 可覆盖配置中的 API key（仅本次生效）。若未设置且未传 `--token`，首次启动时会自动生成并写入配置并打印（每次启动也会打印当前 key）。
- **客户端：** 使用 `base_url=http://127.0.0.1:8000/v1` 与打印的 API key。最后一条用户消息会发给当前配置的智能体，回复以 `choices[0].message.content`（chat）或 `output_text` / `output[].content`（responses）返回。**流式：** chat completions 支持 `stream: true`（单块 SSE）。
- **自助加白名单：** 在 Telegram 或 Discord 中，任何人发送与 `api.key` 完全一致的一条消息即可被加入该平台白名单并写回配置，无需重启。

---

## 智能体后端（前置要求）

**当前已实现：** Cursor、Codex。**尚未实现：** Gemini、Claude、OpenClaw（配置项存在但端到端可能不可用）。

- **Cursor：** Cursor CLI — `agent status` / `agent login`。默认带 `--continue` 延续上一会话；在配置中设置 `cursor.continue_session: false` 可改为每次新会话。
- **Codex：** `npm i -g @openai/codex` 或 `brew install --cask codex`；然后使用 `codex` 或配置 API key。支持与 Cursor 类似的会话延续与历史列表。
- **Gemini：** _尚未实现。_ 计划：`npm i -g @google/gemini-cli` 或 `brew install gemini-cli`；然后使用 `gemini`。
- **Claude：** _尚未实现。_ 计划：支持 `claude -p "prompt"` 的 CLI；在配置中设置 `agent.backend: claude`。
- **OpenClaw：** _尚未实现。_ 计划：`npm install -g openclaw`，然后执行 `openclaw onboard` 并运行 Gateway（`openclaw gateway` 或守护进程）；配置中设置 `agent.backend: openclaw`。

---

## 命令

### CLI

| 命令 | 说明 |
|------|------|
| `openab` | 无子命令时：根据配置自动选择 **serve** / **telegram** / **discord**（同 `openab run`）。 |
| `openab run serve` | 启动 OpenAI API 兼容 HTTP 服务（`POST /v1/chat/completions`、`GET /v1/models`）。可选 `--token`（API key）、`--host`、`--port` 或配置 `api.key` / `api.host` / `api.port`。 |
| `openab run telegram` | 运行 Telegram 机器人。可选 `--token`、`--workspace`、`--verbose`。 |
| `openab run discord` | 运行 Discord 机器人。可选 `--token`、`--workspace`、`--verbose`。 |
| `openab run` | 未指定 run 目标时：从配置文件解析 **service.run**（`serve` \| `telegram` \| `discord`），未配置时默认 `serve`。 |
| `openab config path` | 打印配置文件路径 |
| `openab config get [key]` | 显示配置或指定键的值 |
| `openab config set <key> <value>` | 设置配置键并保存 |
| `openab install-service` | 安装为 **Linux 用户级 systemd 服务**，服务通过**配置文件**启动（执行 `openab run`，目标**仅从配置中的 service.run 解析**）。可选 `--discord` 额外安装 Discord 专用服务、`--start` 立即启动。**仅 Linux。** |

**全局选项**（如 `openab -c /path/config.yaml run telegram`）：`--config` / `-c` 配置文件路径；`--workspace` / `-w` 工作目录；`--verbose` / `-v` 调试日志。**子命令选项**：`run telegram` / `run discord` 支持 `--token` / `-t`（Bot Token）、`--workspace`、`--verbose`；`run serve` 支持 `--token` / `-t`（API key，覆盖配置）、`--host`、`--port`。

### Telegram 机器人

| 命令 | 说明 |
|------|------|
| `/start` | 欢迎语与鉴权状态 |
| `/whoami` | 显示你的 Telegram 用户 ID（用于加入白名单） |
| `/new` | 创建新会话（下一条消息在新会话中处理；仅 Cursor 后端） |
| `/resume` | **推荐**：不填参数时弹出按钮，可点击「延续上一会话」「创建新会话」或从本机 Cursor 历史会话列表中选择一个切换 |
| `/resume [会话ID]` | 直接切换到指定会话（会话 ID 来自本机 `~/.cursor/chats` 下的会话列表） |
| `/sessions` | 说明如何查看与切换会话 |

其他消息会转发给智能体。

### Discord 机器人

| 命令 | 说明 |
|------|------|
| `!start` | 欢迎语与鉴权状态 |
| `!whoami` | 显示你的 Discord 用户 ID（用于加入白名单） |
| `!new` | 创建新会话（下一条消息在新会话中处理；仅 Cursor 后端） |
| `!resume` | **推荐**：不填参数时出现按钮，可点击「延续上一会话」「创建新会话」或从本机 Cursor 历史会话中选择一个切换 |
| `!resume [会话ID]` | 直接切换到指定会话 |
| `!sessions` | 说明如何查看与切换会话 |

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

---

## 常见问题

| 问题 | 处理 |
|------|------|
| 发消息提示「未授权」 | 在聊天里发 `/whoami` 或 `!whoami` 得到你的 ID，用 `openab config set telegram.allowed_user_ids "ID"`（或 `discord.allowed_user_ids`）加入白名单；或把配置里的 `api.key`（或启动 serve 时打印的 key）原样发给机器人自助加白。 |
| Cursor 报未登录或不可用 | 在终端执行 `agent status` 或 `agent login`，确保 Cursor CLI 已登录且可用。 |
| `/resume` 没有历史会话按钮 | 历史会话来自本机 `~/.cursor/chats`。若从未在 Cursor 里聊过，或目录为空，则只显示「延续上一会话」和「创建新会话」。 |
| 想每次都是新会话 | 在配置中设置 `cursor.continue_session: false`。 |
| 修改配置后要重启吗？ | 白名单、API key 等通过「发 API key 加白」或 `config set` 写回配置后无需重启；修改 `agent.backend`、`workspace`、token 等需重启当前运行的 `openab run` 进程。 |
