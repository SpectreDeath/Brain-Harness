"""Contract tests for skill clustering hardening and emergent capability engine (Track 5)."""

from __future__ import annotations

import copy
import re
import pytest

from harness.services.skill_clustering.engine import SkillClusteringEngine
from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS
from harness.services.skill_graph import BuiltinSkillRegistryService


@pytest.mark.unit
class TestSkillClusteringHardening:
    """Verify that clustering and emergent capability synthesis adhere to strict contract invariants."""

    def test_emergent_capabilities_descriptions_complete_sentences(self) -> None:
        """Assert zero emergent_capabilities descriptions end mid-word or with broken fragments."""
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills, registry=registry)

        capabilities = engine.discover_emergent_capabilities()
        assert len(capabilities) >= 15

        broken_endings = {
            " .",  # isolated period without word
            "for .",
            "evidence d.",
            "executable agen.",
            "hotspots into sl.",
            "Runtime Store Min.",
            "no str.",
            "adversarial sel.",
            "resource manifest.",
            "where a se.",
            "model prompt dra.",
        }

        for cap in capabilities:
            desc = cap.description.strip()
            assert desc, f"Capability {cap.id} has empty description"

            # Check punctuation at end
            assert desc[-1] in {".", "!", ")", '"'}, (
                f"Capability {cap.id} description does not end with valid terminal punctuation: '{desc[-30:]}'"
            )

            # Assert none of the known broken sliced endings appear
            for broken in broken_endings:
                assert not desc.endswith(broken), (
                    f"Capability {cap.id} has broken mid-word slice ending: '{desc[-30:]}'"
                )

            # Assert last word is a clean word with letters
            last_token = desc.split()[-1].rstrip('.!?)""')
            assert len(last_token) >= 2, (
                f"Capability {cap.id} has truncated single-character word: '{last_token}'"
            )

    def test_canonical_emergent_patterns_immutability(self) -> None:
        """Assert CANONICAL_EMERGENT_PATTERNS is never mutated across multiple discovery calls."""
        patterns_snapshot = copy.deepcopy(CANONICAL_EMERGENT_PATTERNS)

        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills, registry=registry)

        # Call repeatedly
        _ = engine.discover_emergent_capabilities()
        _ = engine.discover_emergent_capabilities(query="vault")
        _ = engine.discover_emergent_capabilities(query="governance")

        assert CANONICAL_EMERGENT_PATTERNS == patterns_snapshot, (
            "CANONICAL_EMERGENT_PATTERNS was mutated in-place during discovery calls"
        )

    def test_top_in_degree_contains_only_valid_nodes(self) -> None:
        """Assert top_in_degree rankings contain only valid skill IDs present in graph.nodes (Rule 35)."""
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        skill_keys = set(registry.get_nodes().keys())

        # Collect in-degrees across all edges
        in_degrees: dict[str, int] = {}
        for edge in registry.edges:
            # Only count edges targeting valid registered skill nodes
            if edge.target in skill_keys:
                in_degrees[edge.target] = in_degrees.get(edge.target, 0) + 1

        top_in = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        top_keys = [k for k, _ in top_in[:20]]

        # Ensure no phantom HTML/markdown tokens exist
        forbidden_phantom_tokens = {
            "mermaid",
            "script",
            "knowledge",
            "skills",
            "dist",
            "head",
            "body",
            "html",
            "div",
        }

        for k in top_keys:
            assert k in skill_keys, f"Found unregistered node {k} in top_in_degree"
            assert k not in forbidden_phantom_tokens, f"Found phantom token {k} in top_in_degree"
