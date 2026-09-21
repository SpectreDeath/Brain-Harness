"""Tests for the deterministic-validation-loop skill and knowledge item."""
import json
import re
import pytest
from jsonschema import validate, ValidationError

# --- Mock Implementation of 3-Tier Validator & Loop Engine ---

DEPLOYMENT_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["service_name", "replicas", "resources", "health_check"],
    "properties": {
        "service_name": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
        "replicas": {"type": "integer", "minimum": 1, "maximum": 20},
        "resources": {
            "type": "object",
            "required": ["cpu_limit", "memory_limit_mb"],
            "properties": {
                "cpu_limit": {"type": "number", "minimum": 0.1, "maximum": 8.0},
                "memory_limit_mb": {"type": "integer", "minimum": 128, "maximum": 16384},
            },
        },
        "health_check": {
            "type": "object",
            "required": ["path", "timeout_seconds", "interval_seconds"],
            "properties": {
                "path": {"type": "string", "pattern": "^/"},
                "timeout_seconds": {"type": "integer", "minimum": 1},
                "interval_seconds": {"type": "integer", "minimum": 5},
            },
        },
    },
}


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """3-Tier Validator: Schema + Boundary + Cross-Field Business Rules."""
    errors = []
    # Tier 1: Structural Schema Validation
    try:
        validate(instance=config, schema=DEPLOYMENT_CONFIG_SCHEMA)
    except ValidationError as e:
        errors.append(f"Schema: {e.message} (at {list(e.path)})")
        return False, errors  # Bail early on broken structure

    # Tier 2 & 3: Cross-field business rules that JSON Schema cannot easily express
    if config["replicas"] > 5 and config["resources"]["cpu_limit"] < 1.0:
        errors.append(f"replicas={config['replicas']} requires cpu_limit >= 1.0")
    if config["health_check"]["timeout_seconds"] >= config["health_check"]["interval_seconds"]:
        errors.append("timeout_seconds must be < interval_seconds")

    return len(errors) == 0, errors


class MockDeterministicValidationLoop:
    """Mock state machine simulating the generate -> validate -> retry loop."""
    def __init__(self, generator_func, max_attempts: int = 3):
        self.generator_func = generator_func
        self.max_attempts = max_attempts
        self.telemetry_log = []

    def run(self, request: str) -> dict:
        attempts = 0
        errors = []
        payload = None

        while attempts < self.max_attempts:
            attempts += 1
            payload = self.generator_func(request, errors, attempts)
            if not payload:
                errors = ["Output was not valid JSON or was empty"]
                continue

            is_valid, errors = validate_config(payload)
            if is_valid:
                return {"status": "success", "payload": payload, "attempts": attempts, "errors": []}

        # Exhausted attempts -> Execute Triage
        triage_record = {"request": request, "final_errors": errors, "attempts": attempts}
        self.telemetry_log.append(triage_record)
        return {"status": "rejected", "error_code": 422, "errors": errors, "attempts": attempts}


# --- Test Cases ---

def test_tier_1_valid_config():
    """Verify that a compliant config passes validation cleanly."""
    valid_cfg = {
        "service_name": "payment-api",
        "replicas": 3,
        "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
        "health_check": {"path": "/healthz", "timeout_seconds": 2, "interval_seconds": 10},
    }
    is_valid, errors = validate_config(valid_cfg)
    assert is_valid is True
    assert errors == []


def test_tier_1_missing_required_fields():
    """Verify Tier 1 bails early when required fields are missing."""
    broken_cfg = {"service_name": "payment-api"}
    is_valid, errors = validate_config(broken_cfg)
    assert is_valid is False
    assert len(errors) == 1
    assert "Schema:" in errors[0]


def test_tier_2_boundary_violations():
    """Verify Tier 2 catches regex pattern and numerical bounds."""
    invalid_bounds = {
        "service_name": "Invalid_Service_Name",  # uppercase and underscore violate regex
        "replicas": 50,  # exceeds maximum 20
        "resources": {"cpu_limit": 0.5, "memory_limit_mb": 64},  # below minimum 128
        "health_check": {"path": "invalid-no-slash", "timeout_seconds": 2, "interval_seconds": 10},
    }
    is_valid, errors = validate_config(invalid_bounds)
    assert is_valid is False
    assert any("Schema:" in err for err in errors)


def test_tier_3_cross_field_rules():
    """Verify Tier 3 catches cross-field logical invariants."""
    cross_field_broken = {
        "service_name": "auth-service",
        "replicas": 8,  # > 5 requires cpu >= 1.0
        "resources": {"cpu_limit": 0.5, "memory_limit_mb": 1024},
        "health_check": {"path": "/health", "timeout_seconds": 15, "interval_seconds": 10},  # timeout >= interval
    }
    is_valid, errors = validate_config(cross_field_broken)
    assert is_valid is False
    assert len(errors) == 2
    assert any("requires cpu_limit >= 1.0" in err for err in errors)
    assert any("timeout_seconds must be < interval_seconds" in err for err in errors)


def test_state_loop_recovery_on_retry():
    """Verify that feedback injection enables recovery on attempt 2."""
    def mock_llm_generator(req, errors, attempt):
        if attempt == 1:
            # First attempt: invalid cross-field rule
            return {
                "service_name": "worker-svc",
                "replicas": 6,
                "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
                "health_check": {"path": "/health", "timeout_seconds": 2, "interval_seconds": 10},
            }
        # Second attempt: LLM fixes error based on feedback
        assert len(errors) == 1
        assert "requires cpu_limit >= 1.0" in errors[0]
        return {
            "service_name": "worker-svc",
            "replicas": 6,
            "resources": {"cpu_limit": 2.0, "memory_limit_mb": 512},
            "health_check": {"path": "/health", "timeout_seconds": 2, "interval_seconds": 10},
        }

    loop = MockDeterministicValidationLoop(mock_llm_generator, max_attempts=3)
    result = loop.run("Deploy worker service")
    assert result["status"] == "success"
    assert result["attempts"] == 2
    assert result["payload"]["resources"]["cpu_limit"] == 2.0


def test_state_loop_exhausted_retries_triage():
    """Verify that failing 3 attempts triggers typed rejection and telemetry logging."""
    def always_broken_llm(req, errors, attempt):
        return {
            "service_name": "broken-svc",
            "replicas": 10,
            "resources": {"cpu_limit": 0.2, "memory_limit_mb": 256},
            "health_check": {"path": "/h", "timeout_seconds": 10, "interval_seconds": 5},
        }

    loop = MockDeterministicValidationLoop(always_broken_llm, max_attempts=3)
    result = loop.run("Deploy broken service")
    assert result["status"] == "rejected"
    assert result["error_code"] == 422
    assert result["attempts"] == 3
    assert len(loop.telemetry_log) == 1
    assert loop.telemetry_log[0]["request"] == "Deploy broken service"


def test_skill_compliance_and_formatting():
    """Verify SKILL.md, CARD.md, and Knowledge Item conform to Harness standards."""
    import pathlib
    root = pathlib.Path("d:/GitHub/projects/Brain Harness")
    skill_file = root / ".agents/skills/deterministic-validation-loop/SKILL.md"
    card_file = root / ".agents/skills/deterministic-validation-loop/CARD.md"
    ki_meta = root / ".harness/knowledge/ki_self_20260917_03/metadata.json"
    ki_summary = root / ".harness/knowledge/ki_self_20260917_03/summary.md"

    assert skill_file.exists(), "SKILL.md must exist"
    assert card_file.exists(), "CARD.md must exist"
    assert ki_meta.exists(), "metadata.json must exist"
    assert ki_summary.exists(), "summary.md must exist"

    # Rule 44: Frontmatter description length [100, 350]
    content = skill_file.read_text(encoding="utf-8")
    match = re.search(r"description:\s*(.+)", content)
    assert match, "Frontmatter description missing"
    desc = match.group(1).strip()
    assert 100 <= len(desc) <= 350, f"Description length {len(desc)} outside [100, 350]"
    assert "Do not use for" in desc, "Negative boundary missing in description"

    # Rule 37: CARD.md ASCII box header format
    card_content = card_file.read_text(encoding="utf-8")
    assert "│ SKILL: deterministic-validation-loop" in card_content, "CARD header missing or invalid border"
    assert "║" not in card_content, "CARD header must use single-pipe border (│), not double-pipe"

    # Rule 37: SKILL.md anti-patterns header format
    assert "## Anti-Patterns" in content, "Exact ## Anti-Patterns heading missing"
    assert re.search(r"- \*\*[^*]+\*\* —", content), "Anti-patterns must follow '- **Name** — Description' format"

    # Rule 40 & 41: Knowledge Item
    meta_data = json.loads(ki_meta.read_text(encoding="utf-8"))
    assert meta_data["id"] == "ki_self_20260917_03"
    assert meta_data["category"] == "agent_orchestration"
    assert len(meta_data["isnad"]["claims"]) >= 3
