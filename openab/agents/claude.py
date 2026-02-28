"""Claude Code CLI backend (https://code.claude.com/docs/en/cli-reference).

Print mode: claude -p "query" — response to stdout, then exit.
Flags used: --output-format text, --no-session-persistence; optional: --model, --max-turns, --add-dir.
"""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from openab.core.i18n import t


def _find_cmd(agent_config: dict[str, Any] | None = None) -> str:
    cmd = "claude"
    if agent_config:
        c = (agent_config.get("claude") or {}).get("cmd")
        if c:
            cmd = str(c)
    if not cmd:
        cmd = os.environ.get("CLAUDE_CLI_CMD", "claude")
    if os.path.isabs(cmd):
        return cmd
    exe = shutil.which(cmd)
    return exe or cmd


def _build_args(
    prompt: str,
    workspace: Optional[Path],
    agent_config: dict[str, Any] | None = None,
) -> list[str]:
    cmd = _find_cmd(agent_config)
    args = [
        cmd,
        "--print",
        "--output-format", "text",
        "--no-session-persistence",
    ]
    model = ""
    max_turns = ""
    add_dirs: list[str] = []
    if agent_config:
        c = agent_config.get("claude") or {}
        if c.get("model"):
            model = str(c["model"]).strip()
        if c.get("max_turns") is not None:
            max_turns = str(c["max_turns"]).strip()
        ad = c.get("add_dir")
        if isinstance(ad, str) and ad:
            add_dirs = [d.strip() for d in ad.split(os.pathsep) if d.strip()]
        elif isinstance(ad, list):
            add_dirs = [str(x).strip() for x in ad if str(x).strip()]
    if not model:
        model = os.environ.get("CLAUDE_CLI_MODEL", "").strip()
    if not max_turns:
        max_turns = os.environ.get("CLAUDE_CLI_MAX_TURNS", "").strip()
    if not add_dirs:
        raw = os.environ.get("CLAUDE_CLI_ADD_DIR", "").strip()
        if raw:
            add_dirs = [d.strip() for d in raw.split(os.pathsep) if d.strip()]
    if model:
        args.extend(["--model", model])
    if max_turns and max_turns.isdigit():
        args.extend(["--max-turns", max_turns])
    for d in add_dirs:
        args.extend(["--add-dir", d])
    args.append(prompt)
    return args


async def run_async(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: int = 300,
    lang: str = "en",
    agent_config: Optional[dict[str, Any]] = None,
) -> str:
    """Run Claude Code CLI in print mode; return stdout as reply."""
    args = _build_args(prompt, workspace, agent_config)
    cwd = str(workspace) if workspace else None
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
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
