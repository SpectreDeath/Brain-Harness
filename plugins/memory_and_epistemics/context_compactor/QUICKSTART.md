# Quick Start Guide: `plugin.context_compactor` (v1.0.0)

> Agent trajectory summarization, context compaction, and persistent memory offloading via Memtext

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`compact_conversation`**: Compact a message list by summarizing earlier history while preserving recent messages
- **`offload_to_memory`**: Offload important notes, code snippets, or facts to Memtext persistent memory
- **`recall_context`**: Recall stored memories and context matching a query

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.context_compactor.compact_conversation', {'messages': '<messages>', 'preserve_recent': '<preserve_recent>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.context_compactor
harness plugin enable plugin.context_compactor
```

## ⚡ Available Entrypoints & Skills
- **`compact_conversation(messages: array, preserve_recent: integer)`**
  Compact a message list by summarizing earlier history while preserving recent messages
- **`offload_to_memory(key: string, content: string, topic: string)`**
  Offload important notes, code snippets, or facts to Memtext persistent memory
- **`recall_context(query: string, limit: integer)`**
  Recall stored memories and context matching a query