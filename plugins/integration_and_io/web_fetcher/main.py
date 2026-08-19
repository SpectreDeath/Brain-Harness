"""Web fetcher and HTML-to-Markdown distillation tools."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any


def _html_to_markdown(html_content: str) -> str:
    """Convert HTML content to clean, readable Markdown."""
    # 1. Remove script, style, head, noscript, and iframe elements
    cleaned = re.sub(r"<(script|style|head|noscript|iframe)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)

    # 2. Convert headers: <h1> -> # Header
    for level in range(6, 0, -1):
        cleaned = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            lambda m, lvl=level: f"\n{'#' * lvl} {m.group(1).strip()}\n",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )

    # 3. Convert code blocks and pre
    cleaned = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"\n```\n\1\n```\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # 4. Convert links: <a href="url">text</a> -> [text](url)
    cleaned = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # 5. Convert lists
    cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"</?(ul|ol)[^>]*>", "\n", cleaned, flags=re.IGNORECASE)

    # 6. Convert paragraphs, line breaks, blockquotes
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<blockquote[^>]*>(.*?)</blockquote>", r"\n> \1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # 7. Strip remaining HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # 8. Unescape common HTML entities
    cleaned = (
        cleaned.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )

    # 9. Clean excessive blank lines
    lines = [line.strip() for line in cleaned.splitlines()]
    result: list[str] = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                result.append("")
                prev_blank = True
        else:
            result.append(line)
            prev_blank = False

    return "\n".join(result).strip()


def web_fetch_url(url: str, timeout: float = 15.0) -> dict[str, Any]:
    """Fetch URL and return status, headers, and text body."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BrainHarness/1.0 (Autonomous Agent Assistant)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            headers = dict(response.info()) if hasattr(response.info(), "items") else {}
            info_obj = response.info()
            charset = info_obj.get_content_charset() if hasattr(info_obj, "get_content_charset") else "utf-8"
            charset = charset or "utf-8"
            raw_data = response.read()
            body_text = raw_data.decode(charset, errors="replace")

            return {
                "status": "ok",
                "status_code": status_code,
                "url": url,
                "headers": headers,
                "body": body_text,
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "status_code": e.code,
            "error": f"HTTP Error {e.code}: {e.reason}",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def web_fetch_markdown(url: str, timeout: float = 15.0) -> dict[str, Any]:
    """Fetch URL and convert the HTML response to clean Markdown."""
    res = web_fetch_url(url, timeout=timeout)
    if res.get("status") != "ok":
        return res

    body = res.get("body", "")
    markdown = _html_to_markdown(body)

    return {
        "status": "ok",
        "url": url,
        "markdown": markdown,
        "length_chars": len(markdown),
    }


def web_http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Perform a custom HTTP request."""
    try:
        req_headers = headers or {}
        req_headers.setdefault("User-Agent", "BrainHarness/1.0 (Autonomous Agent Assistant)")

        data_bytes = None
        if json_data is not None:
            data_bytes = json.dumps(json_data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=req_headers,
            method=method.upper(),
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            resp_headers = dict(response.info()) if hasattr(response.info(), "items") else {}
            info_obj = response.info()
            charset = info_obj.get_content_charset() if hasattr(info_obj, "get_content_charset") else "utf-8"
            charset = charset or "utf-8"
            raw_body = response.read().decode(charset, errors="replace")

            parsed_json = None
            if "application/json" in resp_headers.get("Content-Type", ""):
                try:
                    parsed_json = json.loads(raw_body)
                except Exception:
                    pass

            return {
                "status": "ok",
                "status_code": status_code,
                "url": url,
                "headers": resp_headers,
                "json": parsed_json,
                "body": raw_body if parsed_json is None else None,
            }
    except urllib.error.HTTPError as e:
        return {"status": "error", "status_code": e.code, "error": f"HTTP Error {e.code}: {e.reason}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
