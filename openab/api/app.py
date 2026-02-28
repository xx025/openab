"""OpenAI Chat Completions 兼容端点：POST /v1/chat/completions。"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from openab.agents import run_agent_async
from openab.core.config import load_config, resolve_workspace

logger = logging.getLogger(__name__)


def _prompt_from_messages(messages: list[dict[str, Any]]) -> str:
    """从 OpenAI 格式 messages 中取出最后一条 user 的 content，或拼接所有 user 内容。"""
    parts = []
    for m in messages:
        role = (m.get("role") or "").strip().lower()
        content = m.get("content")
        if content is None:
            continue
        if isinstance(content, list):
            text = " ".join(
                str(c.get("text", c) if isinstance(c, dict) else c)
                for c in content
                if c
            ).strip()
        else:
            text = str(content).strip()
        if not text:
            continue
        if role == "user":
            parts.append(text)
    return "\n\n".join(parts) if parts else ""


def _check_api_key(api_key: Optional[str], authorization: Optional[str] = Header(None)) -> None:
    if not api_key:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:].strip()
    if token != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def create_app(
    *,
    config: Optional[dict[str, Any]] = None,
    config_path: Optional[Path] = None,
) -> FastAPI:
    """创建 FastAPI 应用，使用给定配置或从 config_path 加载。"""
    if config is None:
        config = load_config(config_path) if config_path else load_config()
    workspace = resolve_workspace(config, None)
    timeout = int((config.get("agent") or {}).get("timeout") or 300)
    api_key = (config.get("api") or {}).get("key") or (config.get("api") or {}).get("api_key")
    if isinstance(api_key, bool):
        api_key = None
    api_key = (api_key or "").strip() or None

    app = FastAPI(title="OpenAB API", description="OpenAI API compatible chat completions")

    @app.post("/v1/chat/completions")
    async def chat_completions(
        request: Request,
        authorization: Optional[str] = Header(None),
    ) -> JSONResponse:
        _check_api_key(api_key, authorization)
        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        messages = body.get("messages") if isinstance(body, dict) else None
        if not messages or not isinstance(messages, list):
            raise HTTPException(status_code=400, detail="Missing or invalid 'messages' array")
        prompt = _prompt_from_messages(messages)
        if not prompt:
            raise HTTPException(status_code=400, detail="No user message content in 'messages'")

        model = (body.get("model") or "openab") if isinstance(body, dict) else "openab"
        stream = body.get("stream") is True if isinstance(body, dict) else False
        if stream:
            raise HTTPException(status_code=501, detail="Streaming not supported yet")

        try:
            reply = await run_agent_async(
                prompt,
                workspace=workspace,
                timeout=timeout,
                lang="en",
                agent_config=config,
            )
        except Exception as e:
            logger.exception("Agent run error")
            raise HTTPException(status_code=500, detail=str(e))

        created = int(time.time())
        return JSONResponse(
            content={
                "id": f"openab-{created}",
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply or ""},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }
        )

    @app.get("/v1/models")
    async def models(authorization: Optional[str] = Header(None)) -> JSONResponse:
        _check_api_key(api_key, authorization)
        return JSONResponse(
            content={
                "object": "list",
                "data": [
                    {
                        "id": "openab",
                        "object": "model",
                        "created": int(time.time()),
                    }
                ],
            }
        )

    return app
