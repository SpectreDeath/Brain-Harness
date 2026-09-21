# Plain-Text Chunk Streaming Architecture for Gemini on Vercel Serverless

## Executive Summary
This Knowledge Item captures the core architectural patterns and invariant rules for deploying real-time streaming AI chatbots using Google Gemini (`@google/genai`) and Vercel Serverless Functions, derived from Johnson Samuel's literature (*How to Build an AI Chatbot with Gemini and Vercel Serverless Functions 🚀*, freeCodeCamp, 2026).

## Architectural Mechanics

### 1. Plain-Text Chunk Streaming Backend
- Rather than waiting for full completion generation before returning a response (`res.json()`), the backend serverless function opens an unbuffered text stream:
  ```javascript
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  ```
- The `@google/genai` client emits an asynchronous generator via `ai.models.generateContentStream(...)`. As each text delta is yielded, `res.write(chunk.text)` immediately flushes bytes across the network pipe to the client.

### 2. Cross-Domain CORS Preflight Interception
- Embedded widgets operating across origins trigger automated browser `OPTIONS` preflight requests.
- Serverless handlers wrapped with an `allowCors` middleware must intercept `req.method === 'OPTIONS'` and immediately return `res.status(200).end()` with permitted origins, headers, and HTTP methods. Unhandled preflight requests fail silently in browser environments.

### 3. Pre-Flight Terminal Stream Verification
- Before wiring UI widgets, the endpoint must be validated using `curl -N -X POST`. The `-N` (`--no-buffer`) flag ensures standard output displays incremental chunks as they arrive, proving that neither the hosting platform nor reverse proxies are buffering response bodies into monolithic chunks.

### 4. Client-Side ReadableStream Default Reader Loop
- On the client side, standard `fetch()` is paired with `res.body.getReader()` to obtain a `ReadableStreamDefaultReader`.
- Chunks are decoded on-the-fly using `TextDecoder.decode(value, { stream: true })`. State updates are applied functionally to the active assistant dialogue bubble, generating an authentic real-time typewriter effect.

## Verifiable Isnad Lineage
- **Grounding Source**: Johnson Samuel, *How to Build an AI Chatbot with Gemini and Vercel Serverless Functions 🚀*, freeCodeCamp (2026-09-17).
- **Core Implementation**: `buildcv.makeadifference.app` chat widget architecture.
- **Governing Principles**: `AGENTS.md` Rule 11 (Hygiene & Boundaries), Rule 37 (ASCII Card Formatting), Rule 40 (Dual-File Directory Invariant), Rule 41 (Dual-Lens Distillation Seam), Rule 44 (Dual-Tier Catalog Budget).
