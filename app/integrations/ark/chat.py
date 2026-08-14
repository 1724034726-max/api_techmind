# 火山方舟对话补全（OpenAI 兼容 chat/completions）
from __future__ import annotations

import json
import threading
from collections.abc import Iterator

import httpx

from app.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import exception


def ark_chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.2,
    timeout: float = 60.0,
) -> str:
    """发送 messages，返回助手 content 文本。"""
    settings = get_settings()
    # 校验密钥
    if not settings.ark_api_key:
        raise exception(ErrorCode.ERR_AI_NOT_CONFIGURED)
    if not messages:
        raise exception(ErrorCode.ERR_VALIDATION, detail="messages 不能为空")

    url = settings.ark_chat_completions_endpoint
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.ark_api_key}",
    }
    payload: dict = {
        "model": model or settings.ark_chat_model,
        "messages": messages,
        "temperature": temperature,
    }

    # 调用方舟 chat completions
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise exception(ErrorCode.ERR_AI_UPSTREAM) from exc

    if resp.status_code >= 400:
        raise exception(
            ErrorCode.ERR_AI_UPSTREAM,
            detail=(resp.text or "")[:500],
        )

    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    return str(content)


def ark_chat_completion_stream(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.2,
    timeout: float = 120.0,
    cancel: threading.Event | None = None,
) -> Iterator[str]:
    """流式调用方舟，逐段 yield content delta；cancel.set 后尽快结束并关闭连接。"""
    settings = get_settings()
    if not settings.ark_api_key:
        raise exception(ErrorCode.ERR_AI_NOT_CONFIGURED)
    if not messages:
        raise exception(ErrorCode.ERR_VALIDATION, detail="messages 不能为空")

    url = settings.ark_chat_completions_endpoint
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.ark_api_key}",
        "Accept": "text/event-stream",
    }
    payload: dict = {
        "model": model or settings.ark_chat_model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code >= 400:
                    body = (resp.read() or b"").decode("utf-8", errors="replace")[:500]
                    raise exception(ErrorCode.ERR_AI_UPSTREAM, detail=body)
                for line in resp.iter_lines():
                    if cancel is not None and cancel.is_set():
                        return
                    if not line:
                        continue
                    if line.startswith(":"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        if data == "[DONE]":
                            break
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = (choices[0].get("delta") or {}).get("content")
                    if isinstance(delta, str) and delta:
                        yield delta
                        if cancel is not None and cancel.is_set():
                            return
    except httpx.HTTPError as exc:
        if cancel is not None and cancel.is_set():
            return
        raise exception(ErrorCode.ERR_AI_UPSTREAM) from exc


def ark_chat(
    user_prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
    timeout: float = 60.0,
) -> str:
    """可选 system + user 的单次问答。"""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    return ark_chat_completion(
        messages,
        model=model,
        temperature=temperature,
        timeout=timeout,
    )


def ark_chat_stream(
    user_prompt: str,
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
    timeout: float = 120.0,
    cancel: threading.Event | None = None,
) -> Iterator[str]:
    """可选 system + user 的流式问答。"""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    return ark_chat_completion_stream(
        messages,
        model=model,
        temperature=temperature,
        timeout=timeout,
        cancel=cancel,
    )
