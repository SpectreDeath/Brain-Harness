"""Comprehensive test suite for the deepened developer-docs-architect skill and tooling seams."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

# Import the deepened skill scripts dynamically or via relative imports
import sys

SKILL_DIR = Path(__file__).parent.parent / ".agents" / "skills" / "developer-docs-architect"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from doc_linter import DocumentationLinter, FileLintReport
from openapi_doc_sync import EndpointOperation, OpenApiDocSynchronizer


@pytest.mark.unit
class TestDocumentationLinter:
    """Unit tests for doc_linter.py AST and editorial inspection engine."""

    def test_bolding_calculation_within_threshold(self) -> None:
        linter = DocumentationLinter(max_bolding_percentage=10.0)
        content = (
            "# Getting Started\n\n"
            "This is standard documentation content explaining how the service functions in great detail. "
            "We have only **one key term** highlighted here out of a large paragraph of text."
        )
        report = linter.lint_text(content, file_identifier="test.md")
        assert report.valid is True
        assert report.bolding is not None
        assert report.bolding.passed is True
        assert report.bolding.bold_percentage <= 10.0

    def test_bolding_calculation_exceeds_threshold(self) -> None:
        linter = DocumentationLinter(max_bolding_percentage=10.0)
        content = (
            "# Critical Notice\n\n"
            "**THIS ENTIRE PARAGRAPH IS HEAVILY BOLDED AND SHOUTING AT THE USER REPEATEDLY.**"
        )
        report = linter.lint_text(content, file_identifier="test_bold.md")
        assert report.valid is False
        assert report.bolding is not None
        assert report.bolding.passed is False
        assert report.bolding.bold_percentage > 10.0
        assert any(f.rule == "BoldingRatio" for f in report.findings)

    def test_heading_hierarchy_sequential(self) -> None:
        linter = DocumentationLinter()
        content = (
            "# Main Title\n\n"
            "## Section Level 2\n\n"
            "### Subsection Level 3\n\n"
            "## Another Section Level 2\n"
        )
        report = linter.lint_text(content, file_identifier="test_headings.md")
        assert report.valid is True
        assert not any(f.rule == "HeadingHierarchy" for f in report.findings)

    def test_heading_hierarchy_skipped_levels(self) -> None:
        linter = DocumentationLinter()
        content = (
            "# Main Title\n\n"
            "### Skipped Straight to Level 3\n"
        )
        report = linter.lint_text(content, file_identifier="test_skip.md")
        assert report.valid is False
        assert any(f.rule == "HeadingHierarchy" for f in report.findings)

    def test_code_block_language_identifier(self) -> None:
        linter = DocumentationLinter()
        content = (
            "# Code Example\n\n"
            "```\necho 'hello world'\n```\n"
        )
        report = linter.lint_text(content, file_identifier="test_code.md")
        assert any(f.rule == "CodeBlockLanguage" for f in report.findings)

    def test_complete_6_section_endpoint_anatomy(self) -> None:
        linter = DocumentationLinter()
        content = """# Create Payment Charge

## Endpoint & Method
```http
POST /v1/payments/charges
```

## Authentication & Headers
- **Authorization**: Bearer <token>
- Headers: Content-Type: application/json

## Request Parameters
| Name | In | Type | Required | Description |
|---|---|---|---|---|
| `amount` | query | integer | Yes | Charge amount in cents |

## Request Body Example
```json
{
  "amount": 1000,
  "currency": "usd"
}
```

## Response Payloads
### HTTP 200 OK
```json
{
  "id": "ch_123",
  "status": "succeeded"
}
```

## Actionable Error Catalog
| HTTP Code | Error Code | Root Cause Trigger | Developer Remediation |
|---|---|---|---|
| `400` | `ERR_BAD_REQUEST` | Missing amount | Provide amount |
| `401` | `ERR_UNAUTHORIZED` | Expired token | Refresh token |
"""
        report = linter.lint_text(content, file_identifier="payment_endpoint.md")
        assert report.valid is True
        assert report.anatomy is not None
        assert report.anatomy.is_api_reference is True
        assert report.anatomy.passed is True
        assert len(report.anatomy.missing_sections) == 0

    def test_incomplete_endpoint_anatomy_flags_missing(self) -> None:
        linter = DocumentationLinter()
        content = """# Incomplete API Reference

POST /v1/test

## Request Parameters
None.
"""
        report = linter.lint_text(content, file_identifier="incomplete.md")
        assert report.valid is False
        assert report.anatomy is not None
        assert report.anatomy.passed is False
        assert len(report.anatomy.missing_sections) > 0


@pytest.mark.unit
class TestOpenApiDocSynchronizer:
    """Unit tests for openapi_doc_sync.py engine."""

    def test_spec_to_markdown_synchronization(self, tmp_path: Path) -> None:
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Payment Gateway API",
                "version": "1.0.0",
                "description": "Enterprise payment processing service.",
            },
            "paths": {
                "/v1/charges": {
                    "post": {
                        "summary": "Create a new charge",
                        "operationId": "create_charge",
                        "tags": ["Charges"],
                        "parameters": [
                            {
                                "name": "idempotency_key",
                                "in": "header",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "Unique idempotency token",
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "amount": {"type": "integer"},
                                            "currency": {"type": "string"},
                                        },
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Charge created successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "charge_id": {"type": "string"},
                                                "status": {"type": "string"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }

        spec_file = tmp_path / "openapi.json"
        spec_file.write_text(json.dumps(spec), encoding="utf-8")

        out_dir = tmp_path / "docs"
        result = OpenApiDocSynchronizer.sync(spec_file, out_dir)

        assert result.status == "ok"
        assert result.operations_count == 1
        assert len(result.output_files) == 2  # 1 endpoint md + 1 llms.txt

        charge_doc = out_dir / "charges" / "create_charge.md"
        assert charge_doc.exists()

        content = charge_doc.read_text(encoding="utf-8")
        assert "## Endpoint & Method" in content
        assert "POST /v1/charges" in content
        assert "## Authentication & Headers" in content
        assert "## Request Parameters" in content
        assert "## Request Body Example" in content
        assert "## Response Payloads" in content
        assert "## Actionable Error Catalog" in content

        # Now lint the generated document with DocumentationLinter
        linter = DocumentationLinter()
        lint_report = linter.lint_file(charge_doc)
        assert lint_report.valid is True
        assert lint_report.anatomy is not None
        assert lint_report.anatomy.passed is True

        # Check llms.txt
        llms_doc = out_dir / "llms.txt"
        assert llms_doc.exists()
        assert "POST /v1/charges" in llms_doc.read_text(encoding="utf-8")
