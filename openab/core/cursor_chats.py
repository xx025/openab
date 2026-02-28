"""从 Cursor 本地 chats 目录读取会话列表，供 Telegram/Discord 展示为可点击按钮。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Tuple

# 默认 Cursor 数据目录
_CURSOR_HOME = Path.home() / ".cursor"
_CHATS_DIR = _CURSOR_HOME / "chats"

# 每个会话的 store.db 里 meta 表的 value 可能是 JSON 或 hex 编码的 JSON
def _read_session_name(store_path: Path) -> str | None:
    try:
        conn = sqlite3.connect(store_path)
        row = conn.execute("SELECT value FROM meta LIMIT 1").fetchone()
        conn.close()
        if not row:
            return None
        raw = row[0]
        if not isinstance(raw, str):
            return None
        # 先尝试直接 JSON 解析
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # 再尝试 hex 解码（Cursor 可能存的是 hex 编码的 JSON）
            if len(raw) % 2 == 0 and all(c in "0123456789abcdef" for c in raw.lower()):
                try:
                    raw = bytes.fromhex(raw).decode("utf-8")
                    data = json.loads(raw)
                except Exception:
                    return None
            else:
                return None
        if isinstance(data, dict) and "name" in data:
            return str(data["name"]).strip() or None
    except Exception:
        pass
    return None


def list_cursor_sessions(
    max_sessions: int = 15,
    chats_dir: Path | None = None,
) -> List[Tuple[str, str]]:
    """
    扫描 ~/.cursor/chats 下的会话，返回 [(session_id, display_name), ...] 按目录 mtime 倒序。
    session_id 即 --resume <id> 用的 ID；display_name 来自 store.db meta（如 "New Agent"），
    无则用 session_id 前 8 位。
    """
    base = chats_dir or _CHATS_DIR
    if not base.is_dir():
        return []
    # session_id 可能出现在多个 project 下，按 session_id 去重，保留 mtime 最新的一条
    seen: dict[str, Tuple[str, float]] = {}
    for project_dir in base.iterdir():
        if not project_dir.is_dir():
            continue
        for session_dir in project_dir.iterdir():
            if not session_dir.is_dir():
                continue
            session_id = session_dir.name
            if len(session_id) != 36 or session_id.count("-") != 4:
                continue
            store = session_dir / "store.db"
            if not store.is_file():
                continue
            name = _read_session_name(store)
            display = (name or session_id[:8]).strip()
            if len(display) > 32:
                display = display[:29] + "..."
            try:
                mtime = store.stat().st_mtime
            except OSError:
                mtime = 0
            if session_id not in seen or mtime > seen[session_id][1]:
                seen[session_id] = (display, mtime)
    out = [(sid, disp, mt) for sid, (disp, mt) in seen.items()]
    out.sort(key=lambda x: x[2], reverse=True)
    return [(sid, disp) for sid, disp, _ in out[:max_sessions]]


def set_cursor_chats_dir(path: Path | None) -> None:
    """测试或覆盖 chats 目录。"""
    global _CHATS_DIR
    if path is not None:
        _CHATS_DIR = Path(path)
    else:
        _CHATS_DIR = Path.home() / ".cursor" / "chats"
