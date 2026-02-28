"""OpenAI API 兼容 HTTP 服务，供兼容客户端（Open WebUI、SDK 等）接入。"""
from __future__ import annotations

from openab.api.app import create_app

__all__ = ["create_app"]
