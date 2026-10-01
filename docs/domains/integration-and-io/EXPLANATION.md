# Integration & I/O Domain Architecture

The Integration & I/O domain governs external web content retrieval, OpenAPI client generation, external webhook broadcasting, and foreign codebase ingestion.

---

## Domain Scope & Boundaries

This domain coordinates bidirectional communication between Brain Harness and the outside world:
- **In Scope**: Clean HTTP web fetching without headless browser overhead, OpenAPI/Swagger specification conversion to agent tools, webhook event dispatching, and external GitHub repository ingestion.
- **Out of Scope**: High-level multi-agent swarms (Agent Orchestration), internal event bus logging (Events), or local SQLite storage (Kernel).

---

## Ubiquitous Language & Core Terminology

- **Web Fetcher**: A clean HTTP client that streams external web endpoints and converts HTML DOMs directly into clean markdown without headless browser overhead. (*Avoid*: Web scraper, page downloader, crawler)
- **API Adapter**: An automated tool generator that parses OpenAPI/Swagger specifications and synthesizes typed, callable agent tools. (*Avoid*: Swagger wrapper, REST client)
- **Webhook Dispatcher**: An asynchronous notification broadcaster that sends structured JSON event payloads to external endpoints. (*Avoid*: Alert sender, HTTP poster)
- **Symbolic Solver**: A formal verification engine that uses SMT/Z3 solvers to verify logical formulas and compute constraint solutions. (*Avoid*: Math engine, formula calculator)
- **Plugin Forge**: An autonomous pipeline that translates external repository architectures into Harness plugins with typed services and manifests. (*Avoid*: Plugin creator, repo converter, wrapper generator)
- **Book-to-Skill Forge**: A structured synthesis engine that converts books, articles, frameworks, and video transcripts into deep-module agent skills and coaching rubrics. (*Avoid*: Book summarizer, text condenser, reading assistant)

---

## Architectural Invariants & Patterns

- **External Ingestion & Protection Boundaries (Rule 46)**: Filesystem inspection of external repositories uses non-modifying shell reads or isolated runner scripts when IDE boundaries restrict access.
- **Stateless MCP Isolation (Rule 24)**: External API pipelines and simulation engines are partitioned behind Model Context Protocol (MCP) servers with JSONSchema validation.
- **Large Corpus Binary Byte-Offset Seek (Rule 48)**: When ingesting large text dumps or document corpora, retrieval engines use lazy binary byte-offset index tables and $O(1)$ seeks.

---

## Co-Located Plugins & Micro-Kernel Services

- **Ingestion Pipeline**: [`src/harness/ingestion/pipeline.py`](../../../src/harness/ingestion/pipeline.py) providing `PluginIngestionPipeline`.
- **OpenAPI Converter**: [`src/harness/ingestion/openapi_converter.py`](../../../src/harness/ingestion/openapi_converter.py) providing `OpenApiConverter`.
- **Web Fetcher Service**: [`src/harness/services/web_fetcher.py`](../../../src/harness/services/web_fetcher.py) providing `WEB_FETCHER_KEY`.
- **CellCog Service**: [`src/harness/services/cellcog.py`](../../../src/harness/services/cellcog.py) providing `CELLCOG_SERVICE_KEY`.
- **ChatbotX Service**: [`src/harness/services/chatbotx.py`](../../../src/harness/services/chatbotx.py) providing `CHATBOTX_SERVICE_KEY`.

---

## Associated Agent Skills

- [`external-repo-bridge-forge`](../../../.agents/skills/external-repo-bridge-forge/SKILL.md): Ingests external GitHub repositories into sandboxed Harness plugins.
- [`book-to-skill-forge`](../../../.agents/skills/book-to-skill-forge/SKILL.md): Transforms non-fiction books and frameworks into deep agent skills.
- [`youtube-transcript-fetcher`](../../../.agents/skills/youtube-transcript-fetcher/SKILL.md): Extracts video transcripts and captions via isolated subprocess RPC.
- [`multimedia-intelligence-forge`](../../../.agents/skills/multimedia-intelligence-forge/SKILL.md): Distills multimedia lectures and literature into verified skills.
