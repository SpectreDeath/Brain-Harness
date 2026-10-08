"""Skill commands — pure async and sync programmatic entry points for skill knowledge and authoring.

Provides an authoritative seam for indexing, routing, chain discovery, topology inspection,
scaffolding, and validation across agent skills. Delegates to BuiltinSkillRegistryService.
"""

from __future__ import annotations

from harness.commands.skills.cli import skills_group
from harness.commands.skills.discovery import (
    export_skill_graph_visual_cmd,
    index_skills_cmd,
    list_skills_cmd,
    run_skill_cmd,
    scaffold_skill_cmd,
    validate_skill_cmd,
)
from harness.commands.skills.routing import (
    compile_guidance_cmd,
    intercept_action_cmd,
    route_skills_cmd,
    select_skills_cmd,
)
from harness.commands.skills.seams import (
    _DEFAULT_GRAPH,
    _DEFAULT_REGISTRY,
    get_skill_graph,
    get_skill_intelligence,
    get_skill_registry,
)
from harness.commands.skills.topology import (
    check_chain_feasibility_cmd,
    cluster_skills_cmd,
    discover_capabilities_cmd,
    find_skill_chain_cmd,
    get_prerequisite_closure_cmd,
    get_skill_topology_cmd,
)

__all__ = [
    "_DEFAULT_GRAPH",
    "_DEFAULT_REGISTRY",
    "check_chain_feasibility_cmd",
    "cluster_skills_cmd",
    "compile_guidance_cmd",
    "discover_capabilities_cmd",
    "export_skill_graph_visual_cmd",
    "find_skill_chain_cmd",
    "get_prerequisite_closure_cmd",
    "get_skill_graph",
    "get_skill_intelligence",
    "get_skill_registry",
    "get_skill_topology_cmd",
    "index_skills_cmd",
    "intercept_action_cmd",
    "list_skills_cmd",
    "route_skills_cmd",
    "run_skill_cmd",
    "scaffold_skill_cmd",
    "select_skills_cmd",
    "skills_group",
    "validate_skill_cmd",
]
