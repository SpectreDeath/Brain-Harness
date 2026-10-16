# Google ADK Docs Navigator Plugin

Searches ADK docs, fetches API signatures, and queries llms.txt.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `adk_docs_search` | `(query, category, limit)` | Search ADK documentation, architecture guides, tutorials, and concepts |
| `adk_get_api_reference` | `(symbol_name, language)` | Retrieve official API references and code signatures for ADK across Python, TypeScript, Go, or Kotlin |
| `adk_fetch_llms_txt` | `(topic, full_content)` | Fetch structured plain-text documentation sections optimized for AI agent consumption |
