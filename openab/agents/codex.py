"""OpenAI Codex CLI backend."""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

from openab.core.i18n import t


def _find_cmd(agent_config: dict[str, Any] | None = None) -> str:
    cmd = "codex"
    if agent_config:
        c = (agent_config.get("codex") or {}).get("cmd")
        if c:
            cmd = str(c)
    if not cmd:
        cmd = os.environ.get("CODEX_CMD", "codex")
    if os.path.isabs(cmd):
        return cmd
    exe = shutil.which(cmd)
    return exe or cmd


def _skip_git_check(agent_config: dict[str, Any] | None = None) -> bool:
    """默认 True：在 OpenAB 中通常不在 Git 仓库内执行，不传则 codex 会直接退出且无 stdout。"""
    if agent_config:
        v = (agent_config.get("codex") or {}).get("skip_git_check")
        if v in (False, "false", "0", 0):
            return False
        if v in (True, "true", "1", 1):
            return True
    return os.environ.get("CODEX_SKIP_GIT_CHECK", "").strip().lower() not in ("0", "false", "no")


def _use_continue_session(agent_config: dict[str, Any] | None = None) -> bool:
    """是否默认延续上一会话（exec resume --last）。默认 True。配置 codex.continue_session 可覆盖。"""
    if agent_config:
        c = (agent_config.get("codex") or {}).get("continue_session")
        if c is not None:
            return bool(c)
    return os.environ.get("CODEX_CONTINUE_SESSION", "").strip().lower() not in ("0", "false", "no")


def _codex_session_override(agent_config: dict[str, Any] | None) -> tuple[bool, Optional[str]]:
    """
    单次调用的会话覆盖。返回 (use_new_session, resume_id)。
    use_new_session=True 表示本次新会话（exec 不带 resume）；resume_id 非空表示 exec resume <id>。
    """
    if not agent_config:
        return (False, None)
    if agent_config.get("_session_new") is True:
        return (True, None)
    rid = agent_config.get("_resume_id")
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
    """
    Codex CLI：默认延续上一会话（exec resume --last）；
    支持 _session_new（新会话）与 _resume_id（指定会话）。最终回复在 stdout。
    """
    cmd = _find_cmd(agent_config)
    use_new, resume_id = _codex_session_override(agent_config)
    skip_git = _skip_git_check(agent_config)

    if use_new:
        args = [cmd, "exec"]
    elif resume_id:
        args = [cmd, "exec", "resume", resume_id]
    elif _use_continue_session(agent_config):
        args = [cmd, "exec", "resume", "--last"]
    else:
        args = [cmd, "exec"]

    if skip_git:
        args.append("--skip-git-repo-check")
    # 仅 exec（新会话）支持 --cd；exec resume 子命令不支持 --cd，传了会报错退出。resume 时用 subprocess cwd 控制工作目录。
    if workspace is not None and use_new:
        args.extend(["--cd", str(workspace)])

    # 用 -o 把最终回复写入临时文件，避免依赖 stdout/stderr（非 TTY 下 Codex 可能不往 stdout 打）
    out_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    out_path = out_file.name
    out_file.close()
    args.extend(["--output-last-message", out_path])
    args.append(prompt)

    cwd = str(workspace) if workspace else None
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            env=os.environ.copy(),
            cwd=cwd,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return t(lang, "agent_timeout")
        try:
            text = Path(out_path).read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            text = ""
        return text or t(lang, "agent_no_output")
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass
