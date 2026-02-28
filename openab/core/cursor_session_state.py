"""Per-user Cursor 会话状态：创建新会话（下次调用不 --continue）、或切换到指定 --resume id。供 Telegram/Discord 共用。"""
from __future__ import annotations

import threading
from typing import Optional

# key: "tg:{chat_id}:{user_id}" 或 "dc:{channel_id}:{user_id}"
# value: {"new_next": bool, "resume_id": Optional[str]}
_state: dict[str, dict] = {}
_lock = threading.Lock()


def _key(platform: str, chat_or_channel_id: int, user_id: int) -> str:
    return f"{platform}:{chat_or_channel_id}:{user_id}"


def set_new_session_next(platform: str, chat_or_channel_id: int, user_id: int) -> None:
    """标记该用户下一次调用 agent 时使用新会话（不传 --continue）。"""
    with _lock:
        k = _key(platform, chat_or_channel_id, user_id)
        _state.setdefault(k, {})["new_next"] = True
        _state[k]["resume_id"] = None


def set_resume_id(platform: str, chat_or_channel_id: int, user_id: int, chat_id: Optional[str]) -> None:
    """设置该用户后续调用 agent 时使用 --resume <chat_id>。chat_id 为空则恢复“延续上一会话”默认行为。"""
    with _lock:
        k = _key(platform, chat_or_channel_id, user_id)
        if k not in _state:
            _state[k] = {}
        _state[k]["new_next"] = False
        _state[k]["resume_id"] = (chat_id or "").strip() or None


def get_session_override(
    platform: str, chat_or_channel_id: int, user_id: int
) -> tuple[bool, Optional[str]]:
    """
    取回本次调用的会话覆盖；(use_new_session, resume_id)。
    use_new_session 为 True 时仅生效一次（随后清除）；resume_id 持久生效直到用户 /new 或 /resume 其他。
    """
    with _lock:
        k = _key(platform, chat_or_channel_id, user_id)
        entry = _state.get(k)
        if not entry:
            return (False, None)
        new_next = entry.pop("new_next", False)  # 一次性，取完即清
        resume_id = entry.get("resume_id")
        return (bool(new_next), resume_id if (resume_id and str(resume_id).strip()) else None)


def build_agent_config_with_session(
    base_agent_config: dict,
    platform: str,
    chat_or_channel_id: int,
    user_id: int,
) -> dict:
    """
    根据当前用户会话状态，在 base 配置上叠加会话覆盖（新会话 / 指定 resume id）。
    同时写入通用 _session_new / _resume_id（供 Codex 等）与 _cursor_*（兼容 Cursor）。
    并清除“新会话”一次性标记。返回新 dict，不修改 base。
    """
    use_new, resume_id = get_session_override(platform, chat_or_channel_id, user_id)
    out = dict(base_agent_config) if base_agent_config else {}
    if use_new:
        out["_session_new"] = True
        out["_cursor_session_new"] = True
    if resume_id:
        out["_resume_id"] = resume_id
        out["_cursor_resume_id"] = resume_id
    return out
