"""Agent backends: Cursor, Codex, Gemini, Claude, OpenClaw. 由 agent_config 或环境变量指定后端与选项。"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Optional

from openab.core.i18n import t

from . import claude, codex, cursor, gemini, openclaw


def get_backend(agent_config: dict[str, Any] | None = None) -> str:
    if agent_config:
        agent = agent_config.get("agent") or {}
        b = agent.get("backend") or "cursor"
        return str(b).strip().lower()
    return (os.environ.get("OPENAB_AGENT") or "cursor").strip().lower()


def run_agent(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: Optional[int] = None,
    agent_config: Optional[dict[str, Any]] = None,
) -> str:
    """同步执行当前配置的 agent，返回完整 stdout 文本。"""
    return asyncio.get_event_loop().run_until_complete(
        run_agent_async(
            prompt,
            workspace=workspace,
            timeout=timeout,
            agent_config=agent_config,
        )
    )


async def run_agent_async(
    prompt: str,
    *,
    workspace: Optional[Path] = None,
    timeout: int = 300,
    lang: str = "en",
    agent_config: Optional[dict[str, Any]] = None,
) -> str:
    """异步执行 agent；backend 与各后端选项来自 agent_config，缺省时回退到环境变量。"""
    backend = get_backend(agent_config)
    if backend == "codex":
        return await codex.run_async(
            prompt, workspace=workspace, timeout=timeout, lang=lang, agent_config=agent_config
        )
    if backend == "gemini":
        return await gemini.run_async(
            prompt, workspace=workspace, timeout=timeout, lang=lang, agent_config=agent_config
        )
    if backend == "claude":
        return await claude.run_async(
            prompt, workspace=workspace, timeout=timeout, lang=lang, agent_config=agent_config
        )
    if backend == "openclaw":
        return await openclaw.run_async(
            prompt, workspace=workspace, timeout=timeout, lang=lang, agent_config=agent_config
        )
    return await cursor.run_async(
        prompt, workspace=workspace, timeout=timeout, lang=lang, agent_config=agent_config
    )


__all__ = ["run_agent", "run_agent_async", "get_backend"]
