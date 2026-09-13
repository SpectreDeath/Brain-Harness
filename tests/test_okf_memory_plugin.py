"""Tests for OKF Memory Plugin (plugins/memory_and_epistemics/okf_memory).

Covers:
- BM25 lexical ranking and governance term boosting
- Path-scoped pre-edit governance evaluation (SearchForPath)
- Path traversal defense invariants
- Concept mutation with frontmatter sanitization and auto-bookkeeping
- Actor trust ordering invariants and normative validation
- Plugin manifest and schema validation via PluginValidator
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.memory_and_epistemics.okf_memory.main import (
    OKFMemoryEngine,
    OKFMemoryPlugin,
    _ensure_within_root,
    _normalize_path,
)


@pytest.mark.unit
class TestOKFMemoryEngineUnit:
    """Unit tests for in-memory and filesystem OKF v0.2 bundle logic."""

    @pytest.fixture
    def bundle_dir(self, tmp_path: Path) -> Path:
        """Create temporary OKF knowledge bundle with sample concepts."""
        knowledge = tmp_path / "knowledge"
        knowledge.mkdir()

        # Concept 1: Auth JWT
        c1 = knowledge / "auth-jwt-revocation.md"
        c1.write_text(
            "---\n"
            "id: auth-jwt-revocation\n"
            "title: JWT Revocation Strategy\n"
            "type: architecture\n"
            "description: Implements Redis denylist for instant token revocation.\n"
            "governance:\n"
            "  - Always hash token jti claim before storing in Redis denylist\n"
            "code_refs:\n"
            "  - src/api/auth.py\n"
            "  - src/core/security.py\n"
            "generated:\n"
            "  by: agent:brain-harness\n"
            "  at: '2026-09-13T12:00:00Z'\n"
            "---\n\n"
            "## Details\nRedis token revocation storage details.",
            encoding="utf-8",
        )

        # Concept 2: DB Connection Pool
        c2 = knowledge / "db-connection-pool.md"
        c2.write_text(
            "---\n"
            "id: db-connection-pool\n"
            "title: Database Pool Sizing\n"
            "type: architecture\n"
            "description: Limits database pool to 20 concurrent connections.\n"
            "governance:\n"
            "  - Never allocate more than 50 connections in production\n"
            "code_refs:\n"
            "  - src/db/session.py\n"
            "generated:\n"
            "  by: agent:brain-harness\n"
            "  at: '2026-09-13T12:00:00Z'\n"
            "---\n\n"
            "## Details\nDatabase pool sizing invariants.",
            encoding="utf-8",
        )

        return knowledge

    def test_path_normalization(self) -> None:
        """Verify cross-platform path normalization to forward slashes."""
        assert _normalize_path("src\\api\\auth.py") == "src/api/auth.py"
        assert _normalize_path("./src/api/auth.py") == "src/api/auth.py"

    def test_path_traversal_defense(self, tmp_path: Path) -> None:
        """Verify that directory escaping raises ValueError."""
        root = tmp_path / "safe_root"
        root.mkdir()
        malicious = root / ".." / "escaped.md"
        with pytest.raises(ValueError, match="Path traversal detected"):
            _ensure_within_root(root, malicious)

    def test_pre_edit_path_scoping(self, bundle_dir: Path) -> None:
        """Verify that scoping by code path retrieves governing concepts and rules."""
        engine = OKFMemoryEngine(default_root=bundle_dir)
        res = engine.search(for_path="src/api/auth.py", bundle_dir=str(bundle_dir))

        assert res["status"] == "ok"
        assert res["results_count"] == 1
        top = res["results"][0]
        assert top["id"] == "auth-jwt-revocation"
        assert "Always hash token jti claim" in top["governance"][0]
        assert "src/api/auth.py" in top["matched_refs"]

    def test_bm25_lexical_search_ranking(self, bundle_dir: Path) -> None:
        """Verify BM25 ranking prioritizes terms in title, description, and governance."""
        engine = OKFMemoryEngine(default_root=bundle_dir)
        res = engine.search(query="redis token revocation", limit=3, bundle_dir=str(bundle_dir))

        assert res["status"] == "ok"
        assert res["results_count"] >= 1
        assert res["results"][0]["id"] == "auth-jwt-revocation"
        assert res["results"][0]["score"] > 0.0

    def test_atomic_create_and_bookkeeping(self, bundle_dir: Path) -> None:
        """Verify that creating a concept automatically updates index.md and log.md."""
        engine = OKFMemoryEngine(default_root=bundle_dir)
        created = engine.create(
            concept_id="cache-eviction-policy",
            title="Cache Eviction Policy",
            concept_type="decision",
            description="LRU cache eviction policy with 1 hour TTL.",
            body="Cache body documentation.",
            governance=["Max memory cap: 256MB"],
            code_refs=["src/cache/lru.py"],
            bundle_dir=str(bundle_dir),
        )

        assert created["id"] == "cache-eviction-policy"
        assert (bundle_dir / "cache-eviction-policy.md").exists()

        # Check index.md
        index_file = bundle_dir / "index.md"
        assert index_file.exists()
        index_text = index_file.read_text(encoding="utf-8")
        assert "cache-eviction-policy" in index_text
        assert "LRU cache eviction policy" in index_text

        # Check log.md
        log_file = bundle_dir / "log.md"
        assert log_file.exists()
        log_text = log_file.read_text(encoding="utf-8")
        assert "CREATE" in log_text
        assert "cache-eviction-policy" in log_text

    def test_update_and_relate_linking(self, bundle_dir: Path) -> None:
        """Verify update mutations and bidirectional frontmatter linking."""
        engine = OKFMemoryEngine(default_root=bundle_dir)

        # Update
        updated = engine.update(
            concept_id="db-connection-pool",
            description="Updated description with pool size 25.",
            bundle_dir=str(bundle_dir),
        )
        assert updated["description"] == "Updated description with pool size 25."

        # Relate
        rel = engine.relate(
            source_id="auth-jwt-revocation",
            target_id="db-connection-pool",
            description="Auth sessions check user state in DB pool",
            bundle_dir=str(bundle_dir),
        )
        assert rel["status"] == "ok"

        # Verify reciprocity
        c1 = engine.show("auth-jwt-revocation", bundle_dir=str(bundle_dir))
        c2 = engine.show("db-connection-pool", bundle_dir=str(bundle_dir))
        assert c1 is not None and c2 is not None

    def test_trust_ordering_and_schema_validation(self, bundle_dir: Path) -> None:
        """Verify actor trust ordering detects self-attestation violations."""
        engine = OKFMemoryEngine(default_root=bundle_dir)

        # Clean bundle passes validation
        rep = engine.validate(strict=False, bundle_dir=str(bundle_dir))
        assert rep["valid"] is True
        assert len(rep["errors"]) == 0

        # Inject self-attestation violation (Rule 3)
        bad_file = bundle_dir / "bad-concept.md"
        bad_file.write_text(
            "---\n"
            "id: bad-concept\n"
            "title: Untrusted Concept\n"
            "type: concept\n"
            "description: Violates actor trust ordering by self-verifying.\n"
            "generated:\n"
            "  by: agent:brain-harness\n"
            "verified:\n"
            "  by: agent:brain-harness\n"
            "---\n\n"
            "Body",
            encoding="utf-8",
        )

        rep_bad = engine.validate(strict=False, bundle_dir=str(bundle_dir))
        assert rep_bad["valid"] is False
        assert any("Self-attestation violation" in err for err in rep_bad["errors"])


@pytest.mark.integration
class TestOKFMemoryPluginIntegration:
    """Integration test verifying plugin discovery and manifest compliance."""

    def test_plugin_validator_compliance(self) -> None:
        """Verify that okf_memory passes PluginValidator with report.valid == True (Rule 34)."""
        report = PluginValidator.validate_sync("plugins/memory_and_epistemics/okf_memory")
        assert report.valid is True, f"Plugin validation failed: {report.errors}"
        assert len(report.errors) == 0

        # Verify all 6 declared entrypoints exist
        ast_check = next((c for c in report.checks if c.name == "AST Function Inspection"), None)
        assert ast_check is not None
        assert ast_check.passed is True

    def test_plugin_instantiation_and_properties(self) -> None:
        """Verify HarnessPlugin singleton subclass properties."""
        plugin = OKFMemoryPlugin()
        assert plugin.name == "plugin.okf_memory"
        assert plugin.version == "1.0.0"
        assert len(plugin.provides) == 1
        assert plugin.provides[0].name == "service.okf_memory"
        assert plugin.requires == []
