# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""ChatbotX Production Skill Domain Engine.

Provides slotted/frozen domain models, deterministic local string salvage,
zero-fork configuration resolution, and non-interactive operational CLI seams.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
from typing import Any

# Reconfigure streams to UTF-8 per Rule 23 / Rule 50
if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr:
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class ContactEntity:
    """Slotted immutable contact profile entity."""

    id: str
    name: str
    channel: str
    channel_user_id: str
    status: str = "active"
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("ContactEntity.id cannot be empty")
        if not self.channel or not self.channel.strip():
            raise ValueError("ContactEntity.channel cannot be empty")


@dataclass(slots=True, frozen=True)
class MessagePayload:
    """Slotted immutable outbound message request."""

    contact_id: str
    channel: str
    text: str

    def __post_init__(self) -> None:
        if not self.contact_id or not self.contact_id.strip():
            raise ValueError("MessagePayload.contact_id cannot be empty")
        if not self.text or not self.text.strip():
            raise ValueError("MessagePayload.text cannot be empty")


@dataclass(slots=True, frozen=True)
class FlowTriggerPayload:
    """Slotted immutable flow dispatch request."""

    contact_id: str
    flow_id: str

    def __post_init__(self) -> None:
        if not self.contact_id or not self.contact_id.strip():
            raise ValueError("FlowTriggerPayload.contact_id cannot be empty")
        if not self.flow_id or not self.flow_id.strip():
            raise ValueError("FlowTriggerPayload.flow_id cannot be empty")


class ChatbotXDomainEngine:
    """Deterministic domain engine for ChatbotX operations."""

    @staticmethod
    def salvage_json(raw_text: str) -> dict[str, Any] | list[Any]:
        """Salvage malformed JSON from model outputs using multi-pass local heuristics."""
        if not raw_text or not raw_text.strip():
            raise ValueError("Cannot salvage empty payload")

        text = raw_text.strip()

        # 1. Strip markdown code fences
        fence_pattern = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
        match = fence_pattern.search(text)
        if match:
            text = match.group(1).strip()

        # 2. Slice text between outermost braces or brackets
        first_brace = text.find("{")
        first_bracket = text.find("[")
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = text.rfind("}")
            if last_brace != -1 and last_brace > first_brace:
                text = text[first_brace : last_brace + 1]
        elif first_bracket != -1:
            last_bracket = text.rfind("]")
            if last_bracket != -1 and last_bracket > first_bracket:
                text = text[first_bracket : last_bracket + 1]

        # 3. Strip trailing commas before closing braces/brackets
        text = re.sub(r",\s*([}\]])", r"\1", text)

        # 4. Parse JSON
        return json.loads(text)

    @staticmethod
    def resolve_configuration(project_root: Path | None = None) -> dict[str, Any]:
        """Resolve 3-tier zero-fork configuration (Project Override -> Skill Default -> Fallback)."""
        base_dir = Path(__file__).resolve().parent.parent
        default_config_path = base_dir / "config.default.yaml"

        config: dict[str, Any] = {
            "version": "1.0.0",
            "connection": {"api_url": "https://app.chatbotx.io/api", "timeout_seconds": 30},
            "budgets": {"max_contacts_per_query": 50, "max_retry_attempts": 3},
            "channels": {"default_channel": "whatsapp", "supported_channels": ["whatsapp", "telegram"]},
        }

        # Load skill default if present
        if default_config_path.exists():
            try:
                import yaml

                loaded = yaml.safe_load(default_config_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    config.update(loaded)
            except Exception:
                pass

        # Check for project override in .agents/skills.config.yaml
        root = project_root or Path.cwd()
        override_file = root / ".agents" / "skills.config.yaml"
        if override_file.exists():
            try:
                import yaml

                overrides = yaml.safe_load(override_file.read_text(encoding="utf-8"))
                if isinstance(overrides, dict) and "chatbotx" in overrides:
                    skill_override = overrides["chatbotx"]
                    if isinstance(skill_override, dict):
                        # Merge additive channels
                        extra = skill_override.get("extra_supported_channels") or []
                        if extra and isinstance(config.get("channels"), dict):
                            current = list(config["channels"].get("supported_channels", []))
                            current.extend(extra)
                            config["channels"]["supported_channels"] = sorted(set(current))
                        config.update(skill_override)
            except Exception:
                pass

        return config


def main() -> None:
    parser = argparse.ArgumentParser(description="ChatbotX Domain Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: salvage
    salvage_parser = subparsers.add_parser("salvage", help="Salvage malformed JSON payload")
    salvage_parser.add_argument("--file", help="File containing raw JSON to salvage")
    salvage_parser.add_argument("--raw", help="Raw JSON string")

    # Subcommand: config
    config_parser = subparsers.add_parser("config", help="Resolve 3-tier zero-fork configuration")
    config_parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    if args.command == "salvage":
        raw_text = ""
        if args.file:
            raw_text = Path(args.file).read_text(encoding="utf-8")
        elif args.raw:
            raw_text = args.raw
        else:
            print("Error: either --file or --raw required", file=sys.stderr)
            sys.exit(1)

        try:
            salvaged = ChatbotXDomainEngine.salvage_json(raw_text)
            print(json.dumps(salvaged, indent=2))
        except Exception as e:
            print(f"Salvage error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "config":
        resolved = ChatbotXDomainEngine.resolve_configuration(Path(args.project_root))
        print(json.dumps(resolved, indent=2))


if __name__ == "__main__":
    main()
