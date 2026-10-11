"""Asynchronous HTTP execution and Context Epoch formatting for OpenRouter."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from typing import Any, cast

from harness.services.openrouter_gateway.headers import build_kilo_headers


def format_context_epoch_messages(
    baseline_system_prompt: str,
    messages: list[dict[str, Any]],
    mid_conversation_updates: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Format messages to preserve KV-cache prefix under Kilo Context Epoch heuristics (KI-KILO-01)."""
    formatted: list[dict[str, Any]] = [
        {"role": "system", "content": baseline_system_prompt}
    ]

    for msg in messages:
        if msg.get("role") == "system":
            continue
        formatted.append(msg)

    if mid_conversation_updates:
        combined_updates = "\n\n".join(mid_conversation_updates)
        formatted.append({
            "role": "system",
            "content": f"[Context Update]\n{combined_updates}",
        })

    return formatted


async def async_http_post(
    base_url: str,
    endpoint_path: str,
    payload: dict[str, Any],
    api_key: str | None = None,
    organization_id: str | None = None,
    task_id: str | None = None,
    feature: str | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Perform asynchronous HTTP POST request to OpenRouter / Kilo Gateway."""
    url = f"{base_url}/{endpoint_path.lstrip('/')}"
    headers = build_kilo_headers(
        task_id=task_id,
        organization_id=organization_id,
        feature=feature,
    )
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    def _do_request() -> dict[str, Any]:
        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = resp.read().decode("utf-8")
                return cast(dict[str, Any], json.loads(resp_data))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                parsed_err = json.loads(err_body)
            except Exception:
                parsed_err = {"error": err_body}
            raise RuntimeError(f"OpenRouter HTTP {e.code}: {parsed_err}") from e
        except Exception as e:
            raise RuntimeError(f"OpenRouter network error: {e}") from e

    return await asyncio.to_thread(_do_request)


async def async_http_get(
    base_url: str,
    endpoint_path: str,
    api_key: str | None = None,
    organization_id: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Perform asynchronous HTTP GET request."""
    url = f"{base_url}/{endpoint_path.lstrip('/')}"
    headers = build_kilo_headers(organization_id=organization_id)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    def _do_request() -> dict[str, Any]:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = resp.read().decode("utf-8")
                return cast(dict[str, Any], json.loads(resp_data))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter HTTP {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"OpenRouter network error: {e}") from e

    return await asyncio.to_thread(_do_request)
