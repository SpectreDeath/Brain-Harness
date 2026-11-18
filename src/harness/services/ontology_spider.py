"""Micro-kernel Ontology-Spider service (Rule 49) with entropy & epistemic auditing."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import importlib
import inspect
from pathlib import Path
from typing import Any, Protocol, Union, runtime_checkable

from harness.kernel.context import ServiceKey

try:
    from ontology_spider.api import (
        evaluate_competency_questions,
        export_model,
        rank_discriminating_attributes,
        run_query,
        validate_model,
    )

    HAS_ONTOLOGY_SPIDER = True
except ModuleNotFoundError:
    HAS_ONTOLOGY_SPIDER = False
    evaluate_competency_questions = None  # type: ignore[assignment]
    export_model = None  # type: ignore[assignment]
    rank_discriminating_attributes = None  # type: ignore[assignment]
    run_query = None  # type: ignore[assignment]
    validate_model = None  # type: ignore[assignment]


@dataclass(slots=True, frozen=True)
class AttributeEntropyRank:
    """Slotted immutable value object ranking an entity attribute by information gain."""

    attribute: str
    entropy_bits: float
    coverage: float
    distinct_values: int
    laya_score: float
    classification_score: float = 0.0
    is_identifier_like: bool = False

    def __post_init__(self) -> None:
        if (
            self.entropy_bits < 0.0
            or not (0.0 <= self.coverage <= 1.0)
            or self.distinct_values < 0
            or self.laya_score < 0.0
            or self.classification_score < 0.0
        ):
            raise ValueError("AttributeEntropyRank metrics out of valid range")


@dataclass(slots=True, frozen=True)
class CompetencyScorecardReport:
    """Slotted immutable Gruber 5-criteria competency question scorecard."""

    vault_uri: str
    total_questions: int
    answered_questions: int
    violation_count: int
    clarity: float
    coherence: float
    extendibility: float
    minimal_encoding_bias: float
    minimal_commitment: float
    overall_score: float
    question_results: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        if self.total_questions < 0 or self.answered_questions < 0 or self.violation_count < 0:
            raise ValueError("CompetencyScorecardReport counts must be non-negative")
        if not (0.0 <= self.overall_score <= 1.0):
            raise ValueError("CompetencyScorecardReport.overall_score must be in [0.0, 1.0]")


@dataclass(slots=True, frozen=True)
class EpistemicVaultAuditReport:
    """Slotted immutable federated epistemic audit over a Knowledge Vault."""

    vault_uri: str
    entities_count: int
    assertions_count: int
    structural_violations: tuple[dict[str, Any], ...]
    unverified_entity_ids: tuple[str, ...]
    top_discriminating_attributes: tuple[AttributeEntropyRank, ...]
    gruber_coherence: float
    status: str
    verified_entities_count: int = 0
    unverified_entities_count: int = 0
    isnad_verification_rate: float = 1.0
    epistemic_status: str = "verified"

    def __post_init__(self) -> None:
        if (
            self.entities_count < 0
            or self.assertions_count < 0
            or self.verified_entities_count < 0
            or self.unverified_entities_count < 0
            or not (0.0 <= self.isnad_verification_rate <= 1.0)
        ):
            raise ValueError("EpistemicVaultAuditReport counts/rates out of bounds")
        if self.status not in ("verified", "violations_detected"):
            raise ValueError("EpistemicVaultAuditReport.status must be 'verified' or 'violations_detected'")
        if self.epistemic_status not in ("verified", "partial_unverified", "violations_detected"):
            raise ValueError("EpistemicVaultAuditReport.epistemic_status invalid")


@dataclass(slots=True, frozen=True)
class RepoOntologyAnalysisReport:
    """Slotted immutable ontology analysis report over a code or research repository."""

    repo_root: str
    resolved_root: str
    entities_count: int
    assertions_count: int
    projects_count: int
    cycle_violations: tuple[dict[str, Any], ...]
    dependency_hubs: tuple[tuple[str, int], ...]
    top_discriminating_attributes: tuple[AttributeEntropyRank, ...]
    unlearned_tested_projects: tuple[str, ...]
    gruber_scorecard: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.repo_root.strip() or not self.resolved_root.strip():
            raise ValueError("RepoOntologyAnalysisReport requires non-empty repo paths")
        if self.entities_count < 0 or self.assertions_count < 0 or self.projects_count < 0:
            raise ValueError("RepoOntologyAnalysisReport counts must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "resolved_root": self.resolved_root,
            "entities_count": self.entities_count,
            "assertions_count": self.assertions_count,
            "projects_count": self.projects_count,
            "cycle_violations": list(self.cycle_violations),
            "dependency_hubs": [[h, c] for h, c in self.dependency_hubs],
            "top_discriminating_attributes": [
                {
                    "attribute": r.attribute,
                    "entropy_bits": r.entropy_bits,
                    "coverage": r.coverage,
                    "distinct_values": r.distinct_values,
                    "laya_score": r.laya_score,
                    "classification_score": r.classification_score,
                    "is_identifier_like": r.is_identifier_like,
                }
                for r in self.top_discriminating_attributes
            ],
            "unlearned_tested_projects": list(self.unlearned_tested_projects),
            "gruber_scorecard": dict(self.gruber_scorecard),
        }


@dataclass(slots=True, frozen=True)
class PortfolioRepoSummary:
    """Compact summary for a single repository or nested monorepo within a portfolio."""

    repo_name: str
    repo_root: str
    resolved_root: str
    projects_count: int
    entities_count: int
    assertions_count: int
    cycle_count: int
    unlearned_tested_count: int
    gruber_overall_score: float
    top_hubs: tuple[tuple[str, int], ...] = ()
    unlearned_tested_sample: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.repo_name.strip() or not self.resolved_root.strip():
            raise ValueError("PortfolioRepoSummary requires non-empty repo_name and resolved_root")
        if self.projects_count < 0 or self.entities_count < 0 or self.assertions_count < 0:
            raise ValueError("PortfolioRepoSummary counts must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "repo_root": self.repo_root,
            "resolved_root": self.resolved_root,
            "projects_count": self.projects_count,
            "entities_count": self.entities_count,
            "assertions_count": self.assertions_count,
            "cycle_count": self.cycle_count,
            "unlearned_tested_count": self.unlearned_tested_count,
            "gruber_overall_score": self.gruber_overall_score,
            "top_hubs": [[h, c] for h, c in self.top_hubs],
            "unlearned_tested_sample": list(self.unlearned_tested_sample),
        }


@dataclass(slots=True, frozen=True)
class PortfolioOntologyAnalysisReport:
    """Slotted immutable aggregated ontology report across a multi-repo portfolio root."""

    portfolio_root: str
    repos_count: int
    total_projects_count: int
    total_entities_count: int
    total_assertions_count: int
    total_cycle_violations: int
    top_unlearned_targets: tuple[str, ...]
    repo_summaries: tuple[PortfolioRepoSummary, ...]

    def __post_init__(self) -> None:
        if not self.portfolio_root.strip():
            raise ValueError("PortfolioOntologyAnalysisReport requires non-empty portfolio_root")
        if self.repos_count < 0 or self.total_projects_count < 0:
            raise ValueError("PortfolioOntologyAnalysisReport counts must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_root": self.portfolio_root,
            "repos_count": self.repos_count,
            "total_projects_count": self.total_projects_count,
            "total_entities_count": self.total_entities_count,
            "total_assertions_count": self.total_assertions_count,
            "total_cycle_violations": self.total_cycle_violations,
            "top_unlearned_targets": list(self.top_unlearned_targets),
            "repo_summaries": [r.to_dict() for r in self.repo_summaries],
        }


@runtime_checkable
class OntologySpiderProtocol(Protocol):
    """Typed micro-kernel contract for ontological vault loading, querying, and auditing."""

    def load_vault(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> Any: ...
    def query(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        query_str: str,
        *,
        rank_by_distance: bool = False,
        as_of: str | None = None,
        min_confidence: float = 0.0,
        max_results: int | None = 5000,
    ) -> dict[str, Any]: ...
    def validate(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> list[dict[str, Any]]: ...
    def export(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        format: str = "json",
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> str: ...
    def rank_attributes(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        candidate_ids: Sequence[str] | None = None,
        *,
        as_of: str | None = None,
    ) -> tuple[AttributeEntropyRank, ...]: ...
    def evaluate_competency(
        self, vault_source: Union[str, Path, dict[str, Any]], questions: Sequence[str], *, as_of: str | None = None
    ) -> CompetencyScorecardReport: ...
    def audit_vault_epistemics(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> EpistemicVaultAuditReport: ...
    def analyze_repository(
        self,
        repo_path: Union[str, Path],
        *,
        vault_dir: Union[str, Path] | None = None,
        max_depth: int = 4,
        max_files_per_unit: int | None = 120,
    ) -> RepoOntologyAnalysisReport: ...
    def analyze_portfolio(
        self,
        portfolio_path: Union[str, Path],
        *,
        vault_dir: Union[str, Path] | None = None,
        max_depth: int = 3,
        max_files_per_unit: int | None = 60,
    ) -> PortfolioOntologyAnalysisReport: ...
    def compute_blast_radius(
        self,
        model: Any,
        *,
        predicate: str = "depends_on_project",
    ) -> dict[str, tuple[str, ...]]: ...


ONTOLOGY_SPIDER_SERVICE_KEY: ServiceKey[OntologySpiderProtocol] = ServiceKey("memory.ontology_spider_service")


def _require_engine() -> None:
    if not HAS_ONTOLOGY_SPIDER:
        raise RuntimeError(
            "Ontology-Spider engine is not installed. Run: pip install -e <path-to-Ontology-Spider> "
            "(see plugins/memory_and_epistemics/ontology_spider/README.md)."
        )


def _to_entropy_ranks(raw_ranks: Sequence[dict[str, Any]]) -> tuple[AttributeEntropyRank, ...]:
    return tuple(
        AttributeEntropyRank(
            attribute=str(item["attribute"]),
            entropy_bits=float(item["entropy_bits"]),
            coverage=float(item["coverage"]),
            distinct_values=int(item["distinct_values"]),
            laya_score=float(item["laya_score"]),
            classification_score=float(item.get("classification_score", item["laya_score"])),
            is_identifier_like=bool(item.get("is_identifier_like", False)),
        )
        for item in raw_ranks
    )


class OntologySpiderKernelService(OntologySpiderProtocol):
    """In-memory micro-kernel service backed by Ontology-Spider and HarnessVaultModelSource."""

    def load_vault(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> Any:
        _require_engine()
        HarnessVaultModelSource = importlib.import_module(
            "plugins.memory_and_epistemics.ontology_spider.adapter"
        ).HarnessVaultModelSource

        return HarnessVaultModelSource(vault_source, as_of=as_of, min_confidence=min_confidence).load()

    def query(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        query_str: str,
        *,
        rank_by_distance: bool = False,
        as_of: str | None = None,
        min_confidence: float = 0.0,
        max_results: int | None = 5000,
    ) -> dict[str, Any]:
        model = self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence)
        if max_results is not None and "max_results" in inspect.signature(run_query).parameters:
            raw = run_query(model, query_str, max_results=max_results).to_dict()
        elif max_results is not None:
            from ontology_spider.engine import Session
            from ontology_spider.prolog.reasoner import PrologReasoner
            from ontology_spider.reasoning.python_backend import PythonReasoner

            prolog = PrologReasoner(max_results=max_results)
            reasoner = prolog if prolog.is_available else PythonReasoner()
            results = Session(model=model, reasoner=reasoner).execute(query_str)
            raw = (
                results[-1].to_dict()
                if results
                else {
                    "query": query_str,
                    "statement_type": "query",
                    "summary": "No results.",
                    "answers": [],
                    "explanation": None,
                }
            )
        else:
            raw = run_query(model, query_str).to_dict()
        if not rank_by_distance:
            return raw
        reranked: list[dict[str, Any]] = []
        for ans in raw.get("answers") or []:
            item = dict(ans)
            hop = max(0, len(item.get("path") or []) - 1)
            item["hop_distance"] = hop
            item["distance_score"] = round(1.0 / (1.0 + hop), 4)
            reranked.append(item)
        reranked.sort(key=lambda entry: (int(entry["hop_distance"]), str(entry.get("value", ""))))
        raw["answers"] = reranked
        return raw

    def validate(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> list[dict[str, Any]]:
        return validate_model(self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence))

    def export(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        format: str = "json",
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> str:
        return export_model(self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence), format=format)

    def rank_attributes(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        candidate_ids: Sequence[str] | None = None,
        *,
        as_of: str | None = None,
    ) -> tuple[AttributeEntropyRank, ...]:
        return _to_entropy_ranks(
            rank_discriminating_attributes(self.load_vault(vault_source, as_of=as_of), candidate_ids)
        )

    def evaluate_competency(
        self, vault_source: Union[str, Path, dict[str, Any]], questions: Sequence[str], *, as_of: str | None = None
    ) -> CompetencyScorecardReport:
        data = evaluate_competency_questions(self.load_vault(vault_source, as_of=as_of), questions)
        return CompetencyScorecardReport(
            vault_uri=str(data["uri"]),
            total_questions=int(data["total_questions"]),
            answered_questions=int(data["answered_questions"]),
            violation_count=int(data["violation_count"]),
            clarity=float(data["clarity"]),
            coherence=float(data["coherence"]),
            extendibility=float(data["extendibility"]),
            minimal_encoding_bias=float(data["minimal_encoding_bias"]),
            minimal_commitment=float(data["minimal_commitment"]),
            overall_score=float(data["overall_score"]),
            question_results=tuple(data["question_results"]),
        )

    def audit_vault_epistemics(
        self, vault_source: Union[str, Path, dict[str, Any]], *, as_of: str | None = None, min_confidence: float = 0.0
    ) -> EpistemicVaultAuditReport:
        model = self.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence)
        violations = tuple(validate_model(model))
        verified_ids = [eid for eid, ent in model.entities.items() if ent.attributes.get("isnad_verified") is True]
        unverified = tuple(
            sorted(eid for eid, ent in model.entities.items() if ent.attributes.get("isnad_verified") is False)
        )
        verified_count = len(verified_ids)
        unverified_count = len(unverified)
        denom = verified_count + unverified_count
        ver_rate = round(verified_count / denom, 4) if denom > 0 else 1.0
        ranked = _to_entropy_ranks(rank_discriminating_attributes(model)[:5])
        coherence = 1.0 if not violations else round(max(0.0, 1.0 - 0.25 * len(violations)), 4)
        if violations:
            ep_status = "violations_detected"
        elif unverified:
            ep_status = "partial_unverified"
        else:
            ep_status = "verified"
        return EpistemicVaultAuditReport(
            vault_uri=model.uri,
            entities_count=len(model.entities),
            assertions_count=len(model.assertions),
            structural_violations=violations,
            unverified_entity_ids=unverified,
            top_discriminating_attributes=ranked,
            gruber_coherence=coherence,
            status="violations_detected" if violations else "verified",
            verified_entities_count=verified_count,
            unverified_entities_count=unverified_count,
            isnad_verification_rate=ver_rate,
            epistemic_status=ep_status,
        )

    def analyze_repository(
        self,
        repo_path: Union[str, Path],
        *,
        vault_dir: Union[str, Path] | None = None,
        max_depth: int = 4,
        max_files_per_unit: int | None = 120,
    ) -> RepoOntologyAnalysisReport:
        """Build a formal OntologyModel from a repository and extract cycles, hubs, entropy, and unlearned gaps."""
        _require_engine()
        from ontology_spider.engine import Session
        from ontology_spider.reasoning.python_backend import PythonReasoner

        RepoOntologyModelSource = importlib.import_module(
            "plugins.memory_and_epistemics.ontology_spider.repo_adapter"
        ).RepoOntologyModelSource

        source = RepoOntologyModelSource(
            repo_path,
            vault_dir=vault_dir,
            max_depth=max_depth,
            max_files_per_unit=max_files_per_unit,
        )
        model = source.load()
        violations = validate_model(model)
        cycle_violations = tuple(v for v in violations if v.get("check_type") == "cycle_violation")

        hub_counts: dict[str, int] = {}
        for asrt in model.query(predicate="depends_on_project"):
            target = asrt.relation.object
            hub_counts[target] = hub_counts.get(target, 0) + 1
        hubs = tuple(sorted(hub_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20])

        project_ids = [eid for eid, ent in model.entities.items() if "raw_name" in ent.attributes]
        ranked = _to_entropy_ranks(rank_discriminating_attributes(model, project_ids)[:8])

        sess = Session(model=model, reasoner=PythonReasoner())
        unlearned_res = sess.execute(
            "query recommend research_project [has_tests=true, harness_learned=false, is_generic_unit=false]"
        )[-1]
        unlearned_tested = tuple(sorted(str(a["value"]) for a in unlearned_res.answers))

        scorecard = evaluate_competency_questions(
            model,
            [
                "query recommend research_project",
                "query count recommend research_project [has_tests=true]",
            ],
        )
        compact_scorecard = {k: v for k, v in scorecard.items() if k != "question_results"}

        return RepoOntologyAnalysisReport(
            repo_root=str(source.repo_path),
            resolved_root=str(source.resolved_root),
            entities_count=len(model.entities),
            assertions_count=len(model.assertions),
            projects_count=len(project_ids),
            cycle_violations=cycle_violations,
            dependency_hubs=hubs,
            top_discriminating_attributes=ranked,
            unlearned_tested_projects=unlearned_tested,
            gruber_scorecard=compact_scorecard,
        )

    def load_repository_model(
        self,
        repo_path: Union[str, Path],
        *,
        vault_dir: Union[str, Path] | None = None,
        max_depth: int = 4,
        max_files_per_unit: int | None = 120,
    ) -> Any:
        """Load a repository or nested monorepo into an OntologyModel via RepoOntologyModelSource."""
        _require_engine()
        RepoOntologyModelSource = importlib.import_module(
            "plugins.memory_and_epistemics.ontology_spider.repo_adapter"
        ).RepoOntologyModelSource
        return RepoOntologyModelSource(
            repo_path,
            vault_dir=vault_dir,
            max_depth=max_depth,
            max_files_per_unit=max_files_per_unit,
        ).load()

    def query_model(
        self,
        model: Any,
        query_str: str,
        *,
        rank_by_distance: bool = False,
        max_results: int | None = 5000,
    ) -> dict[str, Any]:
        """Execute a .dialog query directly on a pre-loaded OntologyModel."""
        _require_engine()
        if max_results is not None and "max_results" in inspect.signature(run_query).parameters:
            raw = run_query(model, query_str, max_results=max_results).to_dict()
        elif max_results is not None:
            from ontology_spider.engine import Session
            from ontology_spider.prolog.reasoner import PrologReasoner
            from ontology_spider.reasoning.python_backend import PythonReasoner

            prolog = PrologReasoner(max_results=max_results)
            reasoner = prolog if prolog.is_available else PythonReasoner()
            results = Session(model=model, reasoner=reasoner).execute(query_str)
            raw = (
                results[-1].to_dict()
                if results
                else {
                    "query": query_str,
                    "statement_type": "query",
                    "summary": "No results.",
                    "answers": [],
                    "explanation": None,
                }
            )
        else:
            raw = run_query(model, query_str).to_dict()
        if not rank_by_distance:
            return raw
        reranked: list[dict[str, Any]] = []
        for ans in raw.get("answers") or []:
            item = dict(ans)
            hop = max(0, len(item.get("path") or []) - 1)
            item["hop_distance"] = hop
            item["distance_score"] = round(1.0 / (1.0 + hop), 4)
            reranked.append(item)
        reranked.sort(key=lambda entry: (int(entry["hop_distance"]), str(entry.get("value", ""))))
        raw["answers"] = reranked
        return raw

    def analyze_portfolio(
        self,
        portfolio_path: Union[str, Path],
        *,
        vault_dir: Union[str, Path] | None = None,
        max_depth: int = 3,
        max_files_per_unit: int | None = 60,
    ) -> PortfolioOntologyAnalysisReport:
        """Analyze each repository inside a multi-repo directory and aggregate unlearned gaps."""
        _require_engine()
        repo_adapter = importlib.import_module("plugins.memory_and_epistemics.ontology_spider.repo_adapter")
        root = Path(portfolio_path).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Portfolio path does not exist or is not a directory: {root}")
        child_repos = repo_adapter.discover_portfolio_repos(root) or [root]
        summaries: list[PortfolioRepoSummary] = []
        total_projects = 0
        total_entities = 0
        total_assertions = 0
        total_cycles = 0
        unlearned_pool: list[str] = []

        for repo_dir in child_repos:
            rep = self.analyze_repository(
                repo_dir,
                vault_dir=vault_dir,
                max_depth=max_depth,
                max_files_per_unit=max_files_per_unit,
            )
            total_projects += rep.projects_count
            total_entities += rep.entities_count
            total_assertions += rep.assertions_count
            total_cycles += len(rep.cycle_violations)
            for target in rep.unlearned_tested_projects[:10]:
                label = f"{repo_dir.name}/{target}" if target != repo_dir.name else repo_dir.name
                if label not in unlearned_pool:
                    unlearned_pool.append(label)
            summaries.append(
                PortfolioRepoSummary(
                    repo_name=repo_dir.name,
                    repo_root=rep.repo_root,
                    resolved_root=rep.resolved_root,
                    projects_count=rep.projects_count,
                    entities_count=rep.entities_count,
                    assertions_count=rep.assertions_count,
                    cycle_count=len(rep.cycle_violations),
                    unlearned_tested_count=len(rep.unlearned_tested_projects),
                    gruber_overall_score=float(rep.gruber_scorecard.get("overall_score", 0.0)),
                    top_hubs=rep.dependency_hubs[:5],
                    unlearned_tested_sample=rep.unlearned_tested_projects[:10],
                )
            )

        return PortfolioOntologyAnalysisReport(
            portfolio_root=str(root),
            repos_count=len(summaries),
            total_projects_count=total_projects,
            total_entities_count=total_entities,
            total_assertions_count=total_assertions,
            total_cycle_violations=total_cycles,
            top_unlearned_targets=tuple(unlearned_pool[:30]),
            repo_summaries=tuple(summaries),
        )

    def compute_blast_radius(
        self,
        model: Any,
        *,
        predicate: str = "depends_on_project",
    ) -> dict[str, tuple[str, ...]]:
        """Return cycle-safe reverse transitive dependents per node for a directed predicate."""
        from collections import deque

        rev_adj: dict[str, set[str]] = {}
        nodes: set[str] = set()
        for asrt in model.assertions.values():
            if asrt.relation.predicate != predicate:
                continue
            subj = str(asrt.relation.subject)
            obj = str(asrt.relation.object)
            nodes.add(subj)
            nodes.add(obj)
            rev_adj.setdefault(obj, set()).add(subj)

        out: dict[str, tuple[str, ...]] = {}
        for node in sorted(nodes):
            visited: set[str] = set()
            queue = deque(sorted(rev_adj.get(node, ())))
            while queue:
                cur = queue.popleft()
                if cur == node or cur in visited:
                    continue
                visited.add(cur)
                for parent in rev_adj.get(cur, ()):
                    if parent != node and parent not in visited:
                        queue.append(parent)
            out[node] = tuple(sorted(visited))
        return out
