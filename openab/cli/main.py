"""OpenAB CLI：以 Typer + Path 传参为主，配置来自用户目录 YAML/JSON；仅全局配置路径用环境变量 OPENAB_CONFIG。"""
from __future__ import annotations

import logging
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
from openab.core.i18n import cli_t

load_dotenv()

app = typer.Typer(
    name="openab",
    help=cli_t("cli_help"),
    no_args_is_help=False,
)


def _get_workspace(config: dict, workspace: Optional[Path]) -> Path:
    return resolve_workspace(config, workspace)


def _get_telegram_token(config: dict, token: Optional[str]) -> str:
    t = (token or "").strip() or (config.get("telegram") or {}).get("bot_token") or ""
    t = (t or "").strip()
    if not t:
        typer.echo(cli_t("err_no_token"), err=True)
        raise typer.Exit(1)
    return t


def _get_discord_token(config: dict, token: Optional[str]) -> str:
    t = (token or "").strip() or (config.get("discord") or {}).get("bot_token") or ""
    t = (t or "").strip()
    if not t:
        typer.echo(cli_t("err_no_token_discord"), err=True)
        raise typer.Exit(1)
    return t


@app.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    token: Optional[str] = typer.Option(None, "--token", "-t", help=cli_t("opt_token")),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help=cli_t("opt_workspace")),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=cli_t("opt_verbose")),
) -> None:
    if ctx.invoked_subcommand is None:
        ctx.invoke(run, token=token, workspace=workspace, verbose=verbose)


@app.command("run", help=cli_t("run_help"))
def run(
    token: Optional[str] = typer.Option(None, "--token", "-t", help=cli_t("opt_token")),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help=cli_t("opt_workspace")),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=cli_t("opt_verbose")),
) -> None:
    """Run Telegram bot (long polling)."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    config = load_config()
    t = _get_telegram_token(config, token)
    ws = _get_workspace(config, workspace)
    allowed = parse_allowed_user_ids((config.get("telegram") or {}).get("allowed_user_ids"))
    timeout = (config.get("agent") or {}).get("timeout")
    timeout = int(timeout) if timeout is not None else 300
    typer.echo(cli_t("starting"))
    run_telegram_bot(
        t,
        workspace=ws,
        timeout=timeout,
        allowed_user_ids=allowed,
        agent_config=config,
    )


@app.command("run-discord", help=cli_t("run_discord_help"))
def run_discord(
    token: Optional[str] = typer.Option(None, "--token", "-t", help=cli_t("opt_token_discord")),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help=cli_t("opt_workspace")),
    verbose: bool = typer.Option(False, "--verbose", "-v", help=cli_t("opt_verbose")),
) -> None:
    """Run Discord bot."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    config = load_config()
    t = _get_discord_token(config, token)
    ws = _get_workspace(config, workspace)
    allowed = parse_allowed_user_ids((config.get("discord") or {}).get("allowed_user_ids"))
    timeout = (config.get("agent") or {}).get("timeout")
    timeout = int(timeout) if timeout is not None else 300
    typer.echo(cli_t("starting_discord"))
    run_discord_bot(
        t,
        workspace=ws,
        timeout=timeout,
        allowed_user_ids=allowed,
        agent_config=config,
    )


config_app = typer.Typer(help="Read or write config file (YAML/JSON).")
app.add_typer(config_app, name="config")


@config_app.command("path")
def config_path_cmd() -> None:
    """Print config file path (current or default)."""
    typer.echo(str(get_config_file_path()))


@config_app.command("get")
def config_get(key: Optional[str] = typer.Argument(None, help="Dot key, e.g. agent.backend (omit to show all).")) -> None:
    """Show config or value at key."""
    cfg = load_config()
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
    key: str = typer.Argument(..., help="Dot key, e.g. agent.backend, telegram.allowed_user_ids"),
    value: str = typer.Argument(..., help="Value (use comma for list IDs)."),
) -> None:
    """Set config key and save to file."""
    path = get_config_file_path()
    cfg = load_config()
    coerced = coerce_config_value(key, value)
    _set_nested(cfg, key, coerced)
    saved = save_config(cfg, path)
    typer.echo(f"Saved to {saved}")


@app.command("config-path")
def config_path_legacy() -> None:
    """Print default config file path (deprecated: use 'openab config path')."""
    p = get_config_path()
    typer.echo(str(p))
