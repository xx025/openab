"""中英文文案适配。根据 Telegram 的 language_code 或 LANG 选择 zh / en。"""
from __future__ import annotations

import os
from typing import Any

from openab.core.i18n.bot import MESSAGES
from openab.core.i18n.cli import CLI_MESSAGES

# 无法从系统获取时的回退语言
DEFAULT_LANG = "en"


def _system_lang() -> str:
    """从环境变量 LANG / LANGUAGE / LC_ALL 解析系统语言，不依赖 _normalize_lang 避免循环。"""
    for key in ("LANG", "LANGUAGE", "LC_ALL"):
        val = os.environ.get(key, "")
        if val:
            code = val.split(":")[0].split(".")[0].strip().lower()
            if code.startswith("zh"):
                return "zh"
            return "en"
    return DEFAULT_LANG


def _normalize_lang(code: str | None) -> str:
    """Telegram language_code 或 LANG → 'zh' | 'en'。无 code 时使用系统语言。"""
    if not (code or "").strip():
        return _system_lang()
    code = (code or "").strip().lower()
    if code.startswith("zh"):
        return "zh"
    return "en"


def lang_from_telegram(language_code: str | None) -> str:
    """根据 Telegram 用户的 language_code 返回 'zh' 或 'en'；未提供时用系统语言。"""
    return _normalize_lang(language_code)


def lang_from_env() -> str:
    """根据环境变量 LANG / LANGUAGE 返回 'zh' 或 'en'（用于 CLI）。"""
    return _system_lang()


def t(lang: str, key: str, **kwargs: Any) -> str:
    """取文案。lang 为 'zh' 或 'en'，key 为 MESSAGES 中的键，kwargs 用于 format。"""
    locale = "zh" if lang == "zh" else "en"
    msg = MESSAGES[locale].get(key, MESSAGES[DEFAULT_LANG].get(key, key))
    if kwargs:
        return msg.format(**kwargs)
    return msg


def cli_t(key: str, **kwargs: Any) -> str:
    """CLI 文案，按 LANG 环境变量。"""
    lang = lang_from_env()
    locale = "zh" if lang == "zh" else "en"
    msg = CLI_MESSAGES[locale].get(key, CLI_MESSAGES[DEFAULT_LANG].get(key, key))
    if kwargs:
        return msg.format(**kwargs)
    return msg


__all__ = [
    "MESSAGES",
    "CLI_MESSAGES",
    "DEFAULT_LANG",
    "t",
    "cli_t",
    "lang_from_telegram",
    "lang_from_env",
]
