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
    get_config_path,
    load_config,
    parse_allowed_user_ids,
    resolve_workspace,
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


@app.command("config-path")
def config_path() -> None:
    """打印默认配置文件路径（YAML 或 JSON）。"""
    p = get_config_path()
    typer.echo(str(p))
