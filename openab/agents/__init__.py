"""Agent backends: Cursor, Codex, Gemini, Claude. Dispatches by OPENAB_AGENT."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional

from openab.core.i18n import t

from . import claude, codex, cursor, gemini


def get_backend() -> str:
    return (os.environ.get("OPENAB_AGENT") or "cursor").strip().lower()


def run_agent(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: Optional[int] = None,
) -> str:
    """同步执行当前配置的 agent，返回完整 stdout 文本。"""
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
    """异步执行当前配置的 agent（OPENAB_AGENT），返回回复文本。"""
    backend = get_backend()
    to = timeout if timeout is not None else int(os.environ.get("OPENAB_AGENT_TIMEOUT", "300"))
    if backend == "codex":
        return await codex.run_async(prompt, workspace=workspace, timeout=to, lang=lang)
    if backend == "gemini":
        return await gemini.run_async(prompt, workspace=workspace, timeout=to, lang=lang)
    if backend == "claude":
        return await claude.run_async(prompt, workspace=workspace, timeout=to, lang=lang)
    return await cursor.run_async(prompt, workspace=workspace, timeout=to, lang=lang)


__all__ = ["run_agent", "run_agent_async", "get_backend"]
