# Quick Start Guide: `plugin.vector_index` (v1.0.0)

> Local semantic vector index, natural language code/doc retrieval, and hybrid search

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`vector_index_directory`**: Scan and index source code or markdown documents in a directory for semantic search
- **`vector_search_semantic`**: Perform natural language semantic cosine search over the indexed chunks
- **`vector_search_hybrid`**: Perform hybrid lexical + semantic search combining exact keyword and vector ranking

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.vector_index.vector_index_directory', {'path': '<path>', 'extensions': '<extensions>', 'chunk_lines': '<chunk_lines>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.vector_index
harness plugin enable plugin.vector_index
```

## ⚡ Available Entrypoints & Skills
- **`vector_index_directory(path: string, extensions: array, chunk_lines: integer)`**
  Scan and index source code or markdown documents in a directory for semantic search
- **`vector_search_semantic(query: string, top_k: integer)`**
  Perform natural language semantic cosine search over the indexed chunks
- **`vector_search_hybrid(query: string, keyword: string, top_k: integer)`**
  Perform hybrid lexical + semantic search combining exact keyword and vector ranking