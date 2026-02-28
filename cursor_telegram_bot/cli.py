"""CLI 入口：使用 typer 启动机器人。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from .bot import run_bot

load_dotenv()

cli = typer.Typer(help="Cursor CLI × Telegram 机器人", no_args_is_help=False)


def _get_token(token: Optional[str]) -> str:
    t = token or __import__("os").environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t:
        typer.echo("错误: 请设置 TELEGRAM_BOT_TOKEN 或使用 --token 传入。", err=True)
        raise typer.Exit(1)
    return t


@cli.callback(invoke_without_command=True)
def _default(
    ctx: typer.Context,
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Telegram Bot Token"),
    workspace: Optional[Path] = typer.Option(None, "--workspace", "-w", path_type=Path, help="Cursor Agent 工作目录"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="打印调试日志"),
) -> None:
    if ctx.invoked_subcommand is None:
        ctx.invoke(run, token=token, workspace=workspace, verbose=verbose)


@cli.command("run")
def run(
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Telegram Bot Token"),
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace", "-w",
        path_type=Path,
        help="Cursor Agent 工作目录",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="打印调试日志"),
) -> None:
    """启动机器人（长轮询）。"""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    t = _get_token(token)
    typer.echo("正在启动 Cursor × Telegram 机器人（长轮询）…")
    run_bot(t, workspace=workspace)


if __name__ == "__main__":
    cli()
