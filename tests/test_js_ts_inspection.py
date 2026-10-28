"""Tests for JavaScript / TypeScript AST inspection and parameter extraction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.ingestion.inspector import RepoInspector
from harness.ingestion.inspector.js_ts_extractor import (
    extract_js_ts_entrypoints,
    parse_js_ts_params,
    try_js_ts_inspection,
)
from harness.plugins.manifest import IsolationMode


@pytest.mark.unit
class TestJsTsInspection:
    def test_parse_js_ts_params(self) -> None:
        raw = "name: string, count: number = 10, tags?: string[], options: Record<string, any> = {}"
        params = parse_js_ts_params(raw)

        assert len(params) == 4
        assert params[0].name == "name"
        assert params[0].type == "string"
        assert params[0].required is True

        assert params[1].name == "count"
        assert params[1].type == "number"
        assert params[1].required is False  # Has default

        assert params[2].name == "tags"
        assert params[2].type == "array"
        assert params[2].required is False  # Has '?'

        assert params[3].name == "options"
        assert params[3].type == "object"
        assert params[3].required is False

    def test_extract_ts_entrypoints(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        ts_file = src / "calculator.ts"
        ts_file.write_text(
            """
            /**
             * Add two numbers together.
             */
            export async function add(a: number, b: number): Promise<number> {
                return a + b;
            }

            /**
             * Multiply two numbers.
             */
            export const multiply = async (x: number, y: number = 1) => x * y;

            function helperPrivate(val: string) {
                return val;
            }
            """,
            encoding="utf-8",
        )

        entrypoints = extract_js_ts_entrypoints(tmp_path)
        ep_names = {ep.name for ep in entrypoints}
        assert "add" in ep_names
        assert "multiply" in ep_names
        assert "helperPrivate" not in ep_names

        add_ep = next(ep for ep in entrypoints if ep.name == "add")
        assert "Add two numbers" in add_ep.description
        assert len(add_ep.parameters) == 2
        assert add_ep.parameters[0].name == "a"
        assert add_ep.parameters[0].type == "number"

    def test_inspect_ts_repository(self, tmp_path: Path) -> None:
        # Create package.json and tsconfig.json
        (tmp_path / "package.json").write_text(
            json.dumps({
                "name": "@acme/math-utils",
                "version": "2.1.0",
                "description": "High performance TS math",
                "main": "dist/index.js",
                "dependencies": {"lodash": "^4.17.21"},
            }),
            encoding="utf-8",
        )
        (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")

        src = tmp_path / "src"
        src.mkdir()
        (src / "index.ts").write_text(
            """
            /**
             * Calculate square root of input.
             */
            export function squareRoot(val: number): number {
                return Math.sqrt(val);
            }
            """,
            encoding="utf-8",
        )

        inspector = RepoInspector()
        manifest = inspector.inspect(tmp_path)

        assert manifest.name == "acme__math-utils"
        assert manifest.version == "2.1.0"
        assert manifest.language == "typescript"
        assert manifest.isolation == IsolationMode.SUBPROCESS
        assert "lodash" in manifest.dependencies
        assert len(manifest.entrypoints) == 1
        assert manifest.entrypoints[0].name == "squareRoot"
        assert manifest.entrypoints[0].parameters[0].name == "val"
        assert manifest.entrypoints[0].parameters[0].type == "number"
