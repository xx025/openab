"""OpenAB CLI: run, (future: config, agent, chat, …)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from openab.chats.telegram import run_bot
from openab.core.i18n import cli_t

load_dotenv()

app = typer.Typer(
    name="openab",
    help=cli_t("cli_help"),
    no_args_is_help=False,
)


def _get_token(token: Optional[str]) -> str:
    t = token or __import__("os").environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t:
        typer.echo(cli_t("err_no_token"), err=True)
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
    t = _get_token(token)
    typer.echo(cli_t("starting"))
    run_bot(t, workspace=workspace)


# Future CLI commands can be added here, e.g.:
# @app.command("config")
# def config_show() -> None: ...
# @app.command("agent")
# def agent_list() -> None: ...
