"""从用户目录加载 YAML/JSON 配置文件；仅全局配置路径用环境变量 OPENAB_CONFIG。"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path.home() / ".config" / "openab"


def get_config_path() -> Path:
    """默认路径为 ~/.config/openab/config.yaml，可通过环境变量 OPENAB_CONFIG 覆盖。"""
    p = os.environ.get("OPENAB_CONFIG", "").strip()
    if p:
        return Path(p).expanduser().resolve()
    return _CONFIG_DIR / "config.yaml"


def _find_config_file() -> Path | None:
    """优先 YAML，其次 JSON；若 OPENAB_CONFIG 已指定则只认该文件。"""
    explicit = os.environ.get("OPENAB_CONFIG", "").strip()
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return path if path.is_file() else None
    base = _CONFIG_DIR
    for name in ("config.yaml", "config.yml", "config.json"):
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def load_config(explicit_path: Path | None = None) -> dict[str, Any]:
    """从指定路径或默认/OPENAB_CONFIG 路径加载 YAML 或 JSON，文件不存在或解析失败返回空 dict。"""
    if explicit_path is not None:
        path = explicit_path.expanduser().resolve()
        if not path.is_file():
            return {}
    else:
        path = _find_config_file()
        if not path:
            return {}
    try:
        text = path.read_text(encoding="utf-8")
        suf = path.suffix.lower()
        if suf in (".json",):
            return json.loads(text)
        # .yaml / .yml
        import yaml
        return yaml.safe_load(text) or {}
    except Exception as e:
        logger.warning("Failed to load config from %s: %s", path, e)
        return {}


def resolve_workspace(config: dict[str, Any], cli_workspace: Path | None) -> Path:
    """CLI 传入的 workspace 优先，否则取 config.agent.workspace，否则家目录。"""
    if cli_workspace is not None:
        return cli_workspace.expanduser().resolve()
    agent = config.get("agent") or {}
    raw = agent.get("workspace")
    if not raw:
        return Path.home()
    if isinstance(raw, Path):
        return raw.expanduser().resolve()
    s = str(raw).strip()
    if s in ("", "~"):
        return Path.home()
    return Path(s).expanduser().resolve()


def parse_allowed_user_ids(raw: Any) -> frozenset[int]:
    """从配置中的列表或逗号分隔字符串解析出用户 ID 集合。"""
    if raw is None:
        return frozenset()
    if isinstance(raw, list):
        out = []
        for x in raw:
            if isinstance(x, int):
                out.append(x)
            elif isinstance(x, str) and x.strip().isdigit():
                out.append(int(x.strip()))
        return frozenset(out)
    if isinstance(raw, str):
        return frozenset(
            int(x.strip()) for x in raw.split(",") if x.strip().isdigit()
        )
    return frozenset()


def get_config_file_path() -> Path:
    """当前使用的配置文件路径；不存在时返回默认路径（用于新建）。"""
    path = _find_config_file()
    if path:
        return path
    return get_config_path()


def _get_nested(data: dict[str, Any], key: str) -> Any:
    """点号键如 agent.backend 取嵌套值。"""
    keys = key.strip().split(".")
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _set_nested(data: dict[str, Any], key: str, value: Any) -> None:
    """点号键如 agent.backend 写嵌套值，自动创建中间 dict。"""
    keys = key.strip().split(".")
    cur = data
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


# 需要转为整数的键
_INT_KEYS = frozenset({"agent.timeout"})
# 需要转为整数组的键（逗号分隔字符串 -> list[int]）
_LIST_INT_KEYS = frozenset({"telegram.allowed_user_ids", "discord.allowed_user_ids"})


def coerce_config_value(key: str, raw: str) -> Any:
    """根据键名将字符串转为合适类型。"""
    if key in _LIST_INT_KEYS:
        return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
    if key in _INT_KEYS:
        try:
            return int(raw.strip())
        except ValueError:
            return raw.strip()
    return raw.strip()


def save_config(config: dict[str, Any], path: Path | None = None) -> Path:
    """将配置写回 YAML 或 JSON；path 为空时用当前或默认路径，格式按扩展名。"""
    if path is None:
        path = _find_config_file() or get_config_path()
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    suf = path.suffix.lower()
    text: str
    if suf == ".json":
        text = json.dumps(config, indent=2, ensure_ascii=False)
    else:
        import yaml
        text = yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(text, encoding="utf-8")
    return path
