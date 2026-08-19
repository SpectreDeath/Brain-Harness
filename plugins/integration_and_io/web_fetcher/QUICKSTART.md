# Quick Start Guide: `plugin.web_fetcher` (v1.0.0)

> Safe web fetching, HTML-to-Markdown distillation, and REST API client

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`web_fetch_url`**: Fetch a web page and return raw response text and headers
- **`web_fetch_markdown`**: Fetch web page and convert HTML into clean LLM-friendly Markdown
- **`web_http_request`**: Perform an HTTP request with custom method, headers, or JSON body

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.web_fetcher.web_fetch_url', {'url': '<url>', 'timeout': '<timeout>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.web_fetcher
harness plugin enable plugin.web_fetcher
```

## ⚡ Available Entrypoints & Skills
- **`web_fetch_url(url: string, timeout: number)`**
  Fetch a web page and return raw response text and headers
- **`web_fetch_markdown(url: string, timeout: number)`**
  Fetch web page and convert HTML into clean LLM-friendly Markdown
- **`web_http_request(url: string, method: string, headers: object, json_data: object, timeout: number)`**
  Perform an HTTP request with custom method, headers, or JSON body