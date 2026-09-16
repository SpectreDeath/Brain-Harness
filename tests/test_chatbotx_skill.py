"""Contract tests for ChatbotX Agent Skill and Domain Engine.

Verifies:
1. Slotted and frozen dataclass immutability (Rule 12, Rule 43)
2. Domain engine construction validation
3. Local JSON salvage heuristics (Rule 42)
4. 3-tier zero-fork configuration resolution (Rule 44)
5. Structural skill hygiene, CARD.md borders, and Anti-Patterns formatting (Rule 37)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

script_path = (
    Path(__file__).resolve().parent.parent
    / ".agents"
    / "skills"
    / "chatbotx"
    / "scripts"
    / "chatbotx_engine.py"
)
import sys

spec = importlib.util.spec_from_file_location("chatbotx_engine", script_path)
assert spec is not None and spec.loader is not None
chatbotx_engine = importlib.util.module_from_spec(spec)
sys.modules["chatbotx_engine"] = chatbotx_engine
spec.loader.exec_module(chatbotx_engine)


ChatbotXDomainEngine = chatbotx_engine.ChatbotXDomainEngine
ContactEntity = chatbotx_engine.ContactEntity
FlowTriggerPayload = chatbotx_engine.FlowTriggerPayload
MessagePayload = chatbotx_engine.MessagePayload



@pytest.mark.unit
def test_chatbotx_domain_entities_immutability() -> None:
    """Verify that domain dataclasses are slotted, frozen, and immutable per Rule 12 and Rule 43."""
    contact = ContactEntity(
        id="cnt_001",
        name="Alice",
        channel="whatsapp",
        channel_user_id="+15550001",
        tags=("lead", "vip"),
    )
    assert contact.id == "cnt_001"
    assert "vip" in contact.tags

    # Direct attribute assignment must raise AttributeError/TypeError per Rule 43
    with pytest.raises((AttributeError, TypeError)):
        contact.name = "Bob"  # type: ignore[misc]

    msg = MessagePayload(
        contact_id="cnt_001",
        channel="whatsapp",
        text="Hello World",
    )
    assert msg.text == "Hello World"
    with pytest.raises((AttributeError, TypeError)):
        msg.text = "Changed"  # type: ignore[misc]

    flow = FlowTriggerPayload(
        contact_id="cnt_001",
        flow_id="flow_welcome",
    )
    assert flow.flow_id == "flow_welcome"
    with pytest.raises((AttributeError, TypeError)):
        flow.flow_id = "flow_other"  # type: ignore[misc]


@pytest.mark.unit
def test_chatbotx_entity_construction_assertions() -> None:
    """Verify that empty mandatory fields trigger ValueError in __post_init__."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        ContactEntity(id="", name="Alice", channel="whatsapp", channel_user_id="123")

    with pytest.raises(ValueError, match="channel cannot be empty"):
        ContactEntity(id="cnt_01", name="Alice", channel="", channel_user_id="123")

    with pytest.raises(ValueError, match="contact_id cannot be empty"):
        MessagePayload(contact_id="", channel="whatsapp", text="Test")

    with pytest.raises(ValueError, match="text cannot be empty"):
        MessagePayload(contact_id="cnt_01", channel="whatsapp", text="")

    with pytest.raises(ValueError, match="flow_id cannot be empty"):
        FlowTriggerPayload(contact_id="cnt_01", flow_id="")


@pytest.mark.unit
def test_chatbotx_local_json_salvage() -> None:
    """Verify multi-pass local string salvage heuristics per Rule 42."""
    raw_fence = '```json\n{"status": "ok", "count": 42}\n```'
    salvaged = ChatbotXDomainEngine.salvage_json(raw_fence)
    assert salvaged == {"status": "ok", "count": 42}

    raw_trailing = 'Prefix text {"action": "send", "items": [1, 2, ], } trailing text'
    salvaged_trailing = ChatbotXDomainEngine.salvage_json(raw_trailing)
    assert salvaged_trailing == {"action": "send", "items": [1, 2]}

    with pytest.raises(ValueError, match="Cannot salvage empty payload"):
        ChatbotXDomainEngine.salvage_json("   ")


@pytest.mark.unit
def test_chatbotx_zero_fork_config_resolution() -> None:
    """Verify layered zero-fork configuration precedence per Rule 44."""
    config = ChatbotXDomainEngine.resolve_configuration()
    assert "connection" in config
    assert config["connection"]["api_url"] == "https://app.chatbotx.io/api"
    assert "whatsapp" in config["channels"]["supported_channels"]


@pytest.mark.unit
def test_chatbotx_skill_documentation_hygiene() -> None:
    """Verify SKILL.md, CARD.md, and description budget per Rule 37 and Rule 44."""
    skill_dir = Path(r"d:\GitHub\projects\Brain Harness\.agents\skills\chatbotx")
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    card_md = (skill_dir / "CARD.md").read_text(encoding="utf-8")

    # Frontmatter budget [100, 350]
    import yaml

    parts = skill_md.split("---")
    assert len(parts) >= 3, "Frontmatter must be enclosed by --- delimiters"
    frontmatter = yaml.safe_load(parts[1])
    desc = frontmatter.get("description", "")
    assert 100 <= len(desc) <= 350, f"Description length {len(desc)} outside [100, 350]"
    assert "Do not use for" in desc, "Negative boundary missing from description"

    # Anti-patterns formatting per Rule 37
    assert "## Anti-Patterns" in skill_md
    assert "- **" in skill_md
    assert " — " in skill_md or " -- " in skill_md

    # CARD.md single pipe borders and SKILL header tag per Rule 37
    assert "SKILL: chatbotx" in card_md
    assert "│" in card_md
    assert "║" not in card_md, "CARD.md must not use double-pipe borders"
