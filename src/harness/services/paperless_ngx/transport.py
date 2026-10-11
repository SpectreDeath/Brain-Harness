"""HTTP transport and authentication utilities for Paperless-NGX REST API."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from harness.services.paperless_ngx.models import PaperlessConfig


def get_auth_headers(config: PaperlessConfig) -> dict[str, str]:
    """Build Authorization and User-Agent headers for Paperless REST API."""
    token = config.api_token or os.environ.get("PAPERLESS_API_TOKEN", "")
    return {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
        "User-Agent": "Brain-Harness-PaperlessNgx/1.0",
    }


def fetch_url_json(url: str, config: PaperlessConfig) -> Any:
    """Execute synchronous GET request to Paperless endpoint and decode JSON payload."""
    req = urllib.request.Request(url, headers=get_auth_headers(config))
    with urllib.request.urlopen(req, timeout=config.timeout_seconds) as resp:
        return json.loads(resp.read().decode("utf-8"))
