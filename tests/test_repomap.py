"""Unit tests for RepoMapService and AST reference graph ranking."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.services.repomap import (
    REPO_MAP_SERVICE_KEY,
    DefaultRepoMapService,
    RepoMapService,
    SymbolTag,
)


@pytest.mark.unit
def test_repomap_service_key() -> None:
    """Verify ServiceKey registration key string."""
    assert REPO_MAP_SERVICE_KEY.name == "service.repomap"


@pytest.mark.unit
def test_extract_tags_python() -> None:
    """Test AST symbol extraction on Python code."""
    svc = DefaultRepoMapService()
    py_code = '''
class PipelineEngine:
    def __init__(self, name: str):
        self.name = name

    async def execute_step(self, step_id: str) -> bool:
        return True

def top_level_helper():
    pass
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(py_code)
        temp_path = f.name

    try:
        tags = svc.extract_tags(temp_path)
        names = {t.name: t.kind for t in tags}
        assert "PipelineEngine" in names
        assert names["PipelineEngine"] == "class"
        assert "execute_step" in names
        assert "top_level_helper" in names
    finally:
        Path(temp_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_extract_tags_typescript() -> None:
    """Test regex symbol extraction on TypeScript code."""
    svc = DefaultRepoMapService()
    ts_code = '''
export interface UserSession {
    id: string;
    role: string;
}

export class SessionStore {
    connect(): void {}
}

export async function authenticateUser(): Promise<boolean> {
    return true;
}
'''
    with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False) as f:
        f.write(ts_code)
        temp_path = f.name

    try:
        tags = svc.extract_tags(temp_path)
        names = {t.name: t.kind for t in tags}
        assert "UserSession" in names
        assert names["UserSession"] == "interface"
        assert "SessionStore" in names
        assert names["SessionStore"] == "class"
        assert "authenticateUser" in names
        assert names["authenticateUser"] == "def"
    finally:
        Path(temp_path).unlink(missing_ok=True)


@pytest.mark.unit
def test_get_repo_map_with_query_ranking() -> None:
    """Test repo map generation and query token ranking."""
    svc = DefaultRepoMapService()
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create multiple files
        (root / "auth.py").write_text("class Authenticator:\n    def verify_token(): pass\n", encoding="utf-8")
        (root / "database.py").write_text("class DatabaseConnection:\n    def query(): pass\n", encoding="utf-8")
        (root / "ui.py").write_text("class VisualWidget:\n    def render(): pass\n", encoding="utf-8")

        # Query mentioning auth
        res = svc.get_repo_map(str(root), query_context="We need to fix Authenticator verify_token issue", max_tokens=200)
        assert res.status == "ok"
        assert res.total_files_scanned == 3
        assert res.total_symbols_indexed > 0
        assert "auth.py:" in res.formatted_map
        # auth.py should appear first due to relevance scoring
        assert res.formatted_map.startswith("auth.py:")
