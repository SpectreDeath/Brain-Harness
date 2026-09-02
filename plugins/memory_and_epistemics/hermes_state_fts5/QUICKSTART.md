# Quick Start Guide: `domain.hermes_state_fts5`

## 🎯 When to Use
Use this plugin for high-speed SQLite FTS5 conversation search and parent-child session tree DAG persistence.

## 🛠️ Available Entrypoints
- `fts5_search_messages(query, session_id, limit)`
- `fork_session_tree(parent_session_id, compression_checkpoint)`
- `compress_session_slice(session_id, window_size)`
- `query_session_provenance(message_id)`
