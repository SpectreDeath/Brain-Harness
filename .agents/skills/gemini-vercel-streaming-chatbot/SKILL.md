---
name: gemini-vercel-streaming-chatbot
description: Architect, build, and deploy production AI chatbots with Google Gemini and Vercel Serverless Functions using plain-text chunk streaming, CORS preflight guards, and React stream consumers. Do not use for Python-only stacks, batch JSON APIs, or WebSocket omnichannel bots.
---

# Gemini & Vercel Streaming Chatbot: Plain-Text Chunk Streaming Architecture

The `gemini-vercel-streaming-chatbot` skill provides the definitive engineering methodology for architecting, building, verifying, and deploying production-grade AI chatbots and embeddable widgets using Google Gemini and Vercel Serverless Functions.

Synthesized from Johnson Samuel's literature (*How to Build an AI Chatbot with Gemini and Vercel Serverless Functions 🚀*, freeCodeCamp, 2026), this skill eliminates brittle chatbot implementations—such as multi-second response latency from monolithic JSON blocking, cross-domain CORS preflight failures, unverified backend streaming buffers, and client-side stream consumption bugs—by enforcing **Plain-Text Chunk Streaming**, strict payload sanitization, pre-UI `curl -N` terminal verification, and reactive `ReadableStreamDefaultReader` + `TextDecoder` loops.

```
[1. API Contract & Sanitization] -> [2. Serverless Streaming & CORS] -> [3. Pre-Flight Terminal Verification] -> [4. Reactive Stream Consumer] -> [5. Deployment & Guardrails]
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and verification checklist.
Consult [gradio-app-architect](../gradio-app-architect/SKILL.md) for Python-native interfaces, [chatbotx](../chatbotx/SKILL.md) for omnichannel messaging networks, and [crafting-skills](../crafting-skills/SKILL.md) for skill authoring craft standards.

---

## 1. API Contract & Payload Sanitization

Establish a strict boundary contract between client widgets and serverless endpoints. All client-supplied text and contextual objects must be bounded and sanitized before entering model prompt templates.

1. **Formulate Strict API Contract**:
   - Define exact request signatures for `POST /api/chat`:
     ```json
     {
       "message": "User query or prompt string",
       "resume": { "domain_specific": "contextual payload object" }
     }
     ```
   - Prohibit open-ended, untyped payload dumps. Require both active user query text and requisite domain context.
2. **Enforce Input Length & Cardinality Guardrails**:
   - Define baseline operational boundaries:
     ```javascript
     const MAX_TEXT_LENGTH = 2000;
     const MAX_ARRAY_LENGTH = 50;
     ```
   - Strip leading/trailing whitespace, non-printable characters, and excess payload depth.
   - Truncate arrays exceeding `MAX_ARRAY_LENGTH` to protect model context window limits.
3. **Assert Immediate Validation Gates**:
   - Return HTTP 400 Bad Request immediately if input message or domain context is missing, malformed, or exceeds safety thresholds. Never dispatch invalid payloads to the Gemini API.

> **Completion criterion**: API payload contract formulated with explicit length thresholds, input sanitizers, and defensive HTTP 400 validation rejection.

---

## 2. Serverless Streaming Backend & CORS Gate

Author the Vercel serverless function (`api/chat.js` or `api/chat.ts`) utilizing the `@google/genai` SDK and Node.js plain-text chunk streaming.

1. **Instantiate Gemini Client**:
   - Initialize the Google GenAI SDK client at module scope:
     ```javascript
     const { GoogleGenAI } = require("@google/genai");
     const ai = new GoogleGenAI({
       apiKey: process.env.GOOGLE_API_KEY,
     });
     ```
   - Assert presence of `process.env.GOOGLE_API_KEY`.
2. **Implement Preflight-Aware CORS Middleware (`allowCors`)**:
   - Intercept browser `OPTIONS` preflight requests and terminate with HTTP 200:
     ```javascript
     const allowCors = fn => async (req, res) => {
       res.setHeader('Access-Control-Allow-Origin', process.env.ALLOWED_ORIGIN || 'https://yourdomain.com');
       res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
       res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');

       if (req.method === 'OPTIONS') {
         return res.status(200).end();
       }
       return await fn(req, res);
     };
     ```
3. **Configure HTTP Plain-Text Streaming Response**:
   - Set streaming response headers prior to chunk emission:
     ```javascript
     res.setHeader("Content-Type", "text/plain; charset=utf-8");
     res.setHeader("Cache-Control", "no-cache, no-transform");
     ```
4. **Execute Asynchronous Stream Loop**:
   - Call `ai.models.generateContentStream` with model identifier and structured prompt:
     ```javascript
     const stream = await ai.models.generateContentStream({
       model: "gemini-2.5-flash",
       contents: promptString,
     });

     for await (const chunk of stream) {
       if (chunk.text) {
         res.write(chunk.text);
       }
     }
     res.end();
     ```
5. **Provide Diagnostic Healthcheck**:
   - Expose `GET /api/chat?type=healthcheck` returning `{ "status": "ok", "timestamp": "..." }` for uptime probing.

> **Completion criterion**: Serverless function exports CORS-wrapped streaming handler emitting incremental plain-text chunks with dedicated healthcheck probe.

---

## 3. Pre-Flight Terminal Stream Verification

Never author or debug frontend UI components against unverified streaming backends. Verify token chunk arrival directly in the terminal to ensure proxy buffering is disabled.

1. **Execute Unbuffered Terminal Request**:
   - Use `curl` with the `-N` (`--no-buffer`) flag against the local dev server or deployed staging function:
     ```bash
     curl -N -X POST "http://localhost:3000/api/chat" \
       -H "Content-Type: application/json" \
       -d '{"message":"Summarize 3 key points","resume":{"name":"Test Subject"}}'
     ```
2. **Verify Progressive Chunk Emission**:
   - Assert that text characters appear incrementally in standard output, matching the model's generation cadence.
   - If output arrives as a single monolithic block after several seconds, inspect intermediate proxies, reverse proxy caches, or missing `res.setHeader("Cache-Control", "no-cache")`.
3. **Validate Preflight Handling**:
   - Test preflight resolution via terminal:
     ```bash
     curl -I -X OPTIONS "http://localhost:3000/api/chat"
     ```
   - Assert HTTP 200 OK and expected `Access-Control-Allow-*` response headers.

> **Completion criterion**: Terminal validation confirms unbuffered, progressive token arrival and clean HTTP 200 preflight responses before frontend wiring.

---

## 4. Reactive Stream Consumer & UI State Loop

Implement the frontend stream consumer in React, Solid, or vanilla JavaScript. Decode raw byte streams into UTF-8 text and progressively update UI state to deliver a smooth "typewriter" effect.

1. **Dispatch Asynchronous Fetch**:
   - Send `POST` request with JSON stringified payload:
     ```javascript
     const res = await fetch("/api/chat", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({ message: userText, resume: domainContext }),
     });
     if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
     ```
2. **Acquire Stream Reader and TextDecoder**:
   - Obtain a `ReadableStreamDefaultReader` on the response body:
     ```javascript
     const reader = res.body.getReader();
     const decoder = new TextDecoder();
     ```
3. **Execute Incremental Accumulation Loop**:
   - Initialize an empty assistant message in state, then stream incoming chunks:
     ```javascript
     let fullText = "";
     setMessages(prev => [...prev, { role: "assistant", text: "" }]);

     while (true) {
       const { value, done } = await reader.read();
       if (done) break;

       const chunk = decoder.decode(value, { stream: true });
       fullText += chunk;

       setMessages(prev => {
         const updated = [...prev];
         updated[updated.length - 1] = { role: "assistant", text: fullText };
         return updated;
       });
     }
     ```
4. **Defensive Error Handling & Loading Reset**:
   - Wrap reader loop in `try...catch...finally`.
   - On network disruption or mid-stream error, render an actionable error message in place without wiping preceding dialogue.
   - Reset `loading = false` inside `finally` block to re-enable the input box and send button.

> **Completion criterion**: Frontend widget reads streaming byte chunks via `ReadableStreamDefaultReader` and updates UI state progressively with robust error recovery.

---

## 5. Production Hardening, Environment Guardrails & Deployment

Harden the deployment configuration against credential leakage, cross-origin abuse, and unbounded generation costs.

1. **Secure Credential Injection**:
   - Store `GOOGLE_API_KEY` strictly in Vercel Environment Variables (`Settings -> Environment Variables`).
   - Never commit `.env` files or expose keys in frontend bundles.
2. **Origin Hardening**:
   - Update `Access-Control-Allow-Origin` from development wildcards to the exact production domain where the widget is embedded (e.g. `https://myapp.com`).
3. **Automate GitOps Deployment**:
   - Deploy via Vercel CLI (`vercel --prod`) or configure automatic GitHub main-branch triggers.
   - Verify production deployment with post-deploy `curl -N` checks against the live Vercel URL.
4. **Client-Side Cancellation via AbortController**:
   - Bind an `AbortController` to the fetch request, allowing users to stop streaming midway:
     ```javascript
     const controller = new AbortController();
     // Pass { signal: controller.signal } into fetch()
     // Call controller.abort() when user clicks "Stop"
     ```

> **Completion criterion**: Application deployed to production with locked CORS origin, verified secret injection, and stream cancellation support.

---

## 5-Point Diagnostic Coaching Rubric

| # | Dimension | Diagnostic Question | Passing Standard (Shu Target) | Failing Condition |
|---|---|---|---|---|
| **01** | **Stream Chunking** | Does the backend emit chunks incrementally via `res.write()`? | `generateContentStream()` + `res.write(chunk.text)` | Awaiting full response and returning `res.json()` |
| **02** | **CORS Preflight** | Does the serverless handler handle browser `OPTIONS` preflight requests cleanly? | `if (req.method === 'OPTIONS') return res.status(200).end()` | Unhandled `OPTIONS` resulting in CORS errors or 405 |
| **03** | **Input Sanitization** | Are client message strings and payload objects length-bounded and validated? | `MAX_TEXT_LENGTH` & `MAX_ARRAY_LENGTH` checks + sanitization | Unsanitized client JSON directly concatenated into prompt templates |
| **04** | **Client Stream Reader** | Does the frontend use `ReadableStreamDefaultReader` and `TextDecoder`? | `res.body.getReader()` + `TextDecoder` loop updating assistant message | Calling `res.text()` or `res.json()`, discarding streaming |
| **05** | **Pre-Flight Verification** | Was streaming verified with unbuffered terminal curl before UI wiring? | `curl -N -X POST` with progressive stdout chunk arrival | Wiring UI blindly against untested backend endpoints |

---

## The Visual Brief Specification

When architecting or refactoring Gemini and Vercel streaming chatbots or embedded widgets:
1. **Target Path**: Render an interactive HTML Visual Brief to `%TEMP%\book-to-skill-forge-<timestamp>-gemini-vercel-streaming.html`.
2. **Visual Assets**: Include Tailwind CSS and Mermaid.js diagrams illustrating the plain-text chunk streaming lifecycle, preflight CORS handling, and client stream consumption.
3. **Diagnostic Tables**: Embed the 5-point diagnostic scorecard and anti-pattern defense matrix.
4. **Delivery**: Verify file existence and deliver a clickable link to the user.

---

## Mandatory Checkpoint Gate

Before scaffolding application files, modifying endpoints, or deploying:
1. **Present Implementation Plan**: Author a comprehensive implementation plan artifact detailing the API payload schema, streaming backend architecture, terminal verification plan, and deployment targets.
2. **Set Feedback Header**: Set `RequestFeedback: true` in artifact metadata.
3. **Human Sign-Off Invariant**: STOP and wait for explicit human review and confirmation before modifying codebase or deploying to production.

---

## 6. Deepened Micro-Kernel IoC Architecture & CLI Seams

Following **Rule 49 (Skill-to-IoC Micro-Kernel Seam Elevation Invariant)**, the skill is backed by an authoritative slotted domain engine, typed micro-kernel IoC service seam, domain-partitioned plugin, and headless Click CLI commands:

- **Slotted Domain Engine**: [`gemini_vercel_engine.py`](scripts/gemini_vercel_engine.py) provides pure Python, zero-dependency static code auditing, 3-tier application scaffolding, stream simulation, and HTML visual brief generation.
- **Micro-Kernel Service**: `src/harness/services/gemini_vercel.py` exposes typed `GEMINI_VERCEL_STREAMING_SERVICE_KEY` and `@runtime_checkable` protocol `GeminiVercelStreamingService`.
- **Domain-Partitioned Plugin**: `plugins/integration_and_io/gemini_vercel_streaming_chatbot/` exports singleton `plugin` with zero-fork configuration.
- **Headless Click CLI Commands**:
  - `harness gemini-vercel inspect <target> [--json-output]`
  - `harness gemini-vercel scaffold [--name <name>] [--framework <react|solid|vanilla>] [--language <javascript|typescript>] [--write]`
  - `harness gemini-vercel verify [--prompt <text>] [--chunks <n>] [--json-output]`
  - `harness gemini-vercel brief [--output <path>]`

---

## Anti-Patterns

- **Monolithic Response Blocking** — Awaiting full AI completion and returning single JSON payloads (`res.json()`), causing multi-second blank stalls for users.
- **Missing CORS Preflight Response** — Failing to intercept and return 200 OK on `OPTIONS` preflight requests, breaking cross-domain embed widgets in browsers.
- **Wildcard CORS in Production** — Deploying serverless endpoints with `Access-Control-Allow-Origin: *`, allowing unauthorized origins to exhaust Gemini API quotas.
- **Unsanitized Client Prompt Injection** — Directly interpolating raw, unbounded client JSON or strings into prompt templates without length guards or structure validation.
- **Monolithic Frontend State Replacement** — Using `fetch().then(res => res.json())` on the frontend, nullifying backend streaming gains and causing UI freezes.
- **Hardcoded API Secrets** — Baking Google API keys into frontend code or committing them into serverless source code repositories instead of environment variables.
