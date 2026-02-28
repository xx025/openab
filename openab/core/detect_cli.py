"""检测用户环境中可用的 agent 后端 CLI 命令，供安装/运行引导使用。"""
from __future__ import annotations

import shutil
from typing import Sequence

# 与 openab.agents 一致的 backend id -> 默认命令名（用于 which 检测）
BACKEND_CLI_NAMES: Sequence[tuple[str, str]] = (
    ("cursor", "agent"),
    ("openclaw", "openclaw"),
    ("claude", "claude"),
    ("gemini", "gemini"),
    ("codex", "codex"),
)


def detect_available_backends() -> list[tuple[str, str]]:
    """
    检测当前 PATH 下存在的 agent 后端命令。
    返回 [(backend_id, 可执行路径或命令名), ...]，按 BACKEND_CLI_NAMES 顺序，仅包含存在的。
    """
    out: list[tuple[str, str]] = []
    for backend_id, cmd_name in BACKEND_CLI_NAMES:
        exe = shutil.which(cmd_name)
        if exe:
            out.append((backend_id, exe))
        else:
            # 仍可被配置为绝对路径使用，这里只报「命令存在」即可
            pass
    return out
