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


def _use_continue_session(agent_config: dict[str, Any] | None) -> bool:
    """是否使用 --continue 延续上一会话。默认 True。配置 cursor.continue_session 或环境变量 CURSOR_AGENT_CONTINUE 可覆盖。"""
    if agent_config:
        c = agent_config.get("cursor") or {}
        if "continue_session" in c:
            return bool(c["continue_session"])
    env = os.environ.get("CURSOR_AGENT_CONTINUE", "").strip().lower()
    if env in ("0", "false", "no"):
        return False
    if env in ("1", "true", "yes"):
        return True
    return True  # 默认延续上一会话


def _cursor_session_override(agent_config: dict[str, Any] | None) -> tuple[bool, Optional[str]]:
    """
    单次调用的会话覆盖（由 Telegram/Discord 传入）。
    返回 (use_new_session, resume_chat_id)。
    use_new_session=True 表示本次不传 --continue 且不传 --resume（新会话）。
    resume_chat_id 非空表示本次传 --resume <id>。
    """
    if not agent_config:
        return (False, None)
    new = agent_config.get("_cursor_session_new")
    if new is True:
        return (True, None)
    rid = agent_config.get("_cursor_resume_id")
    if rid is not None and str(rid).strip():
        return (False, str(rid).strip())
    return (False, None)


async def run_async(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: int = 300,
    lang: str = "en",
    agent_config: Optional[dict[str, Any]] = None,
) -> str:
    """Cursor Agent CLI: agent --print --trust；可选 --continue / --resume <id>。"""
    cmd = _find_cmd(agent_config)
    base_args = [
        cmd,
        "agent",
        "--print",
        "--output-format", "text",
        "--trust",
    ]
    use_new, resume_id = _cursor_session_override(agent_config)
    if use_new:
        pass  # 不传 --continue 也不传 --resume，即新会话
    elif resume_id:
        base_args.extend(["--resume", resume_id])
    elif _use_continue_session(agent_config):
        base_args.append("--continue")
    if workspace is not None:
        base_args.extend(["--workspace", str(workspace)])
    base_args.extend(["--", prompt])
    env = os.environ.copy()
    # 减少子进程 stdout 缓冲，便于尽早拿到输出（非 TTY 时 Cursor/Node 常为块缓冲）
    env.setdefault("PYTHONUNBUFFERED", "1")
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
