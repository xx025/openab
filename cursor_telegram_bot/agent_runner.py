"""在子进程中调用 Cursor Agent CLI，并捕获标准输出。"""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Optional

from .i18n import t


def _find_agent_cmd() -> str:
    cmd = os.environ.get("CURSOR_AGENT_CMD", "agent")
    if os.path.isabs(cmd):
        return cmd
    exe = shutil.which(cmd)
    return exe or cmd


def run_agent(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: Optional[int] = None,
) -> str:
    """
    同步执行 agent --print，将 prompt 传入，返回完整 stdout 文本。
    """
    return asyncio.get_event_loop().run_until_complete(
        run_agent_async(prompt, workspace=workspace, timeout=timeout)
    )


async def run_agent_async(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: Optional[int] = 300,
    lang: str = "en",
) -> str:
    """
    异步执行 agent --print，便于在 Telegram 机器人中配合 typing 使用。
    """
    cmd = _find_agent_cmd()
    base_args = [
        cmd,
        "agent",
        "--print",
        "--output-format", "text",
        "--trust",
    ]
    if workspace is not None:
        base_args.extend(["--workspace", str(workspace)])
    base_args.extend(["--", prompt])

    env = os.environ.copy()
    proc = await asyncio.create_subprocess_exec(
        *base_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
        cwd=str(workspace) if workspace else None,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout or 300)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return t(lang, "agent_timeout")
    text = (stdout or b"").decode("utf-8", errors="replace").strip()
    return text or t(lang, "agent_no_output")
