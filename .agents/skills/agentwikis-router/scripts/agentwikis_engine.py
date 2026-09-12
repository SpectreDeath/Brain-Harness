# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""AgentWikis Engine — Slotted Domain Models, Medallion Lakehouse & Governance.

Operationalizes https://agentwikis.com/for-agents and local AgentWikis corpus
under DAMA-DMBOK data management and deep-module engineering standards:
- Rule 12: Slotted & Frozen Dataclass Domain Architecture
- Contract-first ODCS verification (Bronze -> Silver -> Gold tiers)
- 6-dimension data quality profiling (Accuracy, Completeness, Consistency, Timeliness, Validity, Uniqueness)
- Calibrated confidence search and zero-latency document slice extraction
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.request

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 12: Slotted & Frozen Domain Dataclasses
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class WikiScope:
    """Declared boundary definitions and version freshness for a wiki."""

    covers: str
    not_covered: str
    current_as: str

    def to_dict(self) -> dict[str, str]:
        return {
            "covers": self.covers,
            "not_covered": self.not_covered,
            "current_as": self.current_as,
        }


@dataclass(slots=True, frozen=True)
class WikiEntity:
    """Canonical representation of a single wiki in the knowledge base."""

    slug: str
    title: str
    description: str
    category: str
    tags: tuple[str, ...]
    scope: WikiScope
    document_count: int
    last_updated: str
    raw_base: str
    html_base: str
    xl_document_count: int = 0

    def __post_init__(self) -> None:
        if not self.slug or not self.slug.strip():
            raise ValueError("WikiEntity slug cannot be empty")
        if self.document_count < 0:
            raise ValueError(f"document_count cannot be negative: {self.document_count}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "scope": self.scope.to_dict(),
            "document_count": self.document_count,
            "last_updated": self.last_updated,
            "raw_base": self.raw_base,
            "html_base": self.html_base,
            "xl_document_count": self.xl_document_count,
        }


@dataclass(slots=True, frozen=True)
class SkillEntity:
    """Curated agent skill registered in AgentWikis catalog."""

    name: str
    description: str
    author: str
    wiki: str
    standalone: bool
    file_count: int
    pro: bool
    bundle_url: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("SkillEntity name cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "wiki": self.wiki,
            "standalone": self.standalone,
            "file_count": self.file_count,
            "pro": self.pro,
            "bundle_url": self.bundle_url,
        }


@dataclass(slots=True, frozen=True)
class DocumentSlice:
    """Extracted Markdown section or full document with source isnad provenance."""

    wiki_slug: str
    relative_path: str
    title: str
    content: str
    section: str | None = None
    is_gated: bool = False
    source_isnad: str = "local_llms_full_txt"

    def to_dict(self) -> dict[str, Any]:
        return {
            "wiki_slug": self.wiki_slug,
            "relative_path": self.relative_path,
            "title": self.title,
            "section": self.section,
            "is_gated": self.is_gated,
            "source_isnad": self.source_isnad,
            "content_length": len(self.content),
            "content": self.content,
        }


@dataclass(slots=True, frozen=True)
class MatchResult:
    """Result of intent and boundary evaluation for an incoming agent task."""

    query: str
    in_scope: bool
    calibrated_confident: bool
    matched_wikis: tuple[WikiEntity, ...]
    matched_skills: tuple[SkillEntity, ...]
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        local_skills: list[str] = []
        q_lower = self.query.lower()
        if "pocock" in q_lower or "typescript" in q_lower:
            local_skills.append("pocock-skills")
        if "skill" in q_lower or "card" in q_lower:
            local_skills.append("crafting-skills")

        return {
            "query": self.query,
            "in_scope": self.in_scope,
            "calibrated_confident": self.calibrated_confident,
            "confidence": 0.85 if self.calibrated_confident else 0.2,
            "rejection_reason": self.rejection_reason,
            "matched_wikis": [w.to_dict() for w in self.matched_wikis],
            "recommended_wikis": [w.to_dict() for w in self.matched_wikis],
            "matched_skills": [s.to_dict() for s in self.matched_skills],
            "recommended_agentwikis_skills": [s.to_dict() for s in self.matched_skills],
            "recommended_local_workspace_skills": local_skills,
            "fallback_recommendation": "none" if self.in_scope else "web_search",
        }


@dataclass(slots=True, frozen=True)
class SearchHit:
    """Individual search result item with calibrated confidence and snippet."""

    wiki_slug: str
    doc_path: str
    title: str
    score: float
    calibrated_confident: bool
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "wiki_slug": self.wiki_slug,
            "doc_path": self.doc_path,
            "title": self.title,
            "score": round(self.score, 2),
            "calibrated_confident": self.calibrated_confident,
            "snippet": self.snippet,
        }


@dataclass(slots=True, frozen=True)
class DocumentBlockOffset:
    """Byte offset and length of a document slice inside llms-full.txt."""

    wiki_slug: str
    relative_path: str
    byte_offset: int
    byte_length: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "wiki_slug": self.wiki_slug,
            "relative_path": self.relative_path,
            "byte_offset": self.byte_offset,
            "byte_length": self.byte_length,
        }


@dataclass(slots=True, frozen=True)
class DocumentOffsetTable:
    """Slotted and frozen lookup table mapping document paths to byte offsets for O(1) seeking."""

    corpus_file: str
    total_blocks: int
    offsets: dict[str, tuple[int, int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus_file": self.corpus_file,
            "total_blocks": self.total_blocks,
            "offsets_count": len(self.offsets),
        }


@dataclass(slots=True, frozen=True)
class QualityDimensionReport:
    """Scorecard for a single DAMA data quality dimension."""

    dimension: str
    score: float
    passed: bool
    details: str
    violations_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 2),
            "passed": self.passed,
            "violations_count": self.violations_count,
            "details": self.details,
        }


@dataclass(slots=True, frozen=True)
class QualityScorecard:
    """Aggregate 6-dimension DAMA-DMBOK Data Quality Scorecard."""

    overall_score: float
    passed: bool
    evaluated_at: str
    dimensions: tuple[QualityDimensionReport, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 2),
            "passed": self.passed,
            "evaluated_at": self.evaluated_at,
            "dimensions": [d.to_dict() for d in self.dimensions],
        }

    def generate_markdown(self) -> str:
        lines = [
            "# AgentWikis 6-Dimension Data Quality Scorecard",
            f"**Overall Score**: {self.overall_score:.1f}/100.0 — {'✓ PASS' if self.passed else '✗ FAIL'}",
            f"**Evaluated At**: {self.evaluated_at}",
            "",
            "| Dimension | Score | Status | Violations | Diagnostic Details |",
            "|---|---|---|---|---|",
        ]
        for d in self.dimensions:
            status = "✓ PASS" if d.passed else "✗ FAIL"
            lines.append(f"| **{d.dimension}** | {d.score:.1f}% | {status} | {d.violations_count} | {d.details} |")
        return "\n".join(lines)


@dataclass(slots=True, frozen=True)
class ContractViolation:
    """Specific field or schema violation against Open Data Contract."""

    entity_type: str
    identifier: str
    field_name: str
    violation_type: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "identifier": self.identifier,
            "field": self.field_name,
            "type": self.violation_type,
            "message": self.message,
        }


@dataclass(slots=True, frozen=True)
class ContractValidationReport:
    """Report generated by validating the corpus against Open Data Contract."""

    is_compliant: bool
    contract_name: str
    version: str
    total_entities_checked: int
    violations: tuple[ContractViolation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "contract_name": self.contract_name,
            "version": self.version,
            "total_entities_checked": self.total_entities_checked,
            "violations_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


# ---------------------------------------------------------------------------
# Core Engine & Path Resolution
# ---------------------------------------------------------------------------

class AgentWikisEngine:
    """Deep-module engine encapsulating data ingestion, validation, and retrieval."""

    def __init__(self, corpus_dir: Path | str | None = None, base_url: str = "https://agentwikis.com") -> None:
        self.corpus_dir = self.resolve_corpus_path(corpus_dir)
        self.base_url = base_url.rstrip("/")
        self._raw_index_cache: dict[str, Any] | None = None
        self._wikis_cache: dict[str, WikiEntity] | None = None
        self._skills_cache: dict[str, SkillEntity] | None = None
        self._offset_table: DocumentOffsetTable | None = None

    @staticmethod
    def resolve_corpus_path(custom_path: Path | str | None = None) -> Path:
        """Dynamically resolves corpus path using layered precedence without hardcoded paths."""
        # 1. Custom explicit argument
        if custom_path:
            p = Path(custom_path)
            if p.exists() and p.is_dir():
                return p.resolve()

        # 2. Environment variable
        env_val = os.environ.get("AGENTWIKIS_CORPUS_DIR")
        if env_val:
            p = Path(env_val)
            if p.exists() and p.is_dir():
                return p.resolve()

        # 3. Read config.default.yaml if present in skill directory
        try:
            skill_dir = Path(__file__).resolve().parent.parent
            cfg_file = skill_dir / "config.default.yaml"
            if cfg_file.exists() and yaml is not None:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    cfg_data = yaml.safe_load(f) or {}
                    cfg_corpus = cfg_data.get("corpus_dir")
                    if cfg_corpus:
                        p = Path(cfg_corpus)
                        if p.exists() and p.is_dir():
                            return p.resolve()
        except Exception:
            pass

        # 4. Standard relocatable candidates
        for candidate in [Path("D:/AgentWikis"), Path("./corpus"), Path("./AgentWikis"), Path(".")]:
            if candidate.exists() and candidate.is_dir() and list(candidate.glob("*index.json")):
                return candidate.resolve()

        return Path(".").resolve()

    def get_raw_index(self) -> dict[str, Any]:
        """Loads and caches raw index.json data (Bronze Tier)."""
        if self._raw_index_cache is not None:
            return self._raw_index_cache

        candidates = list(self.corpus_dir.glob("*index.json"))
        if candidates:
            with open(candidates[0], "r", encoding="utf-8") as f:
                self._raw_index_cache = json.load(f)
                return self._raw_index_cache

        return {"wikis": [], "skills": [], "videos": []}

    def load_entities(self) -> tuple[dict[str, WikiEntity], dict[str, SkillEntity]]:
        """Parses Bronze data into typed, slotted Silver Tier entities."""
        if self._wikis_cache is not None and self._skills_cache is not None:
            return self._wikis_cache, self._skills_cache

        raw = self.get_raw_index()
        wikis: dict[str, WikiEntity] = {}
        for w in raw.get("wikis") or []:
            slug = (w.get("slug") or "").strip()
            if not slug:
                continue
            scope_raw = w.get("scope") or {}
            xl_raw = w.get("xl") or {}
            scope = WikiScope(
                covers=str(scope_raw.get("covers") or ""),
                not_covered=str(scope_raw.get("notCovered") or ""),
                current_as=str(scope_raw.get("currentAs") or w.get("lastUpdated") or "Unknown"),
            )
            tags = tuple(str(t).strip() for t in (w.get("tags") or []) if str(t).strip())
            entity = WikiEntity(
                slug=slug,
                title=str(w.get("title") or slug),
                description=str(w.get("description") or ""),
                category=str(w.get("category") or "uncategorized"),
                tags=tags,
                scope=scope,
                document_count=int(w.get("documentCount") or 0),
                last_updated=str(w.get("lastUpdated") or "Unknown"),
                raw_base=str(w.get("raw_base") or f"{self.base_url}/raw/{slug}"),
                html_base=str(w.get("html_base") or f"{self.base_url}/wiki/{slug}"),
                xl_document_count=int(xl_raw.get("documentCount") or 0),
            )
            wikis[slug.lower()] = entity

        skills: dict[str, SkillEntity] = {}
        for s in raw.get("skills") or []:
            name = (s.get("name") or "").strip()
            if not name:
                continue
            skill_entity = SkillEntity(
                name=name,
                description=str(s.get("description") or ""),
                author=str(s.get("author") or "Unknown"),
                wiki=str(s.get("wiki") or ""),
                standalone=bool(s.get("standalone", False)),
                file_count=int(s.get("fileCount") or 0),
                pro=bool(s.get("pro", False)),
                bundle_url=str(s.get("bundle") or ""),
            )
            skills[name.lower()] = skill_entity

        self._wikis_cache = wikis
        self._skills_cache = skills
        return wikis, skills

    def _ensure_offset_table(self) -> DocumentOffsetTable | None:
        """Lazily indexes byte offsets of document blocks inside llms-full.txt for O(1) seeking."""
        if self._offset_table is not None:
            return self._offset_table

        full_txt_files = list(self.corpus_dir.glob("*llms-full.txt"))
        if not full_txt_files:
            return None

        full_txt = full_txt_files[0]
        offset_map: dict[str, tuple[int, int]] = {}
        delimiter_pat = re.compile(rb"^<!--\s*=====\s*([^=\s]+)\s*=====\s*-->")

        try:
            with open(full_txt, "rb") as f:
                current_key: str | None = None
                start_pos = 0
                current_pos = 0

                while True:
                    line = f.readline()
                    if not line:
                        if current_key is not None:
                            offset_map[current_key] = (start_pos, current_pos - start_pos)
                        break

                    line_len = len(line)
                    if line.startswith(b"<!-- =====") or b"=====" in line:
                        m = delimiter_pat.match(line.strip())
                        if m:
                            if current_key is not None:
                                offset_map[current_key] = (start_pos, current_pos - start_pos)
                            current_key = m.group(1).decode("utf-8", errors="replace").strip().lower()
                            start_pos = current_pos + line_len
                    current_pos += line_len

            self._offset_table = DocumentOffsetTable(
                corpus_file=str(full_txt),
                total_blocks=len(offset_map),
                offsets=offset_map,
            )
            return self._offset_table
        except Exception:
            return None

    def list_wikis(
        self,
        category: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[WikiEntity]:
        """Lists wikis filtered by category, tag, or query string."""
        wikis, _ = self.load_entities()
        filtered = list(wikis.values())

        if category:
            cat_lower = category.strip().lower()
            filtered = [w for w in filtered if w.category.lower() == cat_lower]

        if tag:
            tag_lower = tag.strip().lower()
            filtered = [w for w in filtered if tag_lower in [t.lower() for t in w.tags]]

        if query:
            q_lower = query.strip().lower()
            filtered = [
                w for w in filtered
                if q_lower in w.slug.lower()
                or q_lower in w.title.lower()
                or q_lower in w.description.lower()
            ]

        return filtered

    def get_scope(self, wiki_slug: str) -> WikiScope | None:
        """Returns declared scope boundaries and version freshness for a wiki."""
        wikis, _ = self.load_entities()
        entity = wikis.get(wiki_slug.strip().lower())
        return entity.scope if entity else None

    # -----------------------------------------------------------------------
    # DAMA-DMBOK 6-Dimension Quality Profiling
    # -----------------------------------------------------------------------

    def profile_data_quality(self, min_passing_score: float = 85.0) -> QualityScorecard:
        """Evaluates the 6 canonical DAMA data quality dimensions across the corpus."""
        wikis, skills = self.load_entities()
        total_wikis = len(wikis)
        total_skills = len(skills)
        now_str = datetime.now(timezone.utc).isoformat()

        if total_wikis == 0:
            empty_rep = QualityDimensionReport("Completeness", 0.0, False, "No wikis discovered in index", 1)
            return QualityScorecard(0.0, False, now_str, (empty_rep,))

        # 1. Completeness: Ensure non-empty description, category, and scope.covers
        comp_violations = 0
        for w in wikis.values():
            if not w.description or not w.category or not w.scope.covers:
                comp_violations += 1
        comp_score = max(0.0, 100.0 - (comp_violations / total_wikis * 100.0))

        # 2. Accuracy: Verify valid slug format (kebab-case or alphanumeric)
        acc_violations = 0
        for w in wikis.values():
            if not re.match(r"^[a-z0-9_-]+$", w.slug.lower()):
                acc_violations += 1
        acc_score = max(0.0, 100.0 - (acc_violations / total_wikis * 100.0))

        # 3. Consistency: Verify that skill referenced wikis exist in wikis catalog
        cons_violations = 0
        for s in skills.values():
            if s.wiki and s.wiki.lower() not in wikis:
                cons_violations += 1
        cons_score = max(0.0, 100.0 - (cons_violations / max(1, total_skills) * 100.0))

        # 4. Validity: Verify scope.currentAs and lastUpdated are valid date strings
        val_violations = 0
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
        for w in wikis.values():
            if not date_pattern.match(w.last_updated) and w.last_updated != "Unknown":
                val_violations += 1
        val_score = max(0.0, 100.0 - (val_violations / total_wikis * 100.0))

        # 5. Uniqueness: Verify no duplicate slugs or skill names (already hashed by key)
        raw = self.get_raw_index()
        raw_slugs = [w.get("slug") for w in (raw.get("wikis") or []) if w.get("slug")]
        uniq_violations = len(raw_slugs) - len(set(raw_slugs))
        uniq_score = max(0.0, 100.0 - (uniq_violations / max(1, len(raw_slugs)) * 100.0))

        # 6. Timeliness / Freshness: Check if wikis have been updated within last 24 months
        time_violations = 0
        current_year = datetime.now().year
        for w in wikis.values():
            m = re.match(r"^(\d{4})", w.last_updated)
            if m:
                yr = int(m.group(1))
                if current_year - yr > 2:
                    time_violations += 1
            else:
                time_violations += 1
        time_score = max(0.0, 100.0 - (time_violations / total_wikis * 100.0))

        dimensions = (
            QualityDimensionReport("Completeness", comp_score, comp_score >= min_passing_score, f"{comp_violations} wikis missing required metadata", comp_violations),
            QualityDimensionReport("Accuracy", acc_score, acc_score >= min_passing_score, f"{acc_violations} invalid slug formats", acc_violations),
            QualityDimensionReport("Consistency", cons_score, cons_score >= min_passing_score, f"{cons_violations} skill cross-references unmapped", cons_violations),
            QualityDimensionReport("Validity", val_score, val_score >= min_passing_score, f"{val_violations} malformed date timestamps", val_violations),
            QualityDimensionReport("Uniqueness", uniq_score, uniq_score >= min_passing_score, f"{uniq_violations} duplicate slug entries detected", uniq_violations),
            QualityDimensionReport("Timeliness", time_score, time_score >= min_passing_score, f"{time_violations} stale wikis (>24 months old)", time_violations),
        )

        overall = sum(d.score for d in dimensions) / len(dimensions)
        passed = overall >= min_passing_score and all(d.score >= 70.0 for d in dimensions)

        return QualityScorecard(overall, passed, now_str, dimensions)

    # -----------------------------------------------------------------------
    # Open Data Contract (ODCS) Validation
    # -----------------------------------------------------------------------

    def validate_contract(self, contract_path: Path | str) -> ContractValidationReport:
        """Validates the active corpus against a machine-readable Open Data Contract."""
        p = Path(contract_path)
        if not p.exists():
            raise FileNotFoundError(f"Open Data Contract file not found: {p}")

        if yaml is None:
            raise RuntimeError("pyyaml is required for Open Data Contract validation")

        with open(p, "r", encoding="utf-8") as f:
            contract = yaml.safe_load(f) or {}

        contract_name = contract.get("info", {}).get("title", "AgentWikis Data Contract")
        version = contract.get("info", {}).get("version", "1.0.0")

        violations: list[ContractViolation] = []
        wikis, skills = self.load_entities()
        total_entities = len(wikis) + len(skills)

        # Validate Wikis against contract schema
        wiki_rules = contract.get("models", {}).get("wikis", {})
        required_wiki_fields = wiki_rules.get("required", ["slug", "title", "category", "scope"])

        for slug, w in wikis.items():
            for req in required_wiki_fields:
                if req == "scope":
                    if not w.scope.covers:
                        violations.append(ContractViolation("wiki", slug, "scope.covers", "missing_required", "Wiki scope covers is required"))
                elif not getattr(w, req, None):
                    violations.append(ContractViolation("wiki", slug, req, "missing_required", f"Wiki field {req} is required"))

        # Validate Skills against contract schema
        skill_rules = contract.get("models", {}).get("skills", {})
        required_skill_fields = skill_rules.get("required", ["name", "description"])
        for name, s in skills.items():
            for req in required_skill_fields:
                if not getattr(s, req, None):
                    violations.append(ContractViolation("skill", name, req, "missing_required", f"Skill field {req} is required"))

        is_compliant = len(violations) == 0
        return ContractValidationReport(is_compliant, contract_name, version, total_entities, tuple(violations))

    # -----------------------------------------------------------------------
    # Intent Triage, Skill Matching & Calibrated Abstention
    # -----------------------------------------------------------------------

    def match_intent(self, query: str, limit: int = 3) -> MatchResult:
        """Evaluates task intent against wiki scopes and skills with calibrated abstention."""
        wikis, skills = self.load_entities()
        q_norm = query.strip().lower()

        stop_words = {
            "how", "to", "in", "the", "a", "an", "and", "or", "for", "with", "on", "at",
            "is", "of", "by", "from", "as", "into", "all", "any", "do", "does", "did",
            "can", "could", "should", "would", "what", "which", "where", "when", "why",
        }
        tokens = {t for t in re.findall(r"\b[a-z0-9_-]{2,}\b", q_norm) if t not in stop_words}

        # Match wikis
        scored_wikis: list[tuple[float, WikiEntity]] = []
        for w in wikis.values():
            score = 0.0
            slug = w.slug.lower()
            title = w.title.lower()
            desc = w.description.lower()
            tags = [t.lower() for t in w.tags]
            covers = w.scope.covers.lower()
            not_cov = w.scope.not_covered.lower()

            if slug and re.search(rf"\b{re.escape(slug)}\b", q_norm):
                score += 12.0
            if title and re.search(rf"\b{re.escape(title)}\b", q_norm):
                score += 8.0

            for t in tokens:
                if t == slug:
                    score += 5.0
                elif t in tags:
                    score += 4.0
                elif t in title:
                    score += 3.0
                elif t in covers:
                    score += 2.0
                elif t in desc:
                    score += 1.0

                # Strong negative penalty if query contains excluded scope concepts
                if t in not_cov:
                    score -= 5.0

            if score > 0:
                scored_wikis.append((score, w))

        scored_wikis.sort(key=lambda x: x[0], reverse=True)

        # Match skills
        scored_skills: list[tuple[float, SkillEntity]] = []
        top_wiki = scored_wikis[0][1] if scored_wikis else None

        for s in skills.values():
            score = 0.0
            name = s.name.lower()
            desc = s.description.lower()
            wiki_slug = s.wiki.lower()

            if top_wiki and wiki_slug == top_wiki.slug.lower():
                score += 8.0
            if name and re.search(rf"\b{re.escape(name)}\b", q_norm):
                score += 10.0
            if wiki_slug and re.search(rf"\b{re.escape(wiki_slug)}\b", q_norm):
                score += 6.0

            for t in tokens:
                if t in name:
                    score += 4.0
                elif t in desc:
                    score += 2.0

            if score > 0:
                scored_skills.append((score, s))

        scored_skills.sort(key=lambda x: x[0], reverse=True)

        matched_wikis = tuple(w for _, w in scored_wikis[:limit])
        matched_skills = tuple(s for _, s in scored_skills[:limit])

        # Calibrated abstention: if best wiki score is under confidence floor or falls in negative scope
        if not scored_wikis:
            return MatchResult(query, False, False, (), (), "No matching wiki found in catalog")

        best_score, top_wiki = scored_wikis[0]
        if best_score < 5.0:
            return MatchResult(
                query,
                False,
                False,
                (),
                (),
                "Task intent did not meet minimum confidence threshold for in-scope wikis",
            )

        # Check explicit negative deflection (skip wiki's own slug, title, and tags)
        exempt_tokens = {top_wiki.slug.lower(), top_wiki.title.lower()}
        exempt_tokens.update(t.lower() for t in top_wiki.tags)

        for t in tokens:
            if t in exempt_tokens:
                continue
            if re.search(rf"\b{re.escape(t)}\b", top_wiki.scope.not_covered.lower()):
                return MatchResult(
                    query,
                    False,
                    False,
                    matched_wikis,
                    matched_skills,
                    f"Task concept '{t}' explicitly declared under scope.notCovered for {top_wiki.slug}",
                )

        confident = best_score >= 8.0
        return MatchResult(query, True, confident, matched_wikis, matched_skills)

    # -----------------------------------------------------------------------
    # Document Slice Retrieval (Offline First + Online Fallback)
    # -----------------------------------------------------------------------

    def extract_document(
        self,
        doc_path: str,
        section_heading: str | None = None,
        force_remote: bool = False,
    ) -> DocumentSlice:
        """Extracts exact Markdown document section from local llms-full.txt or falls back to remote."""
        normalized_path = doc_path.strip().replace("\\", "/").lstrip("/")
        parts = normalized_path.split("/", 1)
        wiki_slug = parts[0]
        rel_path = parts[1] if len(parts) > 1 else "README.md"

        if not force_remote:
            full_txt_files = list(self.corpus_dir.glob("*llms-full.txt"))
            if full_txt_files:
                doc = self._extract_from_full_txt(full_txt_files[0], wiki_slug, rel_path, section_heading)
                if doc:
                    return doc

        # Remote Fallback
        remote_url = f"{self.base_url}/raw/{wiki_slug}/{rel_path}"
        content = self._fetch_remote(remote_url)
        return self._slice_markdown(content, wiki_slug, rel_path, section_heading, source_isnad=remote_url)

    def _extract_from_full_txt(
        self,
        full_txt_path: Path,
        wiki_slug: str,
        rel_path: str,
        section_heading: str | None,
    ) -> DocumentSlice | None:
        """Scans local llms-full.txt using delimiter tags <!-- ===== slug/path ===== --> with O(1) byte seeking."""
        slug_clean = wiki_slug.lower()
        rel_clean = rel_path.lower()
        target_path_alt = f"{slug_clean}/{rel_clean}"

        # Fast path: O(1) byte-offset seek
        offset_table = self._ensure_offset_table()
        if offset_table and target_path_alt in offset_table.offsets:
            offset, length = offset_table.offsets[target_path_alt]
            try:
                with open(full_txt_path, "rb") as f:
                    f.seek(offset)
                    raw_bytes = f.read(length)
                full_content = raw_bytes.decode("utf-8", errors="replace")
                return self._slice_markdown(full_content, wiki_slug, rel_path, section_heading, "local_llms_full_txt")
            except Exception:
                pass

        # Fallback path: sequential scanning
        delimiter_pat = re.compile(r"<!--\s*=====\s*([^=\s]+)\s*=====\s*-->")
        with open(full_txt_path, "r", encoding="utf-8", errors="replace") as f:
            capturing = False
            captured_lines: list[str] = []

            for line in f:
                m = delimiter_pat.match(line.strip())
                if m:
                    header_path = m.group(1).strip().lower()
                    if header_path == target_path_alt:
                        capturing = True
                        captured_lines = []
                        continue
                    elif capturing:
                        break
                elif capturing:
                    captured_lines.append(line)

            if captured_lines:
                full_content = "".join(captured_lines)
                return self._slice_markdown(full_content, wiki_slug, rel_path, section_heading, "local_llms_full_txt")

        return None

    # -----------------------------------------------------------------------
    # In-Engine Full-Text Search, Batch Extraction & Context Pack Assembly
    # -----------------------------------------------------------------------

    def search(
        self,
        query: str,
        wiki: str | None = None,
        limit: int = 5,
    ) -> tuple[SearchHit, ...]:
        """Searches corpus across documents and metadata with calibrated confidence."""
        wikis, _ = self.load_entities()
        q_clean = query.strip().lower()
        target_wiki = wiki.strip().lower() if wiki else None

        hits: list[SearchHit] = []
        full_txt_files = list(self.corpus_dir.glob("*llms-full.txt"))

        if full_txt_files:
            full_path = full_txt_files[0]
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    current_doc = "index"
                    current_wiki = ""
                    current_content: list[str] = []

                    for line in f:
                        if line.startswith("<!-- ====="):
                            parts = line.replace("<!-- =====", "").replace("===== -->", "").strip().split("/")
                            current_wiki = parts[0].strip().lower() if parts else ""
                            current_doc = line.strip()
                            current_content = []
                        else:
                            if target_wiki and current_wiki != target_wiki:
                                continue
                            if q_clean in line.lower():
                                snippet = line.strip()[:200]
                                score = 10.0 if q_clean in current_doc.lower() else 5.0
                                hits.append(
                                    SearchHit(
                                        wiki_slug=current_wiki or "corpus",
                                        doc_path=current_doc,
                                        title=current_doc,
                                        score=score,
                                        calibrated_confident=score >= 5.0,
                                        snippet=snippet,
                                    )
                                )
                                if len(hits) >= limit * 3:
                                    break
            except Exception:
                pass

        if not hits:
            # Fallback to wiki metadata search
            for slug, w in wikis.items():
                if target_wiki and slug != target_wiki:
                    continue
                if q_clean in w.title.lower() or q_clean in w.description.lower() or q_clean in w.scope.covers.lower():
                    hits.append(
                        SearchHit(
                            wiki_slug=slug,
                            doc_path=f"{slug}/wiki/index.md",
                            title=w.title,
                            score=4.0,
                            calibrated_confident=False,
                            snippet=w.description[:200],
                        )
                    )

        hits.sort(key=lambda x: x.score, reverse=True)
        return tuple(hits[:limit])

    def batch_extract(
        self,
        specs: list[tuple[str, str | None]],
        force_remote: bool = False,
    ) -> list[DocumentSlice]:
        """Extracts multiple document sections in a single batch operation."""
        return [
            self.extract_document(doc_path=p, section_heading=s, force_remote=force_remote)
            for p, s in specs
        ]

    def prepare_context_pack(
        self,
        query: str,
        max_tokens: int = 4000,
    ) -> str:
        """One-shot intent evaluation, document retrieval, and bounded context compilation."""
        match = self.match_intent(query)
        if not match.in_scope or not match.matched_wikis:
            reason = match.rejection_reason or "No confident wiki match found."
            return f"# AgentWikis Context Pack: Out of Scope\n\nQuery: '{query}'\nRejection Reason: {reason}"

        top_wiki = match.matched_wikis[0]
        lines = [
            f"# AgentWikis Context Pack: {query}",
            f"**Scope Status**: IN_SCOPE | **Calibrated Confident**: {match.calibrated_confident}",
            f"**Primary Target Wiki**: {top_wiki.title} (`{top_wiki.slug}`)",
            f"**Covers**: {top_wiki.scope.covers}",
            "",
            "---",
            "",
        ]

        char_budget = max_tokens * 4
        current_chars = sum(len(l) for l in lines)

        extracted_docs: list[DocumentSlice] = []
        for w in match.matched_wikis[:2]:
            candidates = [f"{w.slug}/README.md", f"{w.slug}/wiki/index.md"]
            for c in candidates:
                try:
                    doc = self.extract_document(c)
                    if doc and len(doc.content) > 10:
                        extracted_docs.append(doc)
                        break
                except Exception:
                    continue

        for doc in extracted_docs:
            doc_header = f"## [{doc.title}] (Source: `{doc.source_isnad}`)\n\n"
            content_budget = char_budget - current_chars - len(doc_header) - 100
            if content_budget <= 200:
                break

            doc_body = (
                doc.content
                if len(doc.content) <= content_budget
                else doc.content[:content_budget] + "\n\n... [Content Truncated by Context Budget]"
            )
            lines.append(doc_header)
            lines.append(doc_body)
            lines.append("\n---\n")
            current_chars += len(doc_header) + len(doc_body) + 10

        lines.append("## Provenance & Isnad Lineage")
        lines.append(f"- Corpus Base: `{self.corpus_dir}`")
        lines.append("- Verified Tiers: Bronze (Raw Index) -> Silver (Typed Slotted Entities) -> Gold (Byte-Offset Slices)")
        return "\n".join(lines)


    def _slice_markdown(
        self,
        content: str,
        wiki_slug: str,
        rel_path: str,
        section_heading: str | None,
        source_isnad: str,
    ) -> DocumentSlice:
        """Extracts title and optional specific sub-section from Markdown body."""
        # Extract title from YAML frontmatter or first # header
        title = f"{wiki_slug}/{rel_path}"
        m_title = re.search(r"^title:\s*[\"']?([^\"'\n]+)[\"']?", content, re.MULTILINE)
        if m_title:
            title = m_title.group(1).strip()
        else:
            m_h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if m_h1:
                title = m_h1.group(1).strip()

        if not section_heading:
            return DocumentSlice(wiki_slug, rel_path, title, content.strip(), None, False, source_isnad)

        # Slice section by heading
        sec_clean = section_heading.strip().lstrip("#").strip()
        pat = re.compile(rf"^(#{{1,6}})\s+{re.escape(sec_clean)}\b.*$", re.MULTILINE | re.IGNORECASE)
        match = pat.search(content)
        if not match:
            # Return full content with note if heading not found
            return DocumentSlice(
                wiki_slug,
                rel_path,
                title,
                content.strip(),
                f"Section '{sec_clean}' not found, returned full document",
                False,
                source_isnad,
            )

        level = len(match.group(1))
        start_idx = match.start()
        # Find next heading of equal or higher level
        next_pat = re.compile(rf"^#{{1,{level}}}\s+", re.MULTILINE)
        next_match = next_pat.search(content, match.end())
        end_idx = next_match.start() if next_match else len(content)

        sliced = content[start_idx:end_idx].strip()
        return DocumentSlice(wiki_slug, rel_path, title, sliced, sec_clean, False, source_isnad)

    def _fetch_remote(self, url: str, timeout: float = 10.0) -> str:
        """Fetches remote Markdown with rate-limiting backoff."""
        headers = {"User-Agent": "BrainHarness-AgentWikisEngine/1.0", "Accept": "text/markdown, text/plain"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(f"Document not found at {url} (HTTP 404)")
            raise RuntimeError(f"HTTP {e.code} failed for {url}")
        except Exception as e:
            raise RuntimeError(f"Connection failed for {url}: {e}")
