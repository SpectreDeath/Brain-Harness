"""Phase 0.5: Verify exact live-vs-cached round-trip fidelity for all 7 snapshots."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import (  # noqa: E402
    SNAPSHOTS,
    VAULT,
    bootstrap,
    load_vault_model,
    spider,
    write_json,
)
from p00_snapshot import SNAPSHOT_TARGETS  # noqa: E402

bootstrap()


def _triple_set(model: Any) -> set[tuple[str, str, str]]:
    return {(a.relation.subject, a.relation.predicate, a.relation.object) for a in model.assertions.values()}


def main() -> int:
    from ontology_spider.api import load_model

    svc = spider()
    report: dict[str, Any] = {"all_passed": True, "snapshots": {}}

    for name, target_path in SNAPSHOT_TARGETS.items():
        snap_path = SNAPSHOTS / f"{name}.json"
        cached = load_model(snap_path)
        if name == "vault":
            live = load_vault_model()
        else:
            assert target_path is not None
            live = svc.load_repository_model(target_path, vault_dir=VAULT, max_depth=4, max_files_per_unit=60)

        cached_triples = _triple_set(cached)
        live_triples = _triple_set(live)
        missing_in_cached = sorted(live_triples - cached_triples)
        extra_in_cached = sorted(cached_triples - live_triples)

        entities_match = len(cached.entities) == len(live.entities)
        assertions_match = len(cached.assertions) == len(live.assertions)
        triples_match = cached_triples == live_triples
        passed = entities_match and assertions_match and triples_match

        if not passed:
            report["all_passed"] = False

        report["snapshots"][name] = {
            "passed": passed,
            "cached_entities": len(cached.entities),
            "live_entities": len(live.entities),
            "cached_assertions": len(cached.assertions),
            "live_assertions": len(live.assertions),
            "triples_match": triples_match,
            "missing_in_cached_count": len(missing_in_cached),
            "extra_in_cached_count": len(extra_in_cached),
            "sample_missing": missing_in_cached[:5],
            "sample_extra": extra_in_cached[:5],
        }
        print(
            f"{name}: passed={passed} "
            f"(ent {len(cached.entities)}=={len(live.entities)}, "
            f"asrt {len(cached.assertions)}=={len(live.assertions)}, "
            f"triples={triples_match})"
        )

    out = write_json(0, "roundtrip_check", report)
    print(f"Wrote roundtrip report: {out}")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
