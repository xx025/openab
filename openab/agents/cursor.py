"""Cursor Agent CLI backend."""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from openab.core.i18n import t


def _find_cmd(agent_config: dict[str, Any] | None = None) -> str:
    cmd = "agent"
    if agent_config:
        c = (agent_config.get("cursor") or {}).get("cmd")
        if c:
            cmd = str(c)
    if not cmd:
        cmd = os.environ.get("CURSOR_AGENT_CMD", "agent")
    if os.path.isabs(cmd):
        return cmd
    exe = shutil.which(cmd)
    return exe or cmd


async def run_async(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: int = 300,
    lang: str = "en",
    agent_config: Optional[dict[str, Any]] = None,
) -> str:
    """Cursor Agent CLI: agent --print --trust."""
    cmd = _find_cmd(agent_config)
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
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return t(lang, "agent_timeout")
    text = (stdout or b"").decode("utf-8", errors="replace").strip()
    return text or t(lang, "agent_no_output")
