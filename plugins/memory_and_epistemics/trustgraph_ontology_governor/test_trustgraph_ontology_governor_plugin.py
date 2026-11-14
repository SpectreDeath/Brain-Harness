"""Plugin and IoC contract tests for plugin.trustgraph_ontology_governor."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.trustgraph_governor import TRUSTGRAPH_GOVERNOR_KEY, TrustGraphGovernorProtocol  # noqa: E402
from plugins.memory_and_epistemics.trustgraph_ontology_governor.main import (  # noqa: E402
    TrustGraphOntologyGovernorPlugin,
    plugin,
    tg_build_provenance_trace,
    tg_evaluate_shacl_policy,
    tg_score_laya_decision,
    tg_validate_ontology_triples,
)


@pytest.mark.asyncio
async def test_plugin_ioc_registration_and_validator() -> None:
    assert isinstance(plugin, TrustGraphOntologyGovernorPlugin)
    assert isinstance(plugin, TrustGraphGovernorProtocol)

    ctx = ServiceContext()
    await plugin.on_load(ctx)
    resolved = ctx.require(TRUSTGRAPH_GOVERNOR_KEY)
    assert resolved is plugin

    report = await PluginValidator().validate(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c for c in report.checks if not c.passed]}"


def test_plugin_entrypoint_functions() -> None:
    policy_res = tg_evaluate_shacl_policy(
        triples=[{"s": "urn:s1", "p": "ex:p", "o": "val"}],
        policies=[{"shape_uri": "urn:graph:policy#deny", "matched_subjects": ["urn:s1"]}],
    )
    assert policy_res["open_mode"] is False
    assert policy_res["blocked_subjects"] == ("urn:s1",)

    onto_res = tg_validate_ontology_triples(
        ontology={
            "classes": {"Entity": {}, "Person": {"subClassOf": ["Entity"]}},
            "object_properties": {"knows": {"domain": "Entity", "range": "Entity"}},
            "datatype_properties": {},
        },
        triples=[
            {
                "kind": "relationship",
                "s": "ex:a",
                "predicate": "knows",
                "o": "ex:b",
                "subject_type": "Person",
                "object_type": "Entity",
            }
        ],
    )
    assert onto_res["selector_bypassed"] is True
    assert len(onto_res["accepted_triples"]) == 1

    prov_res = tg_build_provenance_trace(
        question_id="q-plugin",
        query_text="Verify dual graphs",
        document_id="doc-1",
        prompt_tokens=10,
        completion_tokens=5,
    )
    assert prov_res["source_graph"] == "urn:graph:source"
    assert prov_res["retrieval_graph"] == "urn:graph:retrieval"
    assert prov_res["token_triples_appended"] is True

    laya_res = tg_score_laya_decision(
        question_type="choice",
        options=["a", "b"],
        logits_or_probs=[3.0, 0.5],
        temperature=0.2,
    )
    assert laya_res["clamped_temperature"] == 0.5
    assert laya_res["selected_index"] == 0
