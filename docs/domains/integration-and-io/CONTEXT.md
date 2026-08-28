# Integration & I/O Context

The Integration & I/O context governs structured web content retrieval, OpenAPI client generation, external webhook broadcasting, and symbolic constraint evaluation.

## Language

**Web Fetcher**:
A clean HTTP client that streams external web endpoints and converts HTML DOMs directly into clean markdown without headless browser overhead.
_Avoid_: Web scraper, page downloader, crawler

**API Adapter**:
An automated tool generator that parses OpenAPI/Swagger specifications and synthesizes typed, callable agent tools.
_Avoid_: Swagger wrapper, REST client

**Webhook Dispatcher**:
An asynchronous notification broadcaster that sends structured JSON event payloads to external endpoints.
_Avoid_: Alert sender, HTTP poster

**Symbolic Solver**:
A formal verification engine that uses SMT/Z3 solvers to verify logical formulas and compute constraint solutions.
_Avoid_: Math engine, formula calculator

**Plugin Forge**:
An autonomous pipeline that translates external repository architectures into Harness plugins with typed services and manifests.
_Avoid_: Plugin creator, repo converter, wrapper generator

**Book-to-Skill Forge**:
A structured synthesis engine that converts books, articles, frameworks, and video transcripts into deep-module agent skills and coaching rubrics.
_Avoid_: Book summarizer, text condenser, reading assistant

