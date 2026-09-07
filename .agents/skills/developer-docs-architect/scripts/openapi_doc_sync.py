# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
openapi_doc_sync.py — OpenAPI 3.0 to Track B Markdown Synchronizer and Scaffold Engine.
Generates compliant 6-section API endpoint documentation from OpenAPI 3.0 specifications.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 stream entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ============================================================================
# Domain Models (Rule 12: Slotted Dataclass Architecture)
# ============================================================================

@dataclass(slots=True)
class EndpointParameter:
    name: str
    in_location: str  # path, query, header
    required: bool
    schema_type: str
    description: str = ""


@dataclass(slots=True)
class EndpointOperation:
    path: str
    method: str  # get, post, put, delete, patch
    summary: str
    description: str
    operation_id: str
    tags: list[str] = field(default_factory=list)
    security: list[str] = field(default_factory=list)
    parameters: list[EndpointParameter] = field(default_factory=list)
    request_body_schema: dict[str, Any] | None = None
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(slots=True)
class SyncResult:
    spec_title: str
    spec_version: str
    operations_count: int
    output_files: list[str] = field(default_factory=list)
    status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_title": self.spec_title,
            "spec_version": self.spec_version,
            "operations_count": self.operations_count,
            "output_files": self.output_files,
            "status": self.status,
        }


# ============================================================================
# Synchronization Engine
# ============================================================================

class OpenApiDocSynchronizer:
    """Transforms OpenAPI 3.0 specifications into 6-section Track B Markdown."""

    STANDARD_ERROR_REMEDIATIONS: dict[str, tuple[str, str, str]] = {
        "400": ("ERR_BAD_REQUEST", "Malformed JSON syntax or invalid data type", "Validate payload structure against schema."),
        "401": ("ERR_UNAUTHORIZED", "Missing or expired Bearer token", "Generate or refresh your API authentication token."),
        "403": ("ERR_FORBIDDEN", "Insufficient scope or permission for resource", "Request elevated role permissions from tenant admin."),
        "404": ("ERR_NOT_FOUND", "Target URI or resource identifier does not exist", "Verify resource ID and base endpoint URI."),
        "422": ("ERR_UNPROCESSABLE", "Business validation failed on valid syntax", "Correct payload parameters failing semantic validation."),
        "429": ("ERR_RATE_LIMIT", "Request quota exceeded for current time window", "Respect Retry-After header with exponential backoff."),
        "500": ("ERR_INTERNAL", "Unexpected upstream service fault", "Retry with idempotency key; alert platform support if persistent."),
    }

    @classmethod
    def load_spec(cls, spec_path: Path | str) -> dict[str, Any]:
        p = Path(spec_path).resolve()
        content = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
                return yaml.safe_load(content)
            except ImportError:
                # Fallback: simple JSON loader or error
                pass
        return json.loads(content)

    @classmethod
    def parse_operations(cls, spec_dict: dict[str, Any]) -> list[EndpointOperation]:
        ops: list[EndpointOperation] = []
        paths = spec_dict.get("paths") or {}

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method in ("get", "post", "put", "delete", "patch", "options", "head"):
                if method not in path_item:
                    continue
                op_data = path_item[method]
                if not isinstance(op_data, dict):
                    continue

                params: list[EndpointParameter] = []
                for p_raw in (op_data.get("parameters") or []) + (path_item.get("parameters") or []):
                    if isinstance(p_raw, dict):
                        p_schema = p_raw.get("schema") or {}
                        params.append(
                            EndpointParameter(
                                name=p_raw.get("name", ""),
                                in_location=p_raw.get("in", "query"),
                                required=bool(p_raw.get("required", False)),
                                schema_type=p_schema.get("type", "string"),
                                description=p_raw.get("description", ""),
                            )
                        )

                # Request body
                rb_schema = None
                rb = op_data.get("requestBody") or {}
                if isinstance(rb, dict):
                    content = rb.get("content") or {}
                    json_media = content.get("application/json") or {}
                    rb_schema = json_media.get("schema")

                # Responses
                resps = op_data.get("responses") or {}

                sec_list: list[str] = []
                for sec_entry in op_data.get("security") or spec_dict.get("security") or []:
                    if isinstance(sec_entry, dict):
                        sec_list.extend(sec_entry.keys())

                op_id = op_data.get("operationId") or f"{method}_{path_str.replace('/', '_').strip('_')}"

                ops.append(
                    EndpointOperation(
                        path=path_str,
                        method=method.upper(),
                        summary=op_data.get("summary") or f"{method.upper()} {path_str}",
                        description=op_data.get("description", ""),
                        operation_id=op_id,
                        tags=op_data.get("tags") or ["Default"],
                        security=list(dict.fromkeys(sec_list)),
                        parameters=params,
                        request_body_schema=rb_schema,
                        responses=resps,
                    )
                )

        return ops

    @classmethod
    def synthesize_mock_json(cls, schema: dict[str, Any] | None) -> str:
        if not schema:
            return "{\n  \"status\": \"success\"\n}"
        stype = schema.get("type", "object")
        if stype == "object":
            props = schema.get("properties") or {}
            items = []
            for k, v in props.items():
                val_type = v.get("type", "string") if isinstance(v, dict) else "string"
                if val_type == "integer" or val_type == "number":
                    items.append(f'  "{k}": 100')
                elif val_type == "boolean":
                    items.append(f'  "{k}": true')
                elif val_type == "array":
                    items.append(f'  "{k}": []')
                else:
                    items.append(f'  "{k}": "sample_{k}"')
            body = ",\n".join(items) if items else '  "id": "res_sample_123"'
            return f"{{\n{body}\n}}"
        return "{\n  \"data\": \"sample\"\n}"

    @classmethod
    def render_operation_markdown(cls, op: EndpointOperation) -> str:
        """Render a single operation into the strict 6-section Track B Markdown anatomy."""
        md: list[str] = []

        # Title & Summary
        md.append(f"# {op.summary}\n")
        if op.description:
            md.append(f"{op.description}\n")

        # Section 1: Endpoint & HTTP Method
        md.append("## Endpoint & Method\n")
        md.append(f"```http\n{op.method} {op.path}\n```\n")

        # Section 2: Authentication & Headers
        md.append("## Authentication & Headers\n")
        auth_str = ", ".join(op.security) if op.security else "Bearer <token>"
        md.append(f"- **Authorization Scheme**: `{auth_str}`")
        md.append("- **Headers**:")
        md.append("  - `Content-Type`: `application/json`")
        md.append("  - `Accept`: `application/json`\n")

        # Section 3: Request Parameters
        md.append("## Request Parameters\n")
        if op.parameters:
            md.append("| Name | In | Type | Required | Description |")
            md.append("|---|---|---|---|---|")
            for p in op.parameters:
                req_str = "Yes" if p.required else "No"
                desc = p.description or "Parameter value"
                md.append(f"| `{p.name}` | `{p.in_location}` | `{p.schema_type}` | {req_str} | {desc} |")
            md.append("")
        else:
            md.append("No path or query parameters required.\n")

        # Section 4: Request Body Example
        md.append("## Request Body Example\n")
        if op.method in ("POST", "PUT", "PATCH"):
            sample_body = cls.synthesize_mock_json(op.request_body_schema)
            md.append("```json\n" + sample_body + "\n```\n")
        else:
            md.append("This endpoint does not accept a request body.\n")

        # Section 5: Response Payloads
        md.append("## Response Payloads\n")
        if op.responses:
            for status_code, rdata in op.responses.items():
                rdesc = rdata.get("description", "Operation response") if isinstance(rdata, dict) else "Response"
                md.append(f"### HTTP {status_code} — {rdesc}\n")
                r_content = rdata.get("content") or {} if isinstance(rdata, dict) else {}
                r_schema = r_content.get("application/json", {}).get("schema") if isinstance(r_content, dict) else None
                sample_resp = cls.synthesize_mock_json(r_schema)
                md.append("```json\n" + sample_resp + "\n```\n")
        else:
            md.append("### HTTP 200 OK\n```json\n{\n  \"status\": \"success\"\n}\n```\n")

        # Section 6: Actionable Error Catalog
        md.append("## Actionable Error Catalog\n")
        md.append("| HTTP Code | Error Code | Root Cause Trigger | Developer Remediation |")
        md.append("|---|---|---|---|")
        for code, (err_code, cause, rem) in cls.STANDARD_ERROR_REMEDIATIONS.items():
            md.append(f"| `{code}` | `{err_code}` | {cause} | {rem} |")
        md.append("")

        return "\n".join(md)

    @classmethod
    def sync(cls, spec_path: Path | str, output_dir: Path | str) -> SyncResult:
        p_spec = Path(spec_path).resolve()
        p_out = Path(output_dir).resolve()
        p_out.mkdir(parents=True, exist_ok=True)

        spec = cls.load_spec(p_spec)
        info = spec.get("info") or {}
        title = info.get("title", "API Reference")
        version = info.get("version", "1.0.0")

        ops = cls.parse_operations(spec)
        generated_files: list[str] = []

        for op in ops:
            clean_op_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", op.operation_id).lower()
            tag_folder = p_out / re.sub(r"[^a-zA-Z0-9_\-]", "_", op.tags[0]).lower()
            tag_folder.mkdir(parents=True, exist_ok=True)

            out_file = tag_folder / f"{clean_op_id}.md"
            md_content = cls.render_operation_markdown(op)
            out_file.write_text(md_content, encoding="utf-8")
            generated_files.append(str(out_file))

        # Generate index llms.txt summary
        llms_file = p_out / "llms.txt"
        llms_lines = [
            f"# {title} (v{version})",
            f"> Machine-readable documentation catalog for AI agent retrieval.",
            "",
            "## Available Endpoints",
        ]
        for op in ops:
            clean_op_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", op.operation_id).lower()
            tag_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", op.tags[0]).lower()
            llms_lines.append(f"- [{op.method} {op.path}]({tag_name}/{clean_op_id}.md): {op.summary}")

        llms_file.write_text("\n".join(llms_lines), encoding="utf-8")
        generated_files.append(str(llms_file))

        return SyncResult(
            spec_title=title,
            spec_version=version,
            operations_count=len(ops),
            output_files=generated_files,
            status="ok",
        )


# ============================================================================
# CLI Entrypoint
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="openapi_doc_sync.py — Transform OpenAPI 3.0 specifications into 6-section Track B Markdown."
    )
    parser.add_argument("--spec", required=True, help="Path to OpenAPI 3.0 JSON or YAML spec.")
    parser.add_argument("--out", required=True, help="Target directory for generated Markdown documentation.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary.")

    args = parser.parse_args()
    res = OpenApiDocSynchronizer.sync(args.spec, args.out)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
    else:
        print(f"✓ Synchronized {res.operations_count} endpoints from '{res.spec_title}' (v{res.spec_version})")
        print(f"  Target directory: {args.out}")
        print(f"  Generated {len(res.output_files)} files (including llms.txt index).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
