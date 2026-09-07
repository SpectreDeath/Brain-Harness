# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
resolve_config.py — 3-Tier Layered Configuration Resolver for Agent Skills

Precedence hierarchy:
  1. Project Override: <project_root>/.agents/skills.config.yaml (or .agent/skills.config.yaml)
  2. Skill Default:    <skill_dir>/config.default.yaml
  3. Hardcoded Base:   Built-in conservative fallbacks

Supports additive lists via `extra_*` prefix (e.g. `extra_supported_clients`).
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Rule 23: UTF-8 standard streams entrypoint invariant
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


HARDCODED_FALLBACKS: dict[str, Any] = {
    "line_budget_limit": 500,
    "token_budget_limit": 5000,
    "enforce_two_phase_validation": True,
    "max_repair_attempts": 3,
    "security_risk_threshold": 20,
    "supported_clients": [
        "claude-code",
        "antigravity",
        "vscode",
        "cursor",
        "copilot",
    ],
    "extra_security_patterns": [],
}


@dataclass(slots=True)
class SkillConfiguration:
    """Slotted domain model representing resolved skill configuration."""

    line_budget_limit: int = 500
    token_budget_limit: int = 5000
    enforce_two_phase_validation: bool = True
    max_repair_attempts: int = 3
    security_risk_threshold: int = 20
    supported_clients: list[str] = field(
        default_factory=lambda: [
            "claude-code",
            "antigravity",
            "vscode",
            "cursor",
            "copilot",
        ]
    )
    extra_security_patterns: list[str] = field(default_factory=list)
    raw_config: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], sources: dict[str, str] | None = None) -> "SkillConfiguration":
        # Rule 33: JSON Null-Field Fallback Invariant
        return cls(
            line_budget_limit=int(data.get("line_budget_limit") or 500),
            token_budget_limit=int(data.get("token_budget_limit") or 5000),
            enforce_two_phase_validation=bool(
                data.get("enforce_two_phase_validation")
                if data.get("enforce_two_phase_validation") is not None
                else True
            ),
            max_repair_attempts=int(data.get("max_repair_attempts") or 3),
            security_risk_threshold=int(data.get("security_risk_threshold") or 20),
            supported_clients=list(
                data.get("supported_clients")
                or ["claude-code", "antigravity", "vscode", "cursor", "copilot"]
            ),
            extra_security_patterns=list(data.get("extra_security_patterns") or []),
            raw_config=dict(data),
            sources=dict(sources or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return dict(self.raw_config)


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Safely load a YAML file, returning an empty dict on missing or empty files."""
    if not path.exists() or not path.is_file():
        return {}
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return {}
    if yaml is not None:
        try:
            data = yaml.safe_load(content)
            # Rule 33: JSON / YAML Null-Field Fallback Invariant
            return data if isinstance(data, dict) else {}
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to parse YAML file {path}: {e}\n")
            return {}
    else:
        # Robust fallback parser if PyYAML is unavailable
        res: dict[str, Any] = {}
        current_list_key: str | None = None
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Check if this line is a list item under current_list_key
            if stripped.startswith("- ") and current_list_key:
                val = stripped[2:].strip().strip("\"'")
                res[current_list_key].append(val)
                continue

            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                current_list_key = None

                if not v:
                    # Could be start of a list or dict
                    current_list_key = k
                    res[k] = []
                elif v == "[]":
                    res[k] = []
                elif v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
                    res[k] = items
                elif v.lower() == "true":
                    res[k] = True
                elif v.lower() == "false":
                    res[k] = False
                elif v.isdigit():
                    res[k] = int(v)
                else:
                    res[k] = v.strip("\"'")
        return res


def deep_merge(base: dict[str, Any], override: dict[str, Any], sources: dict[str, str], source_name: str) -> dict[str, Any]:
    """
    Recursively merge override into base.
    Handles additive lists with `extra_*` keys.
    """
    result = dict(base)
    for key, value in override.items():
        if key.startswith("extra_"):
            target_key = key[len("extra_"):]
            base_val = result.get(target_key)
            if isinstance(base_val, list) and isinstance(value, list):
                result[target_key] = base_val + [item for item in value if item not in base_val]
                sources[target_key] = f"{source_name} (additive via {key})"
            else:
                result[key] = value
                sources[key] = source_name
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            sub_sources: dict[str, str] = {}
            result[key] = deep_merge(result[key], value, sub_sources, source_name)
            for sub_k, sub_src in sub_sources.items():
                sources[f"{key}.{sub_k}"] = sub_src
        else:
            result[key] = value
            sources[key] = source_name
    return result


def resolve_skill_configuration(
    skill_name: str,
    project_root: Path | None = None,
    skill_dir: Path | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """
    Resolve configuration across Tier 3 (hardcoded), Tier 2 (skill default),
    and Tier 1 (project override).
    """
    sources: dict[str, str] = {k: "hardcoded fallback" for k in HARDCODED_FALLBACKS}
    config = dict(HARDCODED_FALLBACKS)

    # 1. Locate skill directory and load Tier 2 (Skill Default)
    if skill_dir is None:
        if project_root is not None:
            cand1 = project_root / ".agents" / "skills" / skill_name
            cand2 = project_root / ".agent" / "skills" / skill_name
            if cand1.exists():
                skill_dir = cand1
            elif cand2.exists():
                skill_dir = cand2
            else:
                skill_dir = Path(__file__).resolve().parent.parent
        else:
            skill_dir = Path(__file__).resolve().parent.parent

    default_yaml_path = skill_dir / "config.default.yaml"
    tier2_data = load_yaml_file(default_yaml_path)
    if tier2_data:
        config = deep_merge(config, tier2_data, sources, f"skill default ({default_yaml_path.name})")

    # 2. Locate project root and load Tier 1 (Project Override)
    if project_root is None:
        cur = skill_dir.resolve()
        while cur != cur.parent:
            if (cur / ".git").exists() or (cur / "pyproject.toml").exists() or (cur / ".agents").exists():
                project_root = cur
                break
            cur = cur.parent
        if project_root is None:
            project_root = Path.cwd()

    candidate_overrides = [
        project_root / ".agents" / "skills.config.yaml",
        project_root / ".agents" / "skills.config.yml",
        project_root / ".agent" / "skills.config.yaml",
        project_root / ".agent" / "skills.config.yml",
        project_root / "skills.config.yaml",
    ]

    tier1_override: dict[str, Any] = {}
    found_override_path: Path | None = None
    for cand in candidate_overrides:
        if cand.exists() and cand.is_file():
            found_override_path = cand
            full_override = load_yaml_file(cand)
            # Rule 33: check under skill_name key or root
            tier1_override = full_override.get(skill_name) or full_override.get(skill_name.replace("-", "_")) or {}
            if not tier1_override and full_override.get("skills"):
                skills_map = full_override.get("skills") or {}
                tier1_override = skills_map.get(skill_name) or {}
            break

    if tier1_override and found_override_path is not None:
        config = deep_merge(config, tier1_override, sources, f"project override ({found_override_path.name})")

    return config, sources


def resolve_for_skill(
    skill_dir: Path | str,
    project_root: Path | str | None = None,
) -> SkillConfiguration:
    """High-leverage entrypoint: resolve configuration directly from a skill directory."""
    s_dir = Path(skill_dir).resolve()
    p_root = Path(project_root).resolve() if project_root else None
    resolved_dict, sources = resolve_skill_configuration(
        skill_name=s_dir.name,
        project_root=p_root,
        skill_dir=s_dir,
    )
    return SkillConfiguration.from_dict(resolved_dict, sources=sources)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve 3-tier layered configuration for agent skills without forking."
    )
    parser.add_argument(
        "skill_name",
        nargs="?",
        default="agent-skill-sdlc",
        help="Name of the target skill to resolve config for (default: agent-skill-sdlc).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to root of repository or project workspace.",
    )
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=None,
        help="Explicit path to skill directory containing config.default.yaml.",
    )
    parser.add_argument(
        "--print-sources",
        action="store_true",
        help="Print origin source for each configuration key.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit resolved configuration as raw JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional file path to write resolved JSON configuration to.",
    )

    args = parser.parse_args()

    try:
        resolved, sources = resolve_skill_configuration(
            skill_name=args.skill_name,
            project_root=args.project_root,
            skill_dir=args.skill_dir,
        )

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(resolved, indent=2), encoding="utf-8")

        if args.json:
            print(json.dumps(resolved, indent=2))
        else:
            print(f"=== Resolved Configuration for '{args.skill_name}' ===")
            for key, val in resolved.items():
                source_info = f"  [{sources.get(key, 'unknown')}]" if args.print_sources else ""
                print(f"  {key}: {val}{source_info}")

        return 0
    except Exception as exc:
        sys.stderr.write(f"Error resolving configuration: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
