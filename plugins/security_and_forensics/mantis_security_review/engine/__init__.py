"""Engine subpackage for Google Mantis security review and triage."""

from __future__ import annotations

from plugins.security_and_forensics.mantis_security_review.engine.auditor import (
    plan_review,
    research_audit,
)
from plugins.security_and_forensics.mantis_security_review.engine.chains import (
    calibrate_risk,
    chain_exploits,
)
from plugins.security_and_forensics.mantis_security_review.engine.core import MantisReviewEngine
from plugins.security_and_forensics.mantis_security_review.engine.db import (
    compute_stable_signature,
    init_okf_db,
)
from plugins.security_and_forensics.mantis_security_review.engine.models import (
    MANTIS_SECURITY_REVIEW_KEY,
    ExploitChain,
    ExploitStep,
    MantisFinding,
    MantisSecurityReviewService,
)
from plugins.security_and_forensics.mantis_security_review.engine.reporter import generate_report
from plugins.security_and_forensics.mantis_security_review.engine.resolvers import (
    resolve_mantis_security_review,
)
from plugins.security_and_forensics.mantis_security_review.engine.triage import (
    critic_filter,
    dedupe_ladder,
    review_gate,
)
from plugins.security_and_forensics.mantis_security_review.engine.vcs import (
    directory_summary,
    history_scan,
)

__all__ = [
    "ExploitChain",
    "ExploitStep",
    "MANTIS_SECURITY_REVIEW_KEY",
    "MantisFinding",
    "MantisReviewEngine",
    "MantisSecurityReviewService",
    "calibrate_risk",
    "chain_exploits",
    "compute_stable_signature",
    "critic_filter",
    "dedupe_ladder",
    "directory_summary",
    "generate_report",
    "history_scan",
    "init_okf_db",
    "plan_review",
    "research_audit",
    "resolve_mantis_security_review",
    "review_gate",
]
