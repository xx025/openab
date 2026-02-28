"""从 Codex 本地 sessions 目录与 history.jsonl 读取会话列表，供 Telegram/Discord 展示为可点击按钮。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

_CODEX_HOME = Path.home() / ".codex"
_SESSIONS_DIR = _CODEX_HOME / "sessions"
_HISTORY_FILE = _CODEX_HOME / "history.jsonl"

# rollout-2026-03-01T04-32-45-019ca5f4-2170-7961-9d0a-24537ec4c29c.jsonl 末尾为 session_id
_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


def _session_id_from_filename(name: str) -> str | None:
    """从 rollout-<date>T<time>-<uuid>.jsonl 中提取 uuid。"""
    base = name.removesuffix(".jsonl")
    m = _UUID_PATTERN.search(base)
    return m.group(0) if m else None


def _display_from_session_file(path: Path) -> str:
    """从 session jsonl 首行 session_meta 或首条用户消息取简短展示名。"""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(data, dict):
                    continue
                typ = data.get("type")
                payload = data.get("payload") or {}
                if typ == "session_meta" and isinstance(payload, dict):
                    ts = payload.get("timestamp") or ""
                    if ts:
                        return ts[:19].replace("T", " ")
                # 可在此解析 response_item role=user 的 content 取首句作展示
                break
    except OSError:
        pass
    return ""


def list_codex_sessions(
    max_sessions: int = 15,
    sessions_dir: Path | None = None,
    history_path: Path | None = None,
) -> List[Tuple[str, str]]:
    """
    先扫描 ~/.codex/sessions/ 下所有 *-<uuid>.jsonl，再合并 history.jsonl 中的会话；
    按 session_id 去重保留最新时间，展示名来自 session 文件或 history 的 text。
    返回 [(session_id, display_name), ...] 按时间倒序。
    """
    base_sessions = sessions_dir or _SESSIONS_DIR
    path_history = history_path or _HISTORY_FILE

    seen: dict[str, Tuple[str, float]] = {}  # session_id -> (display, mtime_or_ts)

    # 1) 扫描 sessions 目录下所有 .jsonl（文件名末尾为 uuid）
    if base_sessions.is_dir():
        try:
            for f in base_sessions.rglob("*.jsonl"):
                if not f.is_file():
                    continue
                sid = _session_id_from_filename(f.name)
                if not sid:
                    continue
                try:
                    mtime = f.stat().st_mtime
                except OSError:
                    mtime = 0
                display = _display_from_session_file(f).strip()
                if not display:
                    display = f.stem.split("-")[-1][:8] if "-" in f.stem else sid[:8]
                if len(display) > 32:
                    display = display[:29] + "..."
                if sid not in seen or mtime > seen[sid][1]:
                    seen[sid] = (display or sid[:8], mtime)
        except OSError:
            pass

    # 2) 合并 history.jsonl（同 session_id 保留 ts 更大的）
    if path_history.is_file():
        try:
            with open(path_history, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(data, dict):
                        continue
                    sid = data.get("session_id")
                    ts = data.get("ts")
                    text = (data.get("text") or "").strip()
                    if not sid or not isinstance(sid, str):
                        continue
                    if len(sid) != 36 or sid.count("-") != 4:
                        continue
                    ts_f = float(ts) if isinstance(ts, (int, float)) else 0
                    display = (text[:32] + "..." if len(text) > 32 else text) or sid[:8]
                    if sid not in seen or ts_f > seen[sid][1]:
                        seen[sid] = (display, ts_f)
        except OSError:
            pass

    out = [(sid, disp) for sid, (disp, mt) in seen.items()]
    out.sort(key=lambda x: seen[x[0]][1], reverse=True)
    return out[:max_sessions]
