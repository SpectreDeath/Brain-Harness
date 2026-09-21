┌─────────────────────────────────────────────────────────────┐
│ SKILL: gemini-vercel-streaming-chatbot                      │
├─────────────────────────────────────────────────────────────┤
│ DESCRIPTION: Production Gemini streaming chatbots on Vercel │
│ Serverless with CORS preflight & React stream consumers     │
└─────────────────────────────────────────────────────────────┘

## Stage Progression Matrix

| Stage | Focus Area | Core Mechanism | Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. API Contract** | Schema & Bounds | Strict JSON schema, length bounding, input sanitization | Invalid payloads rejected with 400 Bad Request |
| **2. Serverless Backend**| HTTP Chunk Streaming| `@google/genai`, `res.write()`, `allowCors` preflight wrapper | Incremental plain-text stream active on `/api/chat` |
| **3. Terminal Verify** | Pipeline Validation | Unbuffered terminal `curl -N -X POST` verification | Incremental token emission verified before UI wiring |
| **4. Stream Consumer** | Reactive Client UI | `ReadableStreamDefaultReader`, `TextDecoder`, state loop | Smooth real-time typewriter effect in UI widget |
| **5. Production Deploy**| Security & Scale | Vercel Environment Variables, origin lockdown, GitOps | Live production endpoint verified with zero secrets |

---

## Three Pillars Cheat Sheet

### Pillar 1: Plain-Text Chunk Streaming Backend
- **Stream Over Batch**: Always call `ai.models.generateContentStream()` and pipe chunks with `res.write(chunk.text)`.
- **Stream Headers**: Configure `Content-Type: text/plain; charset=utf-8` and `Cache-Control: no-cache, no-transform`.
- **Preflight Gate**: Intercept `req.method === 'OPTIONS'` inside CORS wrapper and return `res.status(200).end()`.

### Pillar 2: Pre-UI Terminal Verification
- **Unbuffered Curl**: Always verify backend streaming via `curl -N -X POST` before writing frontend components.
- **Buffer Detection**: If output arrives in a single burst, check intermediate CDN proxies or missing `no-cache` headers.
- **Healthcheck Probe**: Provide a lightweight `GET /api/chat?type=healthcheck` route for uptime checks.

### Pillar 3: Reactive Client Reader Loop
- **Stream Reader**: Obtain `ReadableStreamDefaultReader` via `res.body.getReader()`.
- **TextDecoder**: Decode incoming byte chunks with `new TextDecoder()`.
- **Functional State Updates**: Accumulate `fullText += chunk` and update the last assistant message progressively.
- **Safe Teardown**: Reset loading flags in `finally` and provide `AbortController` cancellation for in-flight streams.

---

## Verification Checklist

- [ ] Frontmatter description bounded between 100 and 350 characters with action verbs and negative boundary.
- [ ] Serverless handler implements `res.write()` chunk streaming rather than monolithic `res.json()`.
- [ ] Preflight `OPTIONS` requests handled with explicit 200 OK and designated allowed origins.
- [ ] Terminal verification with `curl -N -X POST` executed before frontend consumer integration.
- [ ] Frontend uses `res.body.getReader()` with `TextDecoder` for incremental state updates.
- [ ] Google API key injected via `process.env.GOOGLE_API_KEY` with zero client-side credential exposure.
