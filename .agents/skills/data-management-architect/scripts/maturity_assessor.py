"""Data Management Maturity Assessor — evaluates organizational maturity from Level 0 to Level 5.

Aligns with DAMA-DMBOK / DAMA-DMM and Daniel García Solla's maturity roadmap framework.
Evaluates 6 capabilities: Governance, Architecture, Modeling, Quality, Security/Privacy, and DataOps.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


MATURITY_LEVEL_NAMES = {
    0: "Level 0: No Capability (Ad-hoc, chaotic actions)",
    1: "Level 1: Initial (Individual heroics, uncoordinated)",
    2: "Level 2: Managed (Documented, repeatable departmental processes)",
    3: "Level 3: Defined (Formalized enterprise policies and standards)",
    4: "Level 4: Measured (Quantitatively managed with SLAs and audits)",
    5: "Level 5: Optimized (Continuous automated improvement)",
}


@dataclass(slots=True)
class DimensionMaturity:
    """Maturity evaluation for a single data management capability."""

    dimension_id: str
    dimension_name: str
    current_level: int
    target_level: int
    gap: int
    strengths: list[str] = field(default_factory=list)
    remediations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "current_level": self.current_level,
            "target_level": self.target_level,
            "gap": self.gap,
            "strengths": self.strengths,
            "remediations": self.remediations,
        }


@dataclass(slots=True)
class MaturityReport:
    """Comprehensive organizational data management maturity assessment report."""

    organization_name: str
    overall_maturity_level: float
    target_maturity_level: int
    maturity_stage: str
    dimension_scores: dict[str, DimensionMaturity]
    prioritized_roadmap: list[str] = field(default_factory=list)

    def generate_summary_markdown(self) -> str:
        return self.generate_markdown()

    @property
    def roadmap_recommendations(self) -> list[dict[str, Any]]:
        return [{"recommendation": r} for r in self.prioritized_roadmap]

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_name": self.organization_name,
            "overall_maturity_level": round(self.overall_maturity_level, 2),
            "target_maturity_level": self.target_maturity_level,
            "maturity_stage": self.maturity_stage,
            "dimensions": {
                dim_id: {
                    "name": d.dimension_name,
                    "current_level": d.current_level,
                    "target_level": d.target_level,
                    "gap": d.gap,
                    "strengths": d.strengths,
                    "remediations": d.remediations,
                }
                for dim_id, d in self.dimension_scores.items()
            },
            "prioritized_roadmap": self.prioritized_roadmap,
        }

    def generate_markdown(self) -> str:
        lines = [
            f"# Data Management Maturity Assessment: {self.organization_name}",
            f"**Overall Level**: {self.overall_maturity_level:.1f} / 5.0 ({self.maturity_stage}) | **Target**: Level {self.target_maturity_level}.0",
            "",
            "## Capability Dimension Scorecard",
            "| Capability Dimension | Current Level | Target | Gap | Status |",
            "|---|---|---|---|---|",
        ]

        for dim_id, d in sorted(self.dimension_scores.items()):
            status = "ON TARGET" if d.gap <= 0 else f"GAP: -{d.gap}"
            lines.append(f"| **{d.dimension_name}** | Level {d.current_level} | Level {d.target_level} | {d.gap} | {status} |")

        lines.extend([
            "",
            "## Strategic Roadmap & Priority Remediations",
        ])
        for idx, item in enumerate(self.prioritized_roadmap, 1):
            lines.append(f"{idx}. {item}")

        return "\n".join(lines)


class MaturityAssessor:
    """Assesses organizational capability scores and synthesizes maturity roadmaps."""

    DEFAULT_QUESTIONS = {
        "data_governance": {
            "name": "Data Governance & Stewardship",
            "criteria": [
                "Are Data Owners and Data Stewards formally designated with explicit decision rights?",
                "Are data policies and RACI matrices published enterprise-wide?",
                "Does a Data Governance Council actively resolve cross-domain data conflicts?",
                "Are governance metrics tracked to evaluate policy compliance?",
                "Is governance automated through metadata catalog integrations?",
            ],
        },
        "data_architecture": {
            "name": "Data Architecture & Lakehouse",
            "criteria": [
                "Is there an enterprise data architecture blueprint separating operational and analytical systems?",
                "Are data domains clearly defined with bounded contexts?",
                "Is a multi-tier Medallion architecture (Bronze/Silver/Gold) implemented?",
                "Is data lineage systematically mapped from source to report?",
                "Are data pipelines decoupled into federated domain data products?",
            ],
        },
        "data_modeling": {
            "name": "Data Modeling & Design",
            "criteria": [
                "Are conceptual data models documented with business stakeholders?",
                "Are logical models normalized and technology-independent?",
                "Are physical models optimized for dimensional star schemas and partitioning?",
                "Are Slowly Changing Dimensions (SCD) formally governed?",
                "Are data models automated via version-controlled CI/CD migrations?",
            ],
        },
        "data_quality": {
            "name": "Data Quality Management",
            "criteria": [
                "Are basic data profiling checks performed on raw inputs?",
                "Are quality rules documented for required and critical fields?",
                "Are datasets tested across all 6 DAMA quality dimensions?",
                "Are quality metrics continuously monitored with alerting SLAs?",
                "Are automated circuit-breakers and self-healing pipelines in place?",
            ],
        },
        "data_security_privacy": {
            "name": "Data Security, Ethics & Privacy",
            "criteria": [
                "Are datasets classified into security tiers (Public, Internal, Confidential, Restricted)?",
                "Is Role-Based Access Control (RBAC) enforced with least privilege?",
                "Is sensitive personal data masked, pseudonymized, or encrypted?",
                "Are privacy regulations (GDPR/CCPA) audits conducted regularly?",
                "Are ethical risk assessments embedded into all AI and analytical models?",
            ],
        },
        "data_engineering_ops": {
            "name": "Data Engineering & DataOps",
            "criteria": [
                "Are data pipeline jobs automated on schedules or event triggers?",
                "Are producer-consumer expectations codified in Open Data Contracts?",
                "Is Data Observability active across the 5 pillars (freshness, volume, schema, dist, lineage)?",
                "Are data tests executed automatically in CI/CD before deployment?",
                "Is data versioning and reproducible historical replay operational?",
            ],
        },
    }

    def __init__(self, target_level: int = 4) -> None:
        self.target_level = target_level

    def evaluate_answers(
        self,
        scores: dict[str, int],
        organization_name: str = "Enterprise Organization",
    ) -> MaturityReport:
        """Evaluate pre-scored capability levels (0 to 5) across the 6 dimensions."""
        dim_results: dict[str, DimensionMaturity] = {}
        total_score = 0.0

        for dim_id, q_data in self.DEFAULT_QUESTIONS.items():
            lvl = int(scores.get(dim_id, 1))
            lvl = max(0, min(5, lvl))
            total_score += lvl

            gap = max(0, self.target_level - lvl)
            strengths: list[str] = []
            remediations: list[str] = []

            for i in range(lvl):
                if i < len(q_data["criteria"]):
                    strengths.append(q_data["criteria"][i])

            for i in range(lvl, self.target_level):
                if i < len(q_data["criteria"]):
                    remediations.append(q_data["criteria"][i])

            dim_results[dim_id] = DimensionMaturity(
                dimension_id=dim_id,
                dimension_name=q_data["name"],
                current_level=lvl,
                target_level=self.target_level,
                gap=gap,
                strengths=strengths,
                remediations=remediations,
            )

        overall = total_score / len(self.DEFAULT_QUESTIONS)
        stage_name = MATURITY_LEVEL_NAMES.get(int(round(overall)), "Level 1: Initial")

        # Build prioritized roadmap
        roadmap: list[str] = []
        # Sort dimensions by largest gap descending
        sorted_dims = sorted(dim_results.values(), key=lambda d: d.gap, reverse=True)
        for d in sorted_dims:
            for rem in d.remediations:
                roadmap.append(f"[{d.dimension_name}] {rem}")

        return MaturityReport(
            organization_name=organization_name,
            overall_maturity_level=overall,
            target_maturity_level=self.target_level,
            maturity_stage=stage_name,
            dimension_scores=dim_results,
            prioritized_roadmap=roadmap,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate organizational Data Management Maturity.")
    parser.add_argument("--scores", help="JSON string or path with capability level scores (0 to 5)")
    parser.add_argument("--target", type=int, default=4, help="Target maturity level (default: 4)")
    parser.add_argument("--org", default="University & Mobility Enterprise", help="Organization name")
    parser.add_argument("--output", help="Optional path to output JSON report")
    parser.add_argument("--markdown", help="Optional path to output Markdown report")
    args = parser.parse_args()

    scores = {}
    if args.scores:
        p = Path(args.scores)
        if p.exists():
            scores = json.loads(p.read_text(encoding="utf-8"))
        else:
            scores = json.loads(args.scores)
    else:
        # Default baseline evaluation for testing
        scores = {
            "data_governance": 2,
            "data_architecture": 3,
            "data_modeling": 3,
            "data_quality": 2,
            "data_security_privacy": 3,
            "data_engineering_ops": 2,
        }

    assessor = MaturityAssessor(target_level=args.target)
    report = assessor.evaluate_answers(scores, organization_name=args.org)

    print(report.generate_markdown())

    if args.output:
        Path(args.output).write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(f"\nSaved report JSON to: {args.output}")
    if args.markdown:
        Path(args.markdown).write_text(report.generate_markdown(), encoding="utf-8")
        print(f"Saved markdown report to: {args.markdown}")


if __name__ == "__main__":
    main()
