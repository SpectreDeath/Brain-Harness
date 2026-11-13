# Bot HQ: Primary-vs-Managed Gateway & Screen Isolation

## Invariants
1. **Primary Gateway Non-Interference**: Never restart, stop, or overwrite `config.yaml` of the host's primary agent; attach MCP tools explicitly with a dated backup (`scripts/add-hq-to-hermes.py`).
2. **Managed Bot Isolation**: Each additional bot gets its own `ENGINES_DIR/<botId>`, gateway port (`8650 + slot`), `BH_HOME` browser helper, Chrome profile/CDP port (`9200 + display`), and Orgo X display lease (max 4 screens per computer).
