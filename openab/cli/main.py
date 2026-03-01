"""OpenAB CLI：以 Typer + Path 传参为主，配置来自用户目录 YAML/JSON；仅全局配置路径用环境变量 OPENAB_CONFIG。"""
from __future__ import annotations

import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from openab.chats.discord import run_bot as run_discord_bot
from openab.chats.telegram import run_bot as run_telegram_bot
from openab.core.config import (
    coerce_config_value,
    get_config_path,
    get_config_file_path,
    load_config,
    parse_allowed_user_ids,
    resolve_workspace,
    save_config,
    _get_nested,
    _set_nested,
)
from openab.core.detect_cli import BACKEND_CLI_NAMES, detect_available_backends
from openab.core.i18n import cli_t

load_dotenv()

app = typer.Typer(
    name="openab",
    help=cli_t("cli_help"),
    no_args_is_help=True,
)


# 终端红色粗体（仅 TTY 时使用，避免污染日志）
_CLI_RED = "\033[1;31m"
_CLI_RESET = "\033[0m"


def _echo_severe_warning(msg: str) -> None:
    """向 stderr 输出严重警告，在 TTY 下使用红色粗体。"""
    if sys.stderr.isatty():
        typer.echo(_CLI_RED + msg + _CLI_RESET, err=True)
    else:
        typer.echo(msg, err=True)


def _echo_config_file_path() -> None:
    """启动时打印当前使用的配置文件路径。"""
    typer.echo(cli_t("config_file_used", path=str(get_config_file_path())))


def _get_workspace(config: dict, workspace: Optional[Path]) -> Path:
    return resolve_workspace(config, workspace)


def _config_empty(config: dict) -> bool:
    """配置为空或未配置（无 Telegram/Discord token）时视为空，可默认 run serve。"""
    tg = (config.get("telegram") or {}).get("bot_token") or ""
    dc = (config.get("discord") or {}).get("bot_token") or ""
    return (not (tg and str(tg).strip())) and (not (dc and str(dc).strip()))


def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _ensure_agent_backend(config: dict) -> dict:
    """若未配置 agent.backend 且当前在交互环境，检测可用后端并引导选择，可选保存。配置里已指定 backend 则直接使用、不引导。"""
    if not _is_interactive():
        return config
    # 配置中已指定 agent.backend 时直接启动，不检测、不提示
    current = (config.get("agent") or {}).get("backend")
    if current is not None and str(current).strip():
        return config
    available = detect_available_backends()
    if not available:
        return config
    cmd_by_backend = dict(BACKEND_CLI_NAMES)
    typer.echo("")
    typer.echo(cli_t("run_backends_detected"))
    for i, (bid, _) in enumerate(available, 1):
        typer.echo(f"  {i}) {bid} ({cmd_by_backend.get(bid, bid)})")
    try:
        raw = input(cli_t("run_backend_prompt", n=len(available))).strip() or "1"
        idx = int(raw)
        if 1 <= idx <= len(available):
            _set_nested(config, "agent.backend", available[idx - 1][0])
            get_config_path().parent.mkdir(parents=True, exist_ok=True)
            save_config(config)
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    return config


def _ensure_telegram_run_config(
    config: dict, token_cli: Optional[str]
) -> tuple[str, frozenset[int], dict]:
    """若配置/CLI 无 token 且在交互环境则引导输入并可选保存；返回 (token, allowed_user_ids, config)。"""
    t = (token_cli or "").strip() or (config.get("telegram") or {}).get("bot_token") or ""
    t = (t or "").strip()
    if not t and _is_interactive():
        try:
            t = input(cli_t("run_prompt_telegram_token")).strip()
            if t:
                config.setdefault("telegram", {})["bot_token"] = t
                get_config_path().parent.mkdir(parents=True, exist_ok=True)
                save_config(config)
        except (EOFError, KeyboardInterrupt):
            pass
    if not t:
        typer.echo(cli_t("err_no_token"), err=True)
        raise typer.Exit(1)
    allowed = parse_allowed_user_ids((config.get("telegram") or {}).get("allowed_user_ids"))
    if not allowed and _is_interactive():
        try:
            val = input(cli_t("run_prompt_allowed_telegram")).strip()
            if val:
                ids = coerce_config_value("telegram.allowed_user_ids", val)
                _set_nested(config, "telegram.allowed_user_ids", ids)
                save_config(config)
                allowed = parse_allowed_user_ids(ids)
        except (EOFError, KeyboardInterrupt):
            pass
    return (t, allowed, config)


def _ensure_discord_run_config(
    config: dict, token_cli: Optional[str]
) -> tuple[str, frozenset[int], dict]:
    """若配置/CLI 无 token 且在交互环境则引导输入并可选保存；返回 (token, allowed_user_ids, config)。"""
    t = (token_cli or "").strip() or (config.get("discord") or {}).get("bot_token") or ""
    t = (t or "").strip()
    if not t and _is_interactive():
        try:
            t = input(cli_t("run_prompt_discord_token")).strip()
            if t:
                config.setdefault("discord", {})["bot_token"] = t
                get_config_path().parent.mkdir(parents=True, exist_ok=True)
                save_config(config)
        except (EOFError, KeyboardInterrupt):
            pass
    if not t:
        typer.echo(cli_t("err_no_token_discord"), err=True)
        raise typer.Exit(1)
    allowed = parse_allowed_user_ids((config.get("discord") or {}).get("allowed_user_ids"))
    if not allowed and _is_interactive():
        try:
            val = input(cli_t("run_prompt_allowed_discord")).strip()
            if val:
                ids = coerce_config_value("discord.allowed_user_ids", val)
                _set_nested(config, "discord.allowed_user_ids", ids)
                save_config(config)
                allowed = parse_allowed_user_ids(ids)
        except (EOFError, KeyboardInterrupt):
            pass
    return (t, allowed, config)


def _ensure_api_key(config: dict) -> dict:
    """若配置中无 api.key 则生成随机 token 并写入配置文件，返回可能已修改的 config。"""
    api_cfg = config.get("api")
    if api_cfg is None:
        api_cfg = {}
        config["api"] = api_cfg
    existing = (api_cfg.get("key") or api_cfg.get("api_key")) or ""
    if isinstance(existing, bool):
        existing = ""
    existing = (existing or "").strip()
    if existing:
        return config
    new_key = secrets.token_urlsafe(32)
    api_cfg["key"] = new_key
    get_config_path().parent.mkdir(parents=True, exist_ok=True)
    save_config(config)
    typer.echo(cli_t("api_key_generated", api_key=new_key, config_path=str(get_config_file_path())))
    return config


def _do_serve(
    host: Optional[str] = None,
    port: Optional[int] = None,
    token: Optional[str] = None,
) -> None:
    """启动 OpenAI API 兼容 HTTP 服务（供 run serve 与默认无配置时调用）。token 覆盖配置中的 api.key。"""
    from openab.api import create_app
    import uvicorn

    config_path = get_config_file_path()
    _echo_config_file_path()
    config = load_config()
    if not (token or "").strip():
        config = _ensure_api_key(config)
    api_cfg = config.get("api") or {}
    api_key = (token or "").strip() or (api_cfg.get("key") or api_cfg.get("api_key")) or ""
    if isinstance(api_key, bool):
        api_key = ""
    api_key = (api_key or "").strip()
    bind_host = host if host is not None else api_cfg.get("host") or "127.0.0.1"
    bind_port = port if port is not None else (api_cfg.get("port") if api_cfg.get("port") is not None else 8000)
    bind_port = int(bind_port)

    fastapi_app = create_app(config_path=config_path, api_key_override=token and token.strip() or None)
    typer.echo(cli_t("serve_listen", host=bind_host, port=bind_port))
    typer.echo(cli_t("api_key_display", api_key=api_key))
    uvicorn.run(fastapi_app, host=bind_host, port=bind_port)


@app.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(None, "--config", "-c", path_type=Path, help=cli_t("opt_config")),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help=cli_t("opt_workspace")),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=cli_t("opt_verbose")),
) -> None:
    if config is not None:
        os.environ["OPENAB_CONFIG"] = str(config.expanduser().resolve())
    if ctx.invoked_subcommand is not None:
        return
    # 无子命令：根据配置选择 serve / telegram / discord，未配置且交互时引导用户选择
    cfg = load_config()
    target = _resolve_run_target_from_config(cfg)
    if not target and _is_interactive():
        target = _prompt_run_target(cfg)
    if not target:
        target = "serve"
    if target == "serve":
        if _config_empty(cfg):
            typer.echo(cli_t("default_no_config_run_serve"))
        _do_serve()
        return
    if target == "telegram":
        _echo_config_file_path()
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        cfg = _ensure_agent_backend(cfg)
        t, allowed, cfg = _ensure_telegram_run_config(cfg, None)
        ws = _get_workspace(cfg, None)
        timeout = int((cfg.get("agent") or {}).get("timeout") or 300)
        allow_all = (cfg.get("telegram") or {}).get("allow_all") is True
        if not allowed and not allow_all:
            typer.echo(cli_t("allowlist_empty_warning"), err=True)
        if allow_all:
            _echo_severe_warning(cli_t("allow_all_severe_warning"))
        typer.echo(cli_t("starting"))
        run_telegram_bot(t, workspace=ws, timeout=timeout, allowed_user_ids=allowed, allow_all=allow_all, config_path=get_config_file_path(), agent_config=cfg)
        return
    if target == "discord":
        _echo_config_file_path()
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        cfg = _ensure_agent_backend(cfg)
        t, allowed, cfg = _ensure_discord_run_config(cfg, None)
        ws = _get_workspace(cfg, None)
        timeout = int((cfg.get("agent") or {}).get("timeout") or 300)
        allow_all = (cfg.get("discord") or {}).get("allow_all") is True
        if not allowed and not allow_all:
            typer.echo(cli_t("allowlist_empty_warning"), err=True)
        if allow_all:
            _echo_severe_warning(cli_t("allow_all_severe_warning"))
        typer.echo(cli_t("starting_discord"))
        run_discord_bot(t, workspace=ws, timeout=timeout, allowed_user_ids=allowed, allow_all=allow_all, config_path=get_config_file_path(), agent_config=cfg)
        return
    typer.echo(cli_t("default_show_help"))
    raise typer.Exit(0)


run_app = typer.Typer(help=cli_t("run_help"), no_args_is_help=False, invoke_without_command=True)


def _resolve_run_target_from_config(config: dict) -> str:
    """
    从配置文件中解析 run 目标：仅读取 service.run（serve | telegram | discord），
    未配置或无效时返回空字符串（表示需引导或默认 serve）。
    """
    svc = (config.get("service") or {})
    run = (svc.get("run") or "").strip().lower()
    if run in ("serve", "telegram", "discord"):
        return run
    return ""


def _prompt_run_target(config: dict) -> str:
    """
    交互式引导用户选择启动目标（serve / telegram / discord），可选写入 service.run。
    非交互环境直接返回 serve。
    """
    if not _is_interactive():
        return "serve"
    typer.echo("")
    typer.echo(cli_t("run_prompt_target"))
    try:
        raw = input(cli_t("run_prompt_target_prompt")).strip()
        if raw == "1":
            choice = "serve"
        elif raw == "2":
            choice = "telegram"
        elif raw == "3":
            choice = "discord"
        else:
            choice = "serve"
        config.setdefault("service", {})["run"] = choice
        get_config_path().parent.mkdir(parents=True, exist_ok=True)
        save_config(config)
        return choice
    except (EOFError, KeyboardInterrupt):
        return "serve"


@run_app.callback()
def _run_default(
    ctx: typer.Context,
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", path_type=Path, help=cli_t("opt_config")),
) -> None:
    if config_path is not None:
        os.environ["OPENAB_CONFIG"] = str(config_path.expanduser().resolve())
    if ctx.invoked_subcommand is not None:
        return
    cfg = load_config()
    target = _resolve_run_target_from_config(cfg)
    if not target and _is_interactive():
        target = _prompt_run_target(cfg)
    if not target:
        target = "serve"
    if target == "serve":
        if _config_empty(cfg):
            typer.echo(cli_t("default_no_config_run_serve"))
        _do_serve()
        return
    if target == "telegram":
        _echo_config_file_path()
        # 复用 run_telegram 逻辑，但不通过 typer 传参
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        cfg = _ensure_agent_backend(cfg)
        t, allowed, cfg = _ensure_telegram_run_config(cfg, None)
        ws = _get_workspace(cfg, None)
        timeout = (cfg.get("agent") or {}).get("timeout")
        timeout = int(timeout) if timeout is not None else 300
        allow_all = (cfg.get("telegram") or {}).get("allow_all") is True
        if not allowed and not allow_all:
            typer.echo(cli_t("allowlist_empty_warning"), err=True)
        if allow_all:
            _echo_severe_warning(cli_t("allow_all_severe_warning"))
        typer.echo(cli_t("starting"))
        run_telegram_bot(
            t,
            workspace=ws,
            timeout=timeout,
            allowed_user_ids=allowed,
            allow_all=allow_all,
            config_path=get_config_file_path(),
            agent_config=cfg,
        )
        return
    if target == "discord":
        _echo_config_file_path()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        cfg = _ensure_agent_backend(cfg)
        t, allowed, cfg = _ensure_discord_run_config(cfg, None)
        ws = _get_workspace(cfg, None)
        timeout = (cfg.get("agent") or {}).get("timeout")
        timeout = int(timeout) if timeout is not None else 300
        allow_all = (cfg.get("discord") or {}).get("allow_all") is True
        if not allowed and not allow_all:
            typer.echo(cli_t("allowlist_empty_warning"), err=True)
        if allow_all:
            _echo_severe_warning(cli_t("allow_all_severe_warning"))
        typer.echo(cli_t("starting_discord"))
        run_discord_bot(
            t,
            workspace=ws,
            timeout=timeout,
            allowed_user_ids=allowed,
            allow_all=allow_all,
            config_path=get_config_file_path(),
            agent_config=cfg,
        )
        return
    typer.echo(cli_t("default_show_help_run"))
    raise typer.Exit(0)


@run_app.command("serve", help=cli_t("run_serve_help"))
def run_serve(
    host: Optional[str] = typer.Option(None, "--host", "-H", help=cli_t("serve_opt_host")),
    port: Optional[int] = typer.Option(None, "--port", "-p", help=cli_t("serve_opt_port")),
    token: Optional[str] = typer.Option(None, "--token", "-t", help=cli_t("serve_opt_token")),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", path_type=Path, help=cli_t("opt_config")),
) -> None:
    """Start OpenAI API compatible HTTP server (POST /v1/chat/completions, GET /v1/models)."""
    if config_path is not None:
        os.environ["OPENAB_CONFIG"] = str(config_path.expanduser().resolve())
    _do_serve(host=host, port=port, token=token)


@run_app.command("telegram", help=cli_t("run_telegram_help"))
def run_telegram(
    token: Optional[str] = typer.Option(None, "--token", "-t", help=cli_t("opt_token")),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help=cli_t("opt_workspace")),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=cli_t("opt_verbose")),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", path_type=Path, help=cli_t("opt_config")),
) -> None:
    """Run Telegram bot (long polling)."""
    if config_path is not None:
        os.environ["OPENAB_CONFIG"] = str(config_path.expanduser().resolve())
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    config = load_config()
    _echo_config_file_path()
    config = _ensure_agent_backend(config)
    t, allowed, config = _ensure_telegram_run_config(config, token)
    ws = _get_workspace(config, workspace)
    timeout = (config.get("agent") or {}).get("timeout")
    timeout = int(timeout) if timeout is not None else 300
    allow_all = (config.get("telegram") or {}).get("allow_all") is True
    if not allowed and not allow_all:
        typer.echo(cli_t("allowlist_empty_warning"), err=True)
    if allow_all:
        _echo_severe_warning(cli_t("allow_all_severe_warning"))
    typer.echo(cli_t("starting"))
    run_telegram_bot(
        t,
        workspace=ws,
        timeout=timeout,
        allowed_user_ids=allowed,
        allow_all=allow_all,
        config_path=get_config_file_path(),
        agent_config=config,
    )


@run_app.command("discord", help=cli_t("run_discord_help"))
def run_discord(
    token: Optional[str] = typer.Option(None, "--token", "-t", help=cli_t("opt_token_discord")),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help=cli_t("opt_workspace")),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=cli_t("opt_verbose")),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", path_type=Path, help=cli_t("opt_config")),
) -> None:
    """Run Discord bot."""
    if config_path is not None:
        os.environ["OPENAB_CONFIG"] = str(config_path.expanduser().resolve())
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    config = load_config()
    _echo_config_file_path()
    config = _ensure_agent_backend(config)
    t, allowed, config = _ensure_discord_run_config(config, token)
    ws = _get_workspace(config, workspace)
    timeout = (config.get("agent") or {}).get("timeout")
    timeout = int(timeout) if timeout is not None else 300
    allow_all = (config.get("discord") or {}).get("allow_all") is True
    if not allowed and not allow_all:
        typer.echo(cli_t("allowlist_empty_warning"), err=True)
    if allow_all:
        _echo_severe_warning(cli_t("allow_all_severe_warning"))
    typer.echo(cli_t("starting_discord"))
    run_discord_bot(
        t,
        workspace=ws,
        timeout=timeout,
        allowed_user_ids=allowed,
        allow_all=allow_all,
        config_path=get_config_file_path(),
        agent_config=config,
    )


app.add_typer(run_app, name="run")


config_app = typer.Typer(help="Read or write config file (YAML/JSON).")
app.add_typer(config_app, name="config")


@config_app.callback()
def config_callback(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(None, "--config", "-c", path_type=Path, help="Config file path (default: OPENAB_CONFIG or ~/.config/openab/config.yaml)."),
) -> None:
    """Optional config file for this invocation."""
    ctx.obj = ctx.obj or {}
    ctx.obj["config_file"] = config.expanduser().resolve() if config else None


def _config_file_from_ctx(ctx: typer.Context) -> Path | None:
    """从 config 子命令的 context 取可选配置文件（父级 config 的 -c 或全局 --config 已写入 OPENAB_CONFIG）。"""
    if ctx.parent and ctx.parent.obj:
        return ctx.parent.obj.get("config_file")
    return None


@config_app.command("path")
def config_path_cmd(ctx: typer.Context) -> None:
    """Print config file path (current or default)."""
    cf = _config_file_from_ctx(ctx)
    path = cf if cf else get_config_file_path()
    typer.echo(str(path))


@config_app.command("get")
def config_get(
    ctx: typer.Context,
    key: Optional[str] = typer.Argument(None, help="Dot key, e.g. agent.backend (omit to show all)."),
) -> None:
    """Show config or value at key."""
    cf = _config_file_from_ctx(ctx)
    cfg = load_config(cf)
    if not key:
        import json
        typer.echo(json.dumps(cfg, indent=2, ensure_ascii=False))
        return
    val = _get_nested(cfg, key)
    if val is None:
        raise typer.Exit(1)
    if isinstance(val, (list, dict)):
        import json
        typer.echo(json.dumps(val, indent=2, ensure_ascii=False))
    else:
        typer.echo(val)


@config_app.command("set")
def config_set(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Dot key, e.g. agent.backend, telegram.allowed_user_ids"),
    value: str = typer.Argument(..., help="Value (use comma for list IDs)."),
) -> None:
    """Set config key and save to file."""
    cf = _config_file_from_ctx(ctx)
    path = cf if cf else get_config_file_path()
    cfg = load_config(cf)
    coerced = coerce_config_value(key, value)
    _set_nested(cfg, key, coerced)
    saved = save_config(cfg, path)
    typer.echo(f"Saved to {saved}")


@app.command("config-path")
def config_path_legacy() -> None:
    """Print default config file path (deprecated: use 'openab config path')."""
    p = get_config_path()
    typer.echo(str(p))


allowlist_app = typer.Typer(help=cli_t("allowlist_add_help"))
app.add_typer(allowlist_app, name="allowlist")


@allowlist_app.command("add")
def allowlist_add(
    user_id: int = typer.Argument(..., help="User ID to add (Telegram or Discord numeric ID)."),
    discord: bool = typer.Option(False, "--discord", help="Add to Discord allowlist (default: Telegram)."),
) -> None:
    """Add a user ID to the allowlist and save config."""
    cfg = load_config()
    key = "discord.allowed_user_ids" if discord else "telegram.allowed_user_ids"
    current = parse_allowed_user_ids(_get_nested(cfg, key))
    if user_id in current:
        typer.echo(f"{user_id} already in allowlist.", err=True)
        raise typer.Exit(0)
    new_list = list(current) + [user_id]
    _set_nested(cfg, key, new_list)
    save_config(cfg)
    platform = "Discord" if discord else "Telegram"
    typer.echo(cli_t("allowlist_add_done", user_id=user_id, platform=platform))


def _install_choice_when_has_config() -> tuple[bool, bool, bool]:
    """
    以配置文件为主导：仅让用户选择要安装的服务（主服务 / Discord 专用 / 两者）及是否立即启动。
    调用前需已确认配置文件存在。
    返回 (install_main, install_discord, start_now)。
    """
    config_path = get_config_file_path()
    typer.echo("")
    typer.echo(cli_t("install_config_used_choose", path=str(config_path)))
    try:
        choice = input(cli_t("install_wizard_which_prompt")).strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"
    install_main = choice in ("1", "3")
    install_discord = choice in ("2", "3")
    if not install_main and not install_discord:
        install_main = True

    start_now = False
    try:
        ans = input(cli_t("install_wizard_start_now")).strip().lower()
        start_now = ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        pass
    return install_main, install_discord, start_now


@app.command("install-service", help=cli_t("install_service_help"))
def install_service(
    discord: bool = typer.Option(False, "--discord", help="Install Discord bot service (openab-discord.service) instead of Telegram."),
    start: bool = typer.Option(False, "--start", help="Start the service immediately after enable."),
    no_interactive: bool = typer.Option(False, "--no-interactive", help=cli_t("install_wizard_skip_interactive")),
) -> None:
    """Install OpenAB as a user-level systemd service (Linux only)."""
    try:
        from openab.cli.service_linux import install_user_service

        config_path = get_config_file_path()
        if no_interactive:
            install_telegram = not discord
            install_discord = discord
            start_now = start
            if (install_telegram or install_discord) and not config_path.is_file():
                typer.echo(cli_t("install_config_not_found"), err=True)
                raise typer.Exit(1)
        else:
            if not config_path.is_file():
                typer.echo(cli_t("install_config_not_found"), err=True)
                raise typer.Exit(1)
            install_telegram, install_discord, start_now = _install_choice_when_has_config()

        if install_telegram:
            typer.echo(cli_t("install_wizard_installing_telegram"))
            path = install_user_service(config_path=config_path, discord=False, start=start_now)
            typer.echo(cli_t("install_service_done", path=path))
        if install_discord:
            typer.echo(cli_t("install_wizard_installing_discord"))
            path = install_user_service(config_path=config_path, discord=True, start=start_now)
            typer.echo(cli_t("install_service_done_discord", path=path))
        if not install_telegram and not install_discord:
            typer.echo(cli_t("install_service_linux_only"), err=True)
            raise typer.Exit(1)
        typer.echo(cli_t("install_wizard_done"))
    except RuntimeError as e:
        if "only supported on Linux" in str(e):
            typer.echo(cli_t("install_service_linux_only"), err=True)
            if sys.platform == "darwin":
                typer.echo(cli_t("install_service_mac_hint"), err=True)
        else:
            typer.echo(str(e), err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"systemctl failed: {e}", err=True)
        raise typer.Exit(1)


@app.command("restart-service", help=cli_t("restart_service_help"))
def restart_service(
    discord: bool = typer.Option(False, "--discord", help="Only restart openab-discord.service."),
    main_only: bool = typer.Option(False, "--main", help="Only restart openab.service (main service)."),
) -> None:
    """Restart installed user-level systemd service(s) (Linux only)."""
    try:
        from openab.cli.service_linux import restart_user_services
    except ImportError:
        typer.echo(cli_t("install_service_linux_only"), err=True)
        raise typer.Exit(1)
    try:
        if discord:
            restarted = restart_user_services(discord=True)
        elif main_only:
            restarted = restart_user_services(discord=False)
        else:
            restarted = restart_user_services(all_services=True)
    except RuntimeError as e:
        if "only supported on Linux" in str(e):
            typer.echo(cli_t("install_service_linux_only"), err=True)
        else:
            typer.echo(str(e), err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"systemctl failed: {e}", err=True)
        raise typer.Exit(1)
    if restarted:
        typer.echo(cli_t("restart_service_done", names=", ".join(restarted)))
    else:
        typer.echo(cli_t("restart_service_none"))


@app.command("uninstall-service", help=cli_t("uninstall_service_help"))
def uninstall_service(
    discord: bool = typer.Option(False, "--discord", help="Only remove openab-discord.service."),
    main_only: bool = typer.Option(False, "--main", help="Only remove openab.service (main service)."),
    remove_config: bool = typer.Option(False, "--config", "-c", help="Also delete the config file (e.g. ~/.config/openab/config.yaml)."),
) -> None:
    """Uninstall user-level systemd service(s) and optionally remove config file (Linux only)."""
    try:
        from openab.cli.service_linux import uninstall_user_services
    except ImportError:
        typer.echo(cli_t("install_service_linux_only"), err=True)
        raise typer.Exit(1)
    try:
        if discord:
            removed = uninstall_user_services(discord=True)
        elif main_only:
            removed = uninstall_user_services(discord=False)
        else:
            removed = uninstall_user_services(all_services=True)
    except RuntimeError as e:
        if "only supported on Linux" in str(e):
            typer.echo(cli_t("install_service_linux_only"), err=True)
        else:
            typer.echo(str(e), err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"systemctl failed: {e}", err=True)
        raise typer.Exit(1)

    if removed:
        typer.echo(cli_t("uninstall_service_done", paths=", ".join(removed)))
    else:
        typer.echo(cli_t("uninstall_service_none"))

    if remove_config:
        config_path = get_config_file_path()
        if config_path.is_file():
            config_path.unlink()
            typer.echo(cli_t("uninstall_config_done", path=str(config_path)))
        else:
            typer.echo(cli_t("uninstall_config_none"))
