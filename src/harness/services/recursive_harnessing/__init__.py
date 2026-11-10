"""Recursive harnessing: Propose-Probe-Compose refinement, blind selection, experience library.

Distilled from google/harness2 (arXiv 2610.14224, Apache-2.0). Public surface of the package.
"""

from harness.services.recursive_harnessing.errors import ProposerError, SelectorError
from harness.services.recursive_harnessing.guards import (
    GRADER_VERDICT_MARKERS,
    EvidenceLeakError,
    TraversalDepthError,
    assert_no_leak_paths,
    assert_no_verdicts,
    assert_tree_clean,
    scrub_env,
)
from harness.services.recursive_harnessing.identity import (
    call_fingerprint,
    fingerprint_dir,
    fingerprint_tree,
    inputs_fingerprint,
    is_complete,
    mark_complete,
    read_mark,
    why_not,
)
from harness.services.recursive_harnessing.keys import (
    EVIDENCE_ISOLATION_SERVICE_KEY,
    RECURSIVE_REFINER_SERVICE_KEY,
)
from harness.services.recursive_harnessing.ledger import (
    BudgetError,
    BudgetLedger,
    expected_rollouts,
    expected_sessions,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary, library_root
from harness.services.recursive_harnessing.models import (
    BRAIN_SURFACE,
    ModeResult,
    ProposalReply,
    RunView,
    Selection,
    SelectorChoice,
    Stage,
    SurfaceSpec,
    Tree,
)
from harness.services.recursive_harnessing.protocols import (
    CandidateSelector,
    EvidenceIsolationService,
    HarnessProposer,
    RecursiveRefinerService,
    TaskAdapter,
)
from harness.services.recursive_harnessing.recursion import run_mode, run_parallel, run_sequential
from harness.services.recursive_harnessing.resolvers import (
    resolve_evidence_isolation,
    resolve_recursive_refiner,
)
from harness.services.recursive_harnessing.selection import (
    assign_ids,
    blind_select,
    selection_pool,
    trivial_selection,
)
from harness.services.recursive_harnessing.service import (
    DefaultEvidenceIsolationService,
    DefaultRecursiveRefinerService,
)
from harness.services.recursive_harnessing.stage import run_stage

__all__ = [
    "BRAIN_SURFACE",
    "EVIDENCE_ISOLATION_SERVICE_KEY",
    "GRADER_VERDICT_MARKERS",
    "RECURSIVE_REFINER_SERVICE_KEY",
    "BudgetError",
    "BudgetLedger",
    "CandidateSelector",
    "DefaultEvidenceIsolationService",
    "DefaultRecursiveRefinerService",
    "EvidenceIsolationService",
    "EvidenceLeakError",
    "ExperienceLibrary",
    "HarnessProposer",
    "ModeResult",
    "ProposalReply",
    "ProposerError",
    "RecursiveRefinerService",
    "RunView",
    "Selection",
    "SelectorChoice",
    "SelectorError",
    "Stage",
    "SurfaceSpec",
    "TaskAdapter",
    "TraversalDepthError",
    "Tree",
    "assert_no_leak_paths",
    "assert_no_verdicts",
    "assert_tree_clean",
    "assign_ids",
    "blind_select",
    "call_fingerprint",
    "expected_rollouts",
    "expected_sessions",
    "fingerprint_dir",
    "fingerprint_tree",
    "inputs_fingerprint",
    "is_complete",
    "library_root",
    "mark_complete",
    "read_mark",
    "resolve_evidence_isolation",
    "resolve_recursive_refiner",
    "run_mode",
    "run_parallel",
    "run_sequential",
    "run_stage",
    "scrub_env",
    "selection_pool",
    "trivial_selection",
    "why_not",
]
