# plugin.web_fetcher (v1.0.0)

Clean web page fetcher, automated HTML-to-Markdown distillation, and custom HTTP request client

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/web_fetcher` |
| Category | `integration_and_io` |
| Isolation Mode | `in_process` |
| Services Provided | `service.web_fetcher` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `web_fetch_url` | `(url, timeout)` | Fetch a remote web page by URL and return status, response headers, and raw text body |
| `web_fetch_markdown` | `(url, timeout)` | Fetch a URL and automatically distill HTML layout and styling into clean Markdown |
| `web_http_request` | `(url, method, headers, json_data, timeout)` | Perform custom HTTP requests (GET, POST, PUT, DELETE, PATCH) with custom headers and JSON payloads |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Web fetcher and HTML-to-Markdown distillation tools.

#### Classes

- `class WebFetcherPlugin` — Harness Plugin providing web fetching, markdown extraction, and HTTP request capabilities.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def fetch_url(url, timeout) -> WebFetchResult`
  - `def fetch_url_async(url, timeout) -> WebFetchResult`
  - `def fetch_markdown(url, timeout) -> WebMarkdownResult`
  - `def fetch_markdown_async(url, timeout) -> WebMarkdownResult`
  - `def http_request(url, method, headers, json_data, timeout) -> WebHttpResponse`
  - `def http_request_async(url, method, headers, json_data, timeout) -> WebHttpResponse`


#### Functions

- `def web_fetch_url(url, timeout) -> dict[str, Any]` — Fetch URL and return status, headers, and text body.
- `def web_fetch_markdown(url, timeout) -> dict[str, Any]` — Fetch URL and convert the HTML response to clean Markdown.
- `def web_http_request(url, method, headers, json_data, timeout) -> dict[str, Any]` — Perform a custom HTTP request.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.web_fetcher.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
