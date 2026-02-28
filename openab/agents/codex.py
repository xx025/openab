"""OpenAI Codex CLI backend."""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Optional

from openab.core.i18n import t


def _find_cmd() -> str:
    cmd = os.environ.get("CODEX_CMD", "codex")
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
) -> str:
    """Codex CLI: codex exec --ephemeral, final message on stdout."""
    cmd = _find_cmd()
    args = [cmd, "exec", "--ephemeral"]
    if os.environ.get("CODEX_SKIP_GIT_CHECK", "").strip().lower() in ("1", "true", "yes"):
        args.append("--skip-git-repo-check")
    args.append(prompt)
    cwd = str(workspace) if workspace else None
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env=os.environ.copy(),
        cwd=cwd,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return t(lang, "agent_timeout")
    text = (stdout or b"").decode("utf-8", errors="replace").strip()
    return text or t(lang, "agent_no_output")
