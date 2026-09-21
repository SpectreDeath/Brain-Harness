"""Comprehensive test suite for deepened Gemini & Vercel Streaming Chatbot architecture.

Covers:
- Slotted frozen dataclass immutability (Rule 12 & Rule 43)
- Static analysis across Johnson Samuel's 5 diagnostic rubrics:
  1. Plain-Text Stream Chunking
  2. CORS Preflight Gate
  3. Input Sanitization & Cardinality Bounds
  4. Client Stream Consumer (ReadableStreamDefaultReader + TextDecoder)
  5. Unbuffered Verification & Observability
- Production 3-tier scaffolding and manifest generation
- Unbuffered stream chunking simulation
- Micro-Kernel IoC ServiceKey registration and resolution (Rule 2 & Rule 49)
- PluginValidator compliance and zero-fork configuration (Rule 34, 38, 44, 45)
- Click CLI commands via CliRunner (Rule 6, 10, 23)
- Canonical Knowledge Vault dual-file format (Rule 40)
- Standalone HTML visual brief generation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "gemini-vercel-streaming-chatbot" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from gemini_vercel_engine import (
    AuditCheck,
    AuditReport,
    GeminiVercelStreamingEngine,
    ScaffoldConfig,
    ScaffoldResult,
    StreamSimulationResult,
)

from harness.commands.gemini_vercel import gemini_vercel_group
from harness.creator.skills import SkillValidator
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.gemini_vercel import (
    GEMINI_VERCEL_STREAMING_SERVICE_KEY,
    AuditReportData,
    GeminiVercelStreamingService,
    ScaffoldConfigData,
    StreamSimulationData,
)
from plugins.integration_and_io.gemini_vercel_streaming_chatbot.main import (
    GeminiVercelStreamingPlugin,
)
from plugins.integration_and_io.gemini_vercel_streaming_chatbot.main import (
    plugin as streaming_plugin,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import (
    SkillCardParser,
)


@pytest.fixture
def engine() -> GeminiVercelStreamingEngine:
    return GeminiVercelStreamingEngine()


@pytest.fixture
def service_context() -> ServiceContext:
    ctx = ServiceContext()
    ctx.provide(GEMINI_VERCEL_STREAMING_SERVICE_KEY, streaming_plugin)
    return ctx


# --- 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43) ---


def test_frozen_dataclass_immutability():
    """Verify slotted & frozen dataclasses prevent attribute mutation (Rule 12 & Rule 43)."""
    check = AuditCheck(
        rule_id="RULE_01",
        name="Test Check",
        passed=True,
        message="All good",
        severity="info",
    )
    with pytest.raises((AttributeError, TypeError)):
        check.passed = False  # type: ignore

    report = AuditReport(
        target="test.js",
        passed=True,
        checks=(check,),
    )
    with pytest.raises((AttributeError, TypeError)):
        report.passed = False  # type: ignore

    cfg = ScaffoldConfig(
        app_name="demo_bot",
    )
    with pytest.raises((AttributeError, TypeError)):
        cfg.app_name = "other_bot"  # type: ignore

    res = ScaffoldResult(
        files=(("api/chat.js", "content"),),
    )
    with pytest.raises((AttributeError, TypeError)):
        res.files = ()  # type: ignore

    sim = StreamSimulationResult(
        prompt="Hello world",
        chunks=("Hello", " world"),
        reconstructed_text="Hello world",
        total_chunks=2,
        duration_ms=1.5,
    )
    with pytest.raises((AttributeError, TypeError)):
        sim.prompt = "other"  # type: ignore


# --- 2. Diagnostic Rubrics & Static Analysis ---


def test_audit_clean_serverless_handler_passes(engine: GeminiVercelStreamingEngine):
    """Verify clean serverless chunk streaming handler passes all rubrics."""
    clean_code = """
const { GoogleGenAI } = require('@google/genai');

const MAX_TEXT_LENGTH = 2000;
const ALLOWED_ORIGIN = 'https://app.com';
const ai = new GoogleGenAI({ apiKey: process.env.GOOGLE_API_KEY });

const allowCors = fn => async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', ALLOWED_ORIGIN);
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  return await fn(req, res);
};

const handler = async (req, res) => {
  if (req.query && req.query.type === 'healthcheck') {
    return res.status(200).json({ status: 'ok' });
  }
  const { message } = req.body || {};
  if (!message || message.trim().length === 0) {
    return res.status(400).json({ error: 'Bad Request' });
  }
  const cleanMessage = message.trim().slice(0, MAX_TEXT_LENGTH);
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-cache, no-transform');

  const stream = await ai.models.generateContentStream({
    model: 'gemini-2.5-flash',
    contents: cleanMessage
  });
  for await (const chunk of stream) {
    if (chunk.text) res.write(chunk.text);
  }
  res.end();
};
module.exports = allowCors(handler);
"""
    report = engine.audit_code(clean_code, file_path="api/chat.js")
    assert report.passed is True
    assert len(report.errors) == 0


def test_audit_detects_monolithic_json_blocking(engine: GeminiVercelStreamingEngine):
    """Verify Rubric 1 flags awaiting full response and returning res.json()."""
    bad_code = """
const { GoogleGenAI } = require('@google/genai');
const handler = async (req, res) => {
  const { message } = req.body;
  const result = await ai.models.generateContent({ model: 'gemini-2.5-flash', contents: message });
  // Monolithic JSON response blocks stream
  return res.status(200).json({ reply: result.text });
};
"""
    report = engine.audit_code(bad_code, file_path="monolithic.js")
    assert report.passed is False
    assert any(c.rule_id == "STREAM_CHUNKING" for c in report.errors)


def test_audit_detects_missing_cors_preflight(engine: GeminiVercelStreamingEngine):
    """Verify Rubric 2 flags missing OPTIONS preflight intercept."""
    bad_code = """
const handler = async (req, res) => {
  // Missing req.method === 'OPTIONS' preflight handling
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'Missing' });
  res.setHeader('Content-Type', 'text/plain');
  res.setHeader('Cache-Control', 'no-cache');
  const stream = await ai.models.generateContentStream({ contents: message });
  for await (const chunk of stream) res.write(chunk.text);
  res.end();
};
"""
    report = engine.audit_code(bad_code, file_path="no_cors.js")
    assert report.passed is False
    assert any(c.rule_id == "CORS_PREFLIGHT_GATE" for c in report.errors)


def test_audit_detects_missing_input_bounds(engine: GeminiVercelStreamingEngine):
    """Verify Rubric 3 flags unconstrained input payloads and missing 400 rejection."""
    bad_code = """
const allowCors = fn => async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();
  return await fn(req, res);
};
const handler = async (req, res) => {
  // Directly using req.body without validation or length bounds
  const prompt = req.body.message;
  res.setHeader('Content-Type', 'text/plain');
  res.setHeader('Cache-Control', 'no-cache');
  const stream = await ai.models.generateContentStream({ contents: prompt });
  for await (const chunk of stream) res.write(chunk.text);
  res.end();
};
"""
    report = engine.audit_code(bad_code, file_path="unbounded.js")
    assert report.passed is False
    assert any(c.rule_id == "INPUT_SANITIZATION" for c in report.errors)


def test_audit_detects_client_stream_blocking(engine: GeminiVercelStreamingEngine):
    """Verify Rubric 4 flags client widget awaiting res.json() instead of getReader()."""
    bad_code = """
import React, { useState } from 'react';

export function Chat() {
  const [messages, setMessages] = useState([]);
  const sendMessage = async (msg) => {
    const res = await fetch('/api/chat', { method: 'POST', body: JSON.stringify({ message: msg }) });
    // Anti-pattern: awaiting full text or json, defeating chunk streaming
    const data = await res.json();
    setMessages(prev => [...prev, data]);
  };
  return <div>Chat</div>;
}
"""
    report = engine.audit_code(bad_code, file_path="Chat.jsx")
    assert report.passed is False
    assert any(c.rule_id == "CLIENT_STREAM_READER" for c in report.errors)


def test_audit_clean_client_stream_reader_passes(engine: GeminiVercelStreamingEngine):
    """Verify client widget using ReadableStreamDefaultReader and TextDecoder passes."""
    clean_client = """
import React, { useState } from 'react';

export function ChatWidget() {
  const [messages, setMessages] = useState([]);
  const sendMessage = async (userText) => {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText })
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullText = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
      setMessages(prev => [...prev, { text: fullText }]);
    }
  };
  return <div>Widget</div>;
}
"""
    report = engine.audit_code(clean_client, file_path="ChatWidget.jsx")
    assert report.passed is True
    assert len(report.errors) == 0


# --- 3. Production Scaffolding & Manifest Generation ---


def test_scaffolder_generates_all_layers(engine: GeminiVercelStreamingEngine):
    """Verify 3-tier scaffolding generates backend, frontend, vercel config, and test script."""
    cfg = ScaffoldConfig(
        app_name="customer_support_bot",
        framework="react",
        language="javascript",
        model="gemini-2.5-flash",
    )
    result = engine.scaffold_app(cfg)
    file_map = dict(result.files)

    assert "api/chat.js" in file_map
    assert "src/ChatWidget.jsx" in file_map
    assert "vercel.json" in file_map
    assert "package.json" in file_map
    assert ".env.example" in file_map
    assert "verify_stream.sh" in file_map

    # Check backend content
    assert "generateContentStream" in file_map["api/chat.js"]
    assert "res.write(chunk.text)" in file_map["api/chat.js"]
    assert "req.method === 'OPTIONS'" in file_map["api/chat.js"]

    # Check frontend content
    assert "res.body.getReader()" in file_map["src/ChatWidget.jsx"]
    assert "new TextDecoder" in file_map["src/ChatWidget.jsx"]
    assert "AbortController" in file_map["src/ChatWidget.jsx"]

    # Check verification script
    assert "curl -N -X POST" in file_map["verify_stream.sh"]

    # Check manifest
    assert result.manifest["app_name"] == "customer_support_bot"
    assert result.manifest["files_count"] == 6


def test_scaffolder_typescript_support(engine: GeminiVercelStreamingEngine):
    """Verify scaffolding with TypeScript language emits .ts and .tsx files."""
    cfg = ScaffoldConfig(
        app_name="ts_streaming_bot",
        language="typescript",
    )
    result = engine.scaffold_app(cfg)
    file_map = dict(result.files)

    assert "api/chat.ts" in file_map
    assert "src/ChatWidget.tsx" in file_map
    assert "VercelRequest" in file_map["api/chat.ts"]


# --- 4. Stream Simulation ---


def test_stream_simulation(engine: GeminiVercelStreamingEngine):
    """Verify unbuffered stream simulation yields chunks and reconstructs original prompt."""
    prompt = "Brain Harness provides modular agent engineering with zero hardcoding."
    sim_result = engine.simulate_stream(prompt, chunks_count=4)

    assert sim_result.total_chunks >= 2
    assert sim_result.reconstructed_text.strip() == prompt.strip()
    assert sim_result.duration_ms >= 0


# --- 5. Micro-Kernel IoC Service Registration & Resolution (Rule 2 & Rule 49) ---


def test_ioc_service_registration_and_execution(service_context: ServiceContext):
    """Verify GeminiVercelStreamingService resolves via ServiceKey and executes cleanly."""
    svc: GeminiVercelStreamingService = service_context.require(
        GEMINI_VERCEL_STREAMING_SERVICE_KEY
    )
    assert svc is not None

    # Test audit_code via service seam
    rep_data = svc.audit_code("const x = 1;")
    assert isinstance(rep_data, AuditReportData)
    assert rep_data.passed is True

    # Test scaffold_app via service seam
    cfg_data = ScaffoldConfigData(
        app_name="ioc_test_bot",
    )
    scaffold_res = svc.scaffold_app(cfg_data)
    assert "api/chat.js" in scaffold_res.files
    assert scaffold_res.manifest["app_name"] == "ioc_test_bot"

    # Test simulate_stream via service seam
    sim_data = svc.simulate_stream("Test simulation string")
    assert isinstance(sim_data, StreamSimulationData)
    assert sim_data.total_chunks >= 1

    # Test visual brief via service seam
    brief_p = svc.generate_visual_brief()
    assert brief_p.exists()
    assert "html" in brief_p.suffix


# --- 6. Plugin Validator Compliance & Lifecycle (Rule 34, 38, 44, 45) ---


def test_plugin_validation_sync():
    """Verify gemini_vercel_streaming_chatbot plugin passes PluginValidator checks."""
    plugin_dir = (
        _ws_root / "plugins" / "integration_and_io" / "gemini_vercel_streaming_chatbot"
    )
    assert plugin_dir.exists()

    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True, f"Plugin validation failed: {report.errors}"


@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Verify plugin on_load registers GEMINI_VERCEL_STREAMING_SERVICE_KEY in context."""
    ctx = ServiceContext()
    p = GeminiVercelStreamingPlugin()
    assert GEMINI_VERCEL_STREAMING_SERVICE_KEY in p.provides

    await p.on_load(ctx)
    resolved = ctx.require(GEMINI_VERCEL_STREAMING_SERVICE_KEY)
    assert resolved is p

    await p.on_unload(ctx)


# --- 7. Headless Click CLI Commands (Rule 6, 10, 23) ---


def test_cli_inspect_command():
    """Verify 'harness gemini-vercel inspect' analyzes code and emits output."""
    runner = CliRunner()

    # Passing code
    res_pass = runner.invoke(
        gemini_vercel_group,
        ["inspect", "const client = 1;"],
    )
    assert res_pass.exit_code == 0
    assert "PASSED" in res_pass.output

    # JSON output
    res_json = runner.invoke(
        gemini_vercel_group,
        ["inspect", "const client = 1;", "--json-output"],
    )
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["passed"] is True
    assert len(data["checks"]) == 5


def test_cli_scaffold_command(tmp_path: Path):
    """Verify 'harness gemini-vercel scaffold' creates application files."""
    runner = CliRunner()

    # Preview mode
    res_prev = runner.invoke(
        gemini_vercel_group,
        ["scaffold", "--name", "cli_test_bot"],
    )
    assert res_prev.exit_code == 0
    assert "Files Generated:   6" in res_prev.output
    assert "Preview" in res_prev.output

    # Write mode
    out_dir = tmp_path / "scaffold_out"
    res_write = runner.invoke(
        gemini_vercel_group,
        ["scaffold", "--name", "written_bot", "--output-dir", str(out_dir), "--write"],
    )
    assert res_write.exit_code == 0
    assert (out_dir / "api" / "chat.js").exists()
    assert (out_dir / "src" / "ChatWidget.jsx").exists()
    assert (out_dir / "vercel.json").exists()
    assert (out_dir / "package.json").exists()


def test_cli_verify_command():
    """Verify 'harness gemini-vercel verify' simulates stream."""
    runner = CliRunner()
    res = runner.invoke(
        gemini_vercel_group,
        ["verify", "--prompt", "Hello streaming world", "--chunks", "3"],
    )
    assert res.exit_code == 0
    assert "Unbuffered Plain-Text Chunk Streaming Simulation" in res.output
    assert "Hello streaming world" in res.output


def test_cli_brief_command(tmp_path: Path):
    """Verify 'harness gemini-vercel brief' generates interactive HTML brief."""
    runner = CliRunner()
    out_file = tmp_path / "cli_brief.html"
    res = runner.invoke(gemini_vercel_group, ["brief", "--output", str(out_file)])
    assert res.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Gemini & Vercel" in content
    assert "mermaid" in content


# --- 8. Skill & Knowledge Vault Integrity (Rule 40, 44) ---


def test_skill_validator_and_card_parser():
    """Verify gemini-vercel-streaming-chatbot skill passes SkillValidator and SkillCardParser."""
    skill_dir = _ws_root / ".agents" / "skills" / "gemini-vercel-streaming-chatbot"
    report = SkillValidator.validate_sync(skill_dir)
    assert report.valid is True, f"SkillValidator failed: {report.errors}"

    node = SkillCardParser.parse_directory(skill_dir)
    assert node is not None
    assert node.name == "gemini-vercel-streaming-chatbot"
    assert len(node.stages) >= 5
    assert len(node.anti_patterns) >= 5


def test_knowledge_vault_dual_file_format():
    """Verify canonical dual-file format in Knowledge Vault (Rule 40)."""
    ki_dir = _ws_root / ".harness" / "knowledge" / "ki_20260918_gemini_vercel_streaming"
    assert ki_dir.exists(), "Knowledge vault directory missing"

    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"
    assert meta_file.exists(), "metadata.json missing"
    assert summary_file.exists(), "summary.md missing"

    meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta_data["id"] == "ki_20260918_gemini_vercel_streaming"
    assert "Johnson Samuel" in meta_data["author"]
    assert len(meta_data["isnad"]["claims"]) >= 3

    summary_text = summary_file.read_text(encoding="utf-8")
    assert "Johnson Samuel" in summary_text
    assert "Plain-Text Chunk Streaming" in summary_text
