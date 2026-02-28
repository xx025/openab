"""OpenAB API：OpenAI Chat Completions 与 Responses API 兼容。"""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Generator, Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

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


def _text_from_content(content: Any) -> str:
    """从 message content（字符串或 items 数组）提取纯文本。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return " ".join(
            str(c.get("text", c) if isinstance(c, dict) else c)
            for c in content
            if c
        ).strip()
    return str(content).strip()


def _prompt_from_responses_input(input_val: Any) -> str:
    """从 Responses API 的 input（字符串、单条 message 对象、或 items 数组）提取用户输入文本。"""
    if input_val is None:
        return ""
    if isinstance(input_val, str):
        return input_val.strip()
    if isinstance(input_val, dict):
        content = input_val.get("content")
        return _text_from_content(content)
    if isinstance(input_val, list):
        parts = []
        for item in input_val:
            if not isinstance(item, dict):
                continue
            role = (item.get("role") or "").strip().lower()
            if role != "user":
                continue
            content = item.get("content")
            text = _text_from_content(content)
            if text:
                parts.append(text)
        return "\n\n".join(parts) if parts else ""
    return str(input_val).strip()


def _check_api_key(api_key: Optional[str], authorization: Optional[str]) -> None:
    """标准 OpenAI 鉴权：要求请求头 Authorization: Bearer <api.key>。"""
    if not api_key:
        return
    if not authorization or not isinstance(authorization, str):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    raw = authorization.strip()
    if not raw.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = raw[7:].strip()
    if not token or token != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def create_app(
    *,
    config: Optional[dict[str, Any]] = None,
    config_path: Optional[Path] = None,
    api_key_override: Optional[str] = None,
) -> FastAPI:
    """创建 FastAPI 应用，使用给定配置或从 config_path 加载。api_key_override 可覆盖配置中的 api.key。"""
    if config is None:
        config = load_config(config_path) if config_path else load_config()
    workspace = resolve_workspace(config, None)
    timeout = int((config.get("agent") or {}).get("timeout") or 300)
    api_key = (api_key_override or "").strip() or None
    if api_key is None:
        api_key = (config.get("api") or {}).get("key") or (config.get("api") or {}).get("api_key")
        if isinstance(api_key, bool):
            api_key = None
        api_key = (api_key or "").strip() or None

    app = FastAPI(title="OpenAB API", description="OpenAI Chat Completions & Responses API compatible")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _chat_stream_chunks(reply: str, completion_id: str, model: str) -> Generator[str, None, None]:
        """SSE 流：先发 role delta，再发整段 content，最后 finish。"""
        yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]})}\n\n"
        if reply:
            yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {'content': reply}, 'finish_reason': None}]})}\n\n"
        yield f"data: {json.dumps({'id': completion_id, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        yield "data: [DONE]\n\n"

    @app.post("/v1/chat/completions")
    async def chat_completions(
        request: Request,
        authorization: Optional[str] = Header(None, alias="Authorization"),
    ):
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

        reply = reply or ""
        created = int(time.time())
        completion_id = f"openab-{created}"

        if stream:
            return StreamingResponse(
                _chat_stream_chunks(reply, completion_id, model),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        return JSONResponse(
            content={
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
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

    @app.post("/v1/responses")
    async def responses(
        request: Request,
        authorization: Optional[str] = Header(None, alias="Authorization"),
    ) -> JSONResponse:
        """OpenAI Responses API 兼容：input/instructions → agent → output items。"""
        _check_api_key(api_key, authorization)
        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Body must be a JSON object")

        input_val = body.get("input")
        if input_val is None and "messages" in body:
            input_val = body.get("messages")
        instructions = (body.get("instructions") or "").strip()
        prompt = _prompt_from_responses_input(input_val)
        if not prompt and not instructions:
            raise HTTPException(status_code=400, detail="Missing or empty 'input' and 'instructions'")
        if instructions and prompt:
            prompt = instructions + "\n\n" + prompt
        elif instructions:
            prompt = instructions

        model = body.get("model") or "openab"
        stream = body.get("stream") is True

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

        reply = reply or ""
        response_id = "resp_" + uuid.uuid4().hex
        msg_id = "msg_" + uuid.uuid4().hex
        created = int(time.time())
        output_item = {
            "id": msg_id,
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": reply}],
        }
        return JSONResponse(
            content={
                "id": response_id,
                "object": "response",
                "created": created,
                "model": model,
                "output": [output_item],
                "output_text": reply,
            }
        )

    @app.get("/v1/models")
    async def models(
        authorization: Optional[str] = Header(None, alias="Authorization"),
    ) -> JSONResponse:
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
