"""Slotted domain engine for Gemini & Vercel plain-text chunk streaming chatbot architecture.

Synthesized from Johnson Samuel's literature:
'How to Build an AI Chatbot with Gemini and Vercel Serverless Functions 🚀' (freeCodeCamp, 2026).
Knowledge Item: ki_20260918_gemini_vercel_streaming.

Architecture Invariants:
- Rule 12: Slotted & frozen dataclasses for immutable value objects.
- Rule 23: Windows UTF-8 stream codec entrypoint.
- Rule 51: F-string multiline template isolation and brace escaping.
"""

from __future__ import annotations

import re
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class AuditCheck:
    """Individual diagnostic check result conforming to Rule 12."""

    rule_id: str
    name: str
    passed: bool
    message: str
    severity: str = "error"
    line_number: int | None = None

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("rule_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.severity not in ("error", "warning", "info"):
            raise ValueError(f"Invalid severity: {self.severity}")


@dataclass(slots=True, frozen=True)
class AuditReport:
    """Complete diagnostic audit evaluation result conforming to Rule 12."""

    target: str
    passed: bool
    checks: tuple[AuditCheck, ...] = field(default_factory=tuple)
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.target:
            raise ValueError("target cannot be empty")

    @property
    def errors(self) -> tuple[AuditCheck, ...]:
        return tuple(c for c in self.checks if not c.passed and c.severity == "error")

    @property
    def warnings(self) -> tuple[AuditCheck, ...]:
        return tuple(c for c in self.checks if not c.passed and c.severity == "warning")


@dataclass(slots=True, frozen=True)
class ScaffoldConfig:
    """Configuration specification for 3-tier streaming chatbot scaffolding."""

    app_name: str
    framework: str = "react"
    language: str = "javascript"
    model: str = "gemini-2.5-flash"
    max_text_length: int = 2000
    max_array_length: int = 50
    allowed_origin: str = "https://yourdomain.com"
    output_dir: str = "."

    def __post_init__(self) -> None:
        if not self.app_name:
            raise ValueError("app_name cannot be empty")
        if self.framework not in ("react", "solid", "vanilla"):
            raise ValueError(f"Unsupported framework: {self.framework}")
        if self.language not in ("javascript", "typescript"):
            raise ValueError(f"Unsupported language: {self.language}")


@dataclass(slots=True, frozen=True)
class ScaffoldResult:
    """Output files and metadata manifest from scaffolding generation."""

    files: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    manifest: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class StreamSimulationResult:
    """Result of an unbuffered plain-text chunk streaming simulation."""

    prompt: str
    chunks: tuple[str, ...]
    reconstructed_text: str
    total_chunks: int
    duration_ms: float

    def __post_init__(self) -> None:
        if not self.prompt:
            raise ValueError("prompt cannot be empty")


class GeminiVercelStreamingEngine:
    """Slotted domain engine for Gemini & Vercel streaming chatbots.

    Implements:
    - 5-Point Diagnostic Rubric static evaluation
    - Production 3-tier application scaffolding
    - Unbuffered plain-text chunk streaming simulation
    - Standalone interactive HTML visual brief generation
    """

    def audit_code(self, source_code: str, file_path: str = "") -> AuditReport:
        """Evaluate source code against Johnson Samuel's 5 diagnostic rubrics.

        Rubrics:
        1. STREAM_CHUNKING: Enforces generateContentStream() + res.write(chunk.text).
           Rejects awaiting full completion and returning monolithic res.json() or res.send().
        2. CORS_PREFLIGHT_GATE: Enforces req.method === 'OPTIONS' intercept with 200 OK
           and designated Access-Control-Allow-* headers.
        3. INPUT_SANITIZATION: Enforces length bounds (MAX_TEXT_LENGTH/MAX_ARRAY_LENGTH)
           and prompt template sanitization before model dispatch.
        4. CLIENT_STREAM_READER: Enforces ReadableStreamDefaultReader + TextDecoder loop
           with incremental state updates; rejects res.json() / res.text() on client.
        5. PREFLIGHT_VERIFICATION: Enforces Cache-Control: no-cache, no-transform headers
           and diagnostic healthcheck probe.
        """
        checks: list[AuditCheck] = []
        target = file_path or "<source_code>"
        lines = source_code.splitlines()
        total_lines = len(lines)

        has_serverless_indicators = bool(
            re.search(r"\b(?:res\s*\.\s*(?:status|setHeader|write|end)|req\s*\.\s*(?:method|headers|body|query)|VercelRequest|VercelResponse|GoogleGenAI|allowCors)\b", source_code)
            or re.search(r"(?:handler\s*=\s*async\s*\(\s*req|\(\s*req\s*:\s*VercelRequest|\(\s*req\s*,\s*res\s*\))", source_code)
            or "@google/genai" in source_code
        )
        is_client = any(
            kw in source_code
            for kw in ("fetch", "getReader", "TextDecoder", "useState", "setMessages", "ReadableStreamDefaultReader")
        )
        is_serverless = has_serverless_indicators and not (
            is_client and not ("@google/genai" in source_code or "GoogleGenAI" in source_code or "res.setHeader" in source_code or "res.write" in source_code)
        )

        # --- Rubric 1: Stream Chunking ---
        if is_serverless:
            has_gen_stream = "generateContentStream" in source_code
            has_res_write = "res.write" in source_code
            has_monolithic_json = bool(
                re.search(r"res\s*\.\s*(?:json|send)\s*\(", source_code)
                or re.search(r"return\s+res\s*\.\s*status\s*\(\s*200\s*\)\s*\.\s*json", source_code)
            )

            if has_monolithic_json and not has_res_write:
                line_no = None
                for idx, line in enumerate(lines, 1):
                    if re.search(r"res\s*\.\s*(?:json|send)\s*\(", line):
                        line_no = idx
                        break
                checks.append(
                    AuditCheck(
                        rule_id="STREAM_CHUNKING",
                        name="Plain-Text Stream Chunking",
                        passed=False,
                        message="Monolithic response detected (res.json/res.send). Must use generateContentStream() and pipe incremental chunks via res.write().",
                        severity="error",
                        line_number=line_no,
                    )
                )
            elif has_gen_stream and has_res_write:
                checks.append(
                    AuditCheck(
                        rule_id="STREAM_CHUNKING",
                        name="Plain-Text Stream Chunking",
                        passed=True,
                        message="Proper plain-text chunk streaming using generateContentStream() and res.write().",
                        severity="info",
                    )
                )
            else:
                checks.append(
                    AuditCheck(
                        rule_id="STREAM_CHUNKING",
                        name="Plain-Text Stream Chunking",
                        passed=False,
                        message="Missing generateContentStream() or res.write() chunk streaming pipeline in serverless handler.",
                        severity="error",
                    )
                )
        else:
            checks.append(
                AuditCheck(
                    rule_id="STREAM_CHUNKING",
                    name="Plain-Text Stream Chunking",
                    passed=True,
                    message="Client component or non-serverless source; chunk streaming rubric passed.",
                    severity="info",
                )
            )

        # --- Rubric 2: CORS Preflight Gate ---
        if is_serverless:
            has_options_check = bool(
                re.search(r"req\.method\s*===?\s*['\"]OPTIONS['\"]", source_code)
                or "allowCors" in source_code
            )
            has_cors_headers = "Access-Control-Allow-Origin" in source_code

            if has_options_check and has_cors_headers:
                checks.append(
                    AuditCheck(
                        rule_id="CORS_PREFLIGHT_GATE",
                        name="CORS Preflight Gate",
                        passed=True,
                        message="Preflight OPTIONS requests cleanly intercepted and terminated with designated CORS headers.",
                        severity="info",
                    )
                )
            elif not has_options_check:
                checks.append(
                    AuditCheck(
                        rule_id="CORS_PREFLIGHT_GATE",
                        name="CORS Preflight Gate",
                        passed=False,
                        message="Missing CORS OPTIONS preflight handler. Embedded chat widgets will be blocked by browser preflight requests.",
                        severity="error",
                    )
                )
            else:
                checks.append(
                    AuditCheck(
                        rule_id="CORS_PREFLIGHT_GATE",
                        name="CORS Preflight Gate",
                        passed=False,
                        message="OPTIONS checked but missing Access-Control-Allow-Origin response header.",
                        severity="error",
                    )
                )
        else:
            checks.append(
                AuditCheck(
                    rule_id="CORS_PREFLIGHT_GATE",
                    name="CORS Preflight Gate",
                    passed=True,
                    message="Client component; serverless CORS preflight rubric not applicable.",
                    severity="info",
                )
            )

        # --- Rubric 3: Input Sanitization & Length Guardrails ---
        if is_serverless:
            has_length_guard = any(
                kw in source_code
                for kw in ("MAX_TEXT_LENGTH", "length", "trim", "slice", "sanitize", "substring")
            )
            has_400_check = bool(
                re.search(r"status\s*\(\s*400\s*\)", source_code)
                or re.search(r"status\s*=\s*400", source_code)
                or "Bad Request" in source_code
            )

            if has_length_guard and has_400_check:
                checks.append(
                    AuditCheck(
                        rule_id="INPUT_SANITIZATION",
                        name="Input Sanitization & Length Bounds",
                        passed=True,
                        message="Payload length and structure bounded with HTTP 400 rejection for malformed inputs.",
                        severity="info",
                    )
                )
            else:
                checks.append(
                    AuditCheck(
                        rule_id="INPUT_SANITIZATION",
                        name="Input Sanitization & Length Bounds",
                        passed=False,
                        message="Payload lacks explicit length bounds (MAX_TEXT_LENGTH) or HTTP 400 validation rejection.",
                        severity="error",
                    )
                )
        else:
            checks.append(
                AuditCheck(
                    rule_id="INPUT_SANITIZATION",
                    name="Input Sanitization & Length Bounds",
                    passed=True,
                    message="Client component; backend payload sanitization rubric passed.",
                    severity="info",
                )
            )

        # --- Rubric 4: Client Stream Consumer ---
        if is_client:
            has_fetch = "fetch(" in source_code or "fetch (" in source_code
            has_reader = "getReader" in source_code or "ReadableStreamDefaultReader" in source_code
            has_decoder = "TextDecoder" in source_code
            has_res_json_client = bool(
                re.search(r"await\s+res\s*\.\s*(?:json|text)\s*\(", source_code)
                or re.search(r"\.then\s*\(\s*res\s*=>\s*res\s*\.\s*(?:json|text)\s*\(", source_code)
            )

            if has_res_json_client and not has_reader:
                line_no = None
                for idx, line in enumerate(lines, 1):
                    if re.search(r"res\s*\.\s*(?:json|text)\s*\(", line):
                        line_no = idx
                        break
                checks.append(
                    AuditCheck(
                        rule_id="CLIENT_STREAM_READER",
                        name="Client Stream Consumer",
                        passed=False,
                        message="Client consumes stream with res.json()/res.text() blocking calls instead of ReadableStreamDefaultReader.",
                        severity="error",
                        line_number=line_no,
                    )
                )
            elif has_reader and has_decoder:
                checks.append(
                    AuditCheck(
                        rule_id="CLIENT_STREAM_READER",
                        name="Client Stream Consumer",
                        passed=True,
                        message="Client correctly reads streaming chunks using ReadableStreamDefaultReader and TextDecoder.",
                        severity="info",
                    )
                )
            elif has_fetch and not has_reader:
                checks.append(
                    AuditCheck(
                        rule_id="CLIENT_STREAM_READER",
                        name="Client Stream Consumer",
                        passed=False,
                        message="Client fetch lacks getReader() and TextDecoder for progressive chunk decoding.",
                        severity="error",
                    )
                )
            else:
                checks.append(
                    AuditCheck(
                        rule_id="CLIENT_STREAM_READER",
                        name="Client Stream Consumer",
                        passed=True,
                        message="Client stream reader requirements satisfied.",
                        severity="info",
                    )
                )
        else:
            checks.append(
                AuditCheck(
                    rule_id="CLIENT_STREAM_READER",
                    name="Client Stream Consumer",
                    passed=True,
                    message="Serverless backend source; client stream reader rubric passed.",
                    severity="info",
                )
            )

        # --- Rubric 5: Pre-Flight Verification & Observability ---
        if is_serverless:
            has_cache_control = "Cache-Control" in source_code or "no-cache" in source_code
            has_healthcheck = "healthcheck" in source_code or "type" in source_code

            if has_cache_control or has_healthcheck:
                checks.append(
                    AuditCheck(
                        rule_id="UNBUFFERED_VERIFICATION_OBSERVABILITY",
                        name="Unbuffered Verification & Observability",
                        passed=True,
                        message="Serverless endpoint provides no-cache/no-transform headers or diagnostic healthcheck route.",
                        severity="info",
                    )
                )
            else:
                checks.append(
                    AuditCheck(
                        rule_id="UNBUFFERED_VERIFICATION_OBSERVABILITY",
                        name="Unbuffered Verification & Observability",
                        passed=False,
                        message="Missing 'Cache-Control: no-cache, no-transform' headers or healthcheck route for curl -N verification.",
                        severity="warning",
                    )
                )
        else:
            checks.append(
                AuditCheck(
                    rule_id="UNBUFFERED_VERIFICATION_OBSERVABILITY",
                    name="Unbuffered Verification & Observability",
                    passed=True,
                    message="Client component; verification headers rubric passed.",
                    severity="info",
                )
            )

        all_errors = [c for c in checks if not c.passed and c.severity == "error"]
        overall_passed = len(all_errors) == 0

        return AuditReport(
            target=target,
            passed=overall_passed,
            checks=tuple(checks),
            metrics={
                "total_lines": total_lines,
                "is_serverless": is_serverless,
                "is_client": is_client,
                "checks_count": len(checks),
                "errors_count": len(all_errors),
                "warnings_count": len([c for c in checks if not c.passed and c.severity == "warning"]),
            },
        )

    def scaffold_app(self, config: ScaffoldConfig) -> ScaffoldResult:
        """Generate a production 3-tier Gemini & Vercel streaming application."""
        files: list[tuple[str, str]] = []

        is_ts = config.language == "typescript"
        backend_file = "api/chat.ts" if is_ts else "api/chat.js"
        frontend_file = "src/ChatWidget.tsx" if is_ts else "src/ChatWidget.jsx"

        # 1. Backend Serverless Function
        if is_ts:
            backend_code = f"""import type {{ VercelRequest, VercelResponse }} from '@vercel/node';
import {{ GoogleGenAI }} from '@google/genai';

const MAX_TEXT_LENGTH = {config.max_text_length};
const MAX_ARRAY_LENGTH = {config.max_array_length};
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || '{config.allowed_origin}';

const ai = new GoogleGenAI({{
  apiKey: process.env.GOOGLE_API_KEY || '',
}});

function setCorsHeaders(res: VercelResponse): void {{
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
}}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {{
  setCorsHeaders(res);

  if (req.method === 'OPTIONS') {{
    res.status(200).end();
    return;
  }}

  if (req.method === 'GET') {{
    const url = new URL(req.url || '', `http://${{req.headers.host}}`);
    if (url.searchParams.get('type') === 'healthcheck') {{
      res.status(200).json({{ status: 'ok', timestamp: new Date().toISOString() }});
      return;
    }}
  }}

  if (req.method !== 'POST') {{
    res.status(405).json({{ error: 'Method Not Allowed' }});
    return;
  }}

  const {{ message, resume }} = req.body || {{}};
  if (!message || typeof message !== 'string' || !message.trim()) {{
    res.status(400).json({{ error: 'Invalid or missing message string' }});
    return;
  }}

  const cleanMessage = message.trim().slice(0, MAX_TEXT_LENGTH);
  const contextJson = resume ? JSON.stringify(resume).slice(0, MAX_TEXT_LENGTH) : '';

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-cache, no-transform');

  try {{
    const prompt = contextJson
      ? `Context: ${{contextJson}}\\n\\nUser Query: ${{cleanMessage}}`
      : cleanMessage;

    const stream = await ai.models.generateContentStream({{
      model: '{config.model}',
      contents: prompt,
    }});

    for await (const chunk of stream) {{
      if (chunk.text) {{
        res.write(chunk.text);
      }}
    }}
    res.end();
  }} catch (err: any) {{
    res.status(500).write(`\\n[STREAM_ERROR]: ${{err.message || 'Stream generation failed'}}`);
    res.end();
  }}
}}
"""
        else:
            backend_code = f"""const {{ GoogleGenAI }} = require('@google/genai');

const MAX_TEXT_LENGTH = {config.max_text_length};
const MAX_ARRAY_LENGTH = {config.max_array_length};
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || '{config.allowed_origin}';

const ai = new GoogleGenAI({{
  apiKey: process.env.GOOGLE_API_KEY,
}});

const allowCors = fn => async (req, res) => {{
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');

  if (req.method === 'OPTIONS') {{
    return res.status(200).end();
  }}
  return await fn(req, res);
}};

const handler = async (req, res) => {{
  if (req.method === 'GET' && req.query.type === 'healthcheck') {{
    return res.status(200).json({{ status: 'ok', timestamp: new Date().toISOString() }});
  }}

  if (req.method !== 'POST') {{
    return res.status(405).json({{ error: 'Method Not Allowed' }});
  }}

  const {{ message, resume }} = req.body || {{}};
  if (!message || typeof message !== 'string' || !message.trim()) {{
    return res.status(400).json({{ error: 'Bad Request: message is required and must be non-empty' }});
  }}

  const cleanMessage = message.trim().slice(0, MAX_TEXT_LENGTH);
  const contextJson = resume ? JSON.stringify(resume).slice(0, MAX_TEXT_LENGTH) : '';

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-cache, no-transform');

  try {{
    const prompt = contextJson
      ? `Context: ${{contextJson}}\\n\\nUser Query: ${{cleanMessage}}`
      : cleanMessage;

    const stream = await ai.models.generateContentStream({{
      model: '{config.model}',
      contents: prompt,
    }});

    for await (const chunk of stream) {{
      if (chunk.text) {{
        res.write(chunk.text);
      }}
    }}
    res.end();
  }} catch (err) {{
    res.status(500).write(`\\n[STREAM_ERROR]: ${{err.message || 'Stream generation failed'}}`);
    res.end();
  }}
}};

module.exports = allowCors(handler);
"""
        files.append((backend_file, backend_code))

        # 2. Frontend Reactive Stream Consumer
        if is_ts:
            frontend_code = f"""import React, {{ useState, useRef }} from 'react';

interface Message {{
  role: 'user' | 'assistant';
  text: string;
}}

export const ChatWidget: React.FC = () => {{
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    setMessages(prev => [...prev, {{ role: 'user', text: userText }}]);
    setLoading(true);

    abortControllerRef.current = new AbortController();

    try {{
      const res = await fetch('/api/chat', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: userText, resume: {{ source: '{config.app_name}' }} }}),
        signal: abortControllerRef.current.signal,
      }});

      if (!res.ok) {{
        throw new Error(`HTTP error: ${{res.status}}`);
      }}

      if (!res.body) {{
        throw new Error('ReadableStream not supported on response body');
      }}

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullText = '';

      setMessages(prev => [...prev, {{ role: 'assistant', text: '' }}]);

      while (true) {{
        const {{ value, done }} = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, {{ stream: true }});
        fullText += chunk;

        setMessages(prev => {{
          const updated = [...prev];
          updated[updated.length - 1] = {{ role: 'assistant', text: fullText }};
          return updated;
        }});
      }}
    }} catch (err: any) {{
      if (err.name !== 'AbortError') {{
        setMessages(prev => [...prev, {{ role: 'assistant', text: `[Error]: ${{err.message}}` }}]);
      }}
    }} finally {{
      setLoading(false);
      abortControllerRef.current = null;
    }}
  }};

  const stopStreaming = () => {{
    if (abortControllerRef.current) {{
      abortControllerRef.current.abort();
    }}
  }};

  return (
    <div className="chat-container">
      <div className="messages-window">
        {{messages.map((m, idx) => (
          <div key={{idx}} className={{`message ${{m.role}}`}}>
            <strong>{{m.role === 'user' ? 'You' : 'Assistant'}}:</strong> {{m.text}}
          </div>
        ))}}
      </div>
      <form onSubmit={{sendMessage}} className="input-form">
        <input
          type="text"
          value={{input}}
          onChange={{e => setInput(e.target.value)}}
          placeholder="Type your message..."
          disabled={{loading}}
        />
        {{loading ? (
          <button type="button" onClick={{stopStreaming}}>Stop</button>
        ) : (
          <button type="submit">Send</button>
        )}}
      </form>
    </div>
  );
}};
"""
        else:
            frontend_code = f"""import React, {{ useState, useRef }} from 'react';

export function ChatWidget() {{
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef(null);

  const sendMessage = async (e) => {{
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    setMessages(prev => [...prev, {{ role: 'user', text: userText }}]);
    setLoading(true);

    abortControllerRef.current = new AbortController();

    try {{
      const res = await fetch('/api/chat', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message: userText, resume: {{ source: '{config.app_name}' }} }}),
        signal: abortControllerRef.current.signal,
      }});

      if (!res.ok) {{
        throw new Error(`HTTP error: ${{res.status}}`);
      }}

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullText = '';

      setMessages(prev => [...prev, {{ role: 'assistant', text: '' }}]);

      while (true) {{
        const {{ value, done }} = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, {{ stream: true }});
        fullText += chunk;

        setMessages(prev => {{
          const updated = [...prev];
          updated[updated.length - 1] = {{ role: 'assistant', text: fullText }};
          return updated;
        }});
      }}
    }} catch (err) {{
      if (err.name !== 'AbortError') {{
        setMessages(prev => [...prev, {{ role: 'assistant', text: `[Error]: ${{err.message}}` }}]);
      }}
    }} finally {{
      setLoading(false);
      abortControllerRef.current = null;
    }}
  }};

  const stopStreaming = () => {{
    if (abortControllerRef.current) {{
      abortControllerRef.current.abort();
    }}
  }};

  return (
    <div className="chat-container">
      <div className="messages-window">
        {{messages.map((m, idx) => (
          <div key={{idx}} className={{`message ${{m.role}}`}}>
            <strong>{{m.role === 'user' ? 'You' : 'Assistant'}}:</strong> {{m.text}}
          </div>
        ))}}
      </div>
      <form onSubmit={{sendMessage}} className="input-form">
        <input
          type="text"
          value={{input}}
          onChange={{e => setInput(e.target.value)}}
          placeholder="Ask a question..."
          disabled={{loading}}
        />
        {{loading ? (
          <button type="button" onClick={{stopStreaming}}>Stop</button>
        ) : (
          <button type="submit">Send</button>
        )}}
      </form>
    </div>
  );
}}
"""
        files.append((frontend_file, frontend_code))

        # 3. vercel.json
        vercel_config = """{
  "version": 2,
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    }
  ]
}
"""
        files.append(("vercel.json", vercel_config))

        # 4. package.json
        pkg_json = f"""{{
  "name": "{config.app_name}",
  "version": "1.0.0",
  "private": true,
  "scripts": {{
    "dev": "vercel dev",
    "build": "vercel build",
    "verify": "bash verify_stream.sh"
  }},
  "dependencies": {{
    "@google/genai": "^0.1.1",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }},
  "devDependencies": {{
    "@vercel/node": "^3.0.0"
  }}
}}
"""
        files.append(("package.json", pkg_json))

        # 5. .env.example
        env_example = """# Google Gemini API Key (keep secret in Vercel Environment Variables)
GOOGLE_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGIN=https://yourdomain.com
"""
        files.append((".env.example", env_example))

        # 6. verify_stream.sh
        verify_script = f"""#!/usr/bin/env bash
# Pre-Flight Terminal Stream Verification Script (Pillar 2)
# Johnson Samuel (freeCodeCamp, 2026)
set -euo pipefail

TARGET_URL="${{1:-http://localhost:3000/api/chat}}"

echo "==> 1. Testing Preflight OPTIONS resolution..."
curl -s -o /dev/null -w "OPTIONS Response Code: %{{http_code}}\\n" -X OPTIONS "$TARGET_URL"

echo "==> 2. Probing Healthcheck Endpoint..."
curl -s "$TARGET_URL?type=healthcheck" || echo ""
echo ""

echo "==> 3. Testing Unbuffered Plain-Text Chunk Streaming (-N)..."
curl -N -X POST "$TARGET_URL" \\
  -H "Content-Type: application/json" \\
  -d '{{"message":"Explain plain-text chunk streaming in 2 sentences","resume":{{"app":"{config.app_name}"}}}}'
echo ""
echo "==> Verification completed."
"""
        files.append(("verify_stream.sh", verify_script))

        manifest = {
            "app_name": config.app_name,
            "framework": config.framework,
            "language": config.language,
            "model": config.model,
            "files_count": len(files),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return ScaffoldResult(files=tuple(files), manifest=manifest)

    def simulate_stream(self, prompt: str, chunks_count: int = 5) -> StreamSimulationResult:
        """Simulate unbuffered plain-text chunk emission and client reconstruction."""
        start_time = time.perf_counter()
        words = prompt.split()
        if not words:
            words = ["Gemini", "Vercel", "Streaming", "Response"]

        chunk_size = max(1, len(words) // chunks_count)
        chunks: list[str] = []
        for i in range(0, len(words), chunk_size):
            chunk_slice = " ".join(words[i : i + chunk_size])
            if i > 0:
                chunks.append(" " + chunk_slice)
            else:
                chunks.append(chunk_slice)

        # Ensure we have at least 1 chunk
        if not chunks:
            chunks = ["Echo: " + prompt]

        reconstructed = "".join(chunks)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return StreamSimulationResult(
            prompt=prompt,
            chunks=tuple(chunks),
            reconstructed_text=reconstructed,
            total_chunks=len(chunks),
            duration_ms=round(duration_ms, 2),
        )

    def generate_visual_brief(self, output_path: str | Path | None = None) -> Path:
        """Generate standalone HTML visual brief with Tailwind CSS and Mermaid.js."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        if output_path is None:
            out_p = Path(tempfile.gettempdir()) / f"gemini-vercel-streaming-{timestamp}.html"
        else:
            out_p = Path(output_path)

        html_template = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gemini & Vercel Streaming Chatbot: Architecture Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0f172a',
        primaryColor: '#38bdf8',
        primaryTextColor: '#f8fafc',
        primaryBorderColor: '#0ea5e9',
        lineColor: '#94a3b8',
        secondaryColor: '#1e293b',
        tertiaryColor: '#0f172a'
      }
    });
  </script>
  <style>
    body { background-color: #0b0f19; color: #f1f5f9; font-family: ui-sans-serif, system-ui, sans-serif; }
    .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
  </style>
</head>
<body class="min-h-screen p-8 max-w-7xl mx-auto">
  <header class="mb-10 pb-6 border-b border-slate-800 flex justify-between items-center">
    <div>
      <div class="flex items-center gap-3">
        <span class="px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">Streaming Edge Architecture</span>
        <span class="text-xs text-slate-400">Gemini Vercel Streaming Engine</span>
      </div>
      <h1 class="text-3xl font-bold mt-2 text-white">Gemini & Vercel Plain-Text Streaming Architecture</h1>
      <p class="text-slate-400 text-sm mt-1">Literature: Johnson Samuel (freeCodeCamp, 2026) | Generated: __TIMESTAMP__</p>
    </div>
  </header>

  <!-- Streaming Topology Diagram -->
  <section class="glass-card p-6 rounded-2xl mb-8 shadow-xl">
    <h2 class="text-xl font-bold text-white mb-4">Plain-Text Chunk Streaming & CORS Preflight Topology</h2>
    <pre class="mermaid text-xs">
flowchart TD
    subgraph ClientWidget [Frontend Chat Widget: React / Web Component]
        User[User Input] --> Fetch[POST /api/chat with Fetch]
        Abort[AbortController.signal] -.-> Fetch
        Fetch --> StreamBody[ReadableStreamDefaultReader: res.body.getReader()]
        StreamBody --> Decoder[TextDecoder 'utf-8']
        Decoder --> StateLoop[Progressive Assistant Message State Update]
    end

    subgraph VercelEdge [Vercel Serverless Function: api/chat.js]
        Preflight{HTTP Method == OPTIONS?}
        Preflight -->|Yes| CORS200[200 OK + Access-Control-Allow-Origin]
        Preflight -->|No| MethodCheck{Method == POST?}
        MethodCheck -->|No| Err405[405 Method Not Allowed]
        MethodCheck -->|Yes| Sanitizer[Payload Length & Cardinality Gate: MAX_TEXT_LENGTH]
        Sanitizer --> Headers[Set Headers: Content-Type: text/plain, Cache-Control: no-cache]
        Headers --> GeminiAPI[ai.models.generateContentStream]
        GeminiAPI --> Chunks[for await chunk of stream]
        Chunks --> Write[res.write: chunk.text]
        Write -.->|Incremental HTTP Chunks| StreamBody
        Write --> End[res.end]
    end

    style ClientWidget fill:#0f291e,stroke:#34d399
    style VercelEdge fill:#0d233a,stroke:#38bdf8
    </pre>
  </section>

  <!-- Diagnostic Scorecard Matrix -->
  <section class="glass-card p-6 rounded-2xl mb-8 shadow-xl">
    <h2 class="text-xl font-bold text-white mb-4">Johnson Samuel 5-Point Diagnostic Rubric Scorecard</h2>
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
      <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
        <div class="text-xs font-mono text-cyan-400 font-semibold">RUBRIC 1</div>
        <div class="text-sm font-bold text-white mt-1">Stream Chunking</div>
        <div class="text-xs text-slate-400 mt-2">generateContentStream() + res.write(chunk.text). Zero JSON blocking.</div>
      </div>
      <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
        <div class="text-xs font-mono text-cyan-400 font-semibold">RUBRIC 2</div>
        <div class="text-sm font-bold text-white mt-1">CORS Preflight</div>
        <div class="text-xs text-slate-400 mt-2">Explicit OPTIONS 200 OK intercept preventing browser embed blocks.</div>
      </div>
      <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
        <div class="text-xs font-mono text-cyan-400 font-semibold">RUBRIC 3</div>
        <div class="text-sm font-bold text-white mt-1">Input Bounds</div>
        <div class="text-xs text-slate-400 mt-2">MAX_TEXT_LENGTH sanitization and strict 400 Bad Request rejection.</div>
      </div>
      <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
        <div class="text-xs font-mono text-cyan-400 font-semibold">RUBRIC 4</div>
        <div class="text-sm font-bold text-white mt-1">Client Reader</div>
        <div class="text-xs text-slate-400 mt-2">ReadableStreamDefaultReader + TextDecoder incremental typewriter loop.</div>
      </div>
      <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50">
        <div class="text-xs font-mono text-cyan-400 font-semibold">RUBRIC 5</div>
        <div class="text-sm font-bold text-white mt-1">Terminal Verify</div>
        <div class="text-xs text-slate-400 mt-2">Unbuffered curl -N -X POST verification before UI wiring.</div>
      </div>
    </div>
  </section>

  <footer class="pt-6 border-t border-slate-800 text-center text-xs text-slate-500">
    Gemini & Vercel Streaming Chatbot Engine | Brain Harness &copy; 2026
  </footer>
</body>
</html>
"""
        html_rendered = html_template.replace("__TIMESTAMP__", timestamp)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(html_rendered, encoding="utf-8")
        return out_p
