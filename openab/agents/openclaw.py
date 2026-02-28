"""OpenClaw 后端：通过 CLI `openclaw agent --message "..."` 调用，需先运行 OpenClaw Gateway（或使用本地回退）。

参考：https://docs.openclaw.ai/tools/agent-send
安装：npm install -g openclaw@latest，并运行 openclaw onboard / openclaw gateway。
"""
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from openab.core.i18n import t


def _find_cmd(agent_config: dict[str, Any] | None = None) -> str:
    cmd = "openclaw"
    if agent_config:
        c = (agent_config.get("openclaw") or {}).get("cmd")
        if c:
            cmd = str(c)
    if not cmd:
        cmd = os.environ.get("OPENCLAW_CMD", "openclaw")
    if os.path.isabs(cmd):
        return cmd
    exe = shutil.which(cmd)
    return exe or cmd


def _strip_media_lines(text: str) -> str:
    """去掉 OpenClaw 输出中的 MEDIA: 行，只保留回复正文。"""
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("MEDIA:"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


async def run_async(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: int = 300,
    lang: str = "en",
    agent_config: Optional[dict[str, Any]] = None,
) -> str:
    """调用 openclaw agent --message \"<prompt>\"，从 stdout 取回复；默认会过滤 MEDIA: 行。"""
    cmd = _find_cmd(agent_config)
    args = [cmd, "agent", "--message", prompt]
    oc_cfg = (agent_config or {}).get("openclaw") or {}
    to = oc_cfg.get("timeout") or timeout
    if to and int(to) > 0:
        args.extend(["--timeout", str(int(to))])
    thinking = (oc_cfg.get("thinking") or "").strip().lower()
    if thinking in ("off", "minimal", "low", "medium", "high", "xhigh"):
        args.extend(["--thinking", thinking])
    cwd = str(workspace) if workspace else None
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy(),
        cwd=cwd,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return t(lang, "agent_timeout")
    text = (stdout or b"").decode("utf-8", errors="replace")
    text = _strip_media_lines(text)
    if not text.strip():
        return t(lang, "agent_no_output")
    return text
