"""Repository-to-Ontology ModelSource adapter for Ontology-Spider (Phase 2).

Extracts structural entities, manifests, domain taxonomy, framework edges,
cross-project Python AST imports, arXiv citations, and Knowledge Vault bridge links
using bounded traversal (Rule 52) and collision-safe identifier allocation.
"""

from __future__ import annotations

import ast
import json
import logging
import os
from pathlib import Path
import re
from typing import Any
import warnings

from plugins.memory_and_epistemics.ontology_spider.adapter import (
    _NOISE_DIRS,
    _alloc_unique_identifier,
    _sanitize_identifier,
)

logger = logging.getLogger(__name__)

try:
    from ontology_spider.model import (
        ACYCLIC,
        DISJOINT_WITH,
        DOMAIN,
        INSTANCE_OF,
        RANGE,
        SUBCLASS_OF,
        Entity,
        OntologyModel,
        Provenance,
        Relation,
    )
    from ontology_spider.seam import ModelSource

    HAS_ONTOLOGY_SPIDER = True
except ModuleNotFoundError:
    HAS_ONTOLOGY_SPIDER = False
    Entity = None  # type: ignore
    OntologyModel = None  # type: ignore
    Provenance = None  # type: ignore
    Relation = None  # type: ignore
    ModelSource = object  # type: ignore

_EXTRA_NOISE_DIRS = frozenset(
    {
        "venv",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".harness",
        ".gemini",
        "external",
        "test_ingested_plugins",
        "3rdparty",
        "third_party",
        "vendor",
    }
)
_PRUNE_DIRS = _NOISE_DIRS | _EXTRA_NOISE_DIRS

_MANIFEST_FILES = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "package.json",
        "cargo.toml",
        "go.mod",
        "build",
        "run.sh",
        "plugin.json",
    }
)
_README_NAMES = frozenset({"readme.md", "readme.rst", "readme.txt", "readme"})
_ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.IGNORECASE)
_PY_IMPORT_LINE_RE = re.compile(r"^\s*(?:import|from)\s+([^\n#]+)", re.MULTILINE)
_GO_QUOTED_IMPORT_RE = re.compile(r'"([^"\s]+)"')
_BAZEL_DEP_RE = re.compile(r'"//([a-zA-Z0-9_-]+)(?:[/:][^"]*)?"')
_TS_REL_IMPORT_RE = re.compile(r"""(?:from|import)\s+['"]\.\./([a-zA-Z0-9_-]+)(?:/[^'"]*)?['"]""")
_RUST_USE_RE = re.compile(r"\buse\s+([a-zA-Z0-9_]+)::")
_CPP_INCLUDE_RE = re.compile(r'^\s*#include\s+"([a-zA-Z0-9_-]+)/', re.MULTILINE)

_LEARNED_NOISE_TOKENS = frozenset(
    {
        "external",
        "google",
        "google_research",
        "google-research",
        "google-research-master",
        "google_research_master",
        "github",
        "github.com",
        "https",
        "http",
        "www",
        "com",
        "org",
        "src",
        "main",
        "master",
        "docs",
        "doc",
        "test",
        "tests",
        "scripts",
        "examples",
        "python",
        "plugins",
        "plugin",
        "bridge",
        "architecture",
        "tree",
        "blob",
        "internal",
        "reference",
    }
)

_GENERIC_UNIT_NAMES = frozenset(
    {
        "python",
        "tests",
        "scripts",
        "test",
        "go",
        "js",
        "pkg",
        "tools",
        "docs",
        "examples",
        "bench",
        "images",
        "website",
        "protos",
        "data",
        "eval",
        "training",
        "runtime",
    }
)

_FW_PATTERNS: dict[str, re.Pattern[str]] = {
    "tensorflow": re.compile(r"\b(?:import\s+tensorflow|from\s+tensorflow\b)"),
    "jax": re.compile(r"\b(?:import\s+jax|from\s+jax\b)"),
    "flax": re.compile(r"\b(?:import\s+flax|from\s+flax\b)"),
    "haiku": re.compile(r"\b(?:import\s+haiku|from\s+haiku\b)"),
    "optax": re.compile(r"\b(?:import\s+optax|from\s+optax\b)"),
    "torch": re.compile(r"\b(?:import\s+torch|from\s+torch\b)"),
    "keras": re.compile(r"\b(?:import\s+keras|from\s+keras\b|tf\.keras)"),
    "numpy": re.compile(r"\b(?:import\s+numpy|from\s+numpy\b)"),
    "scipy": re.compile(r"\b(?:import\s+scipy|from\s+scipy\b)"),
    "absl": re.compile(r"\b(?:import\s+absl|from\s+absl\b)"),
    "gin": re.compile(r"\b(?:import\s+gin|from\s+gin\b)"),
    "apache_beam": re.compile(r"\b(?:import\s+apache_beam|from\s+apache_beam\b)"),
    "sklearn": re.compile(r"\b(?:import\s+sklearn|from\s+sklearn\b)"),
    "pydantic": re.compile(r"\b(?:import\s+pydantic|from\s+pydantic\b)"),
    "structlog": re.compile(r"\b(?:import\s+structlog|from\s+structlog\b)"),
    "pytest": re.compile(r"\b(?:import\s+pytest|from\s+pytest\b)"),
}

_FW_UNION_RE = re.compile(
    r"\b(tensorflow|jax|flax|haiku|optax|torch|keras|numpy|scipy|absl|gin|apache_beam|sklearn|pydantic|structlog|pytest)\b"
)

_DOMAIN_RULES: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = tuple(
    (
        dom,
        tuple(re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in kws),
    )
    for dom, kws in (
        (
            "rl_and_control_project",
            (
                "reinforcement learning",
                "rl",
                "mdp",
                "q-learning",
                "actor-critic",
                "policy gradient",
                "mujoco",
                "atari",
                "bandit",
                "offline rl",
            ),
        ),
        (
            "nlp_and_llm_project",
            (
                "language model",
                "llm",
                "llms",
                "transformer",
                "bert",
                "t5",
                "question answering",
                "question-answering",
                "closed-book",
                "summarization",
                "translation",
                "retrieval",
                "rag",
                "tokenizer",
                "dialogue",
                "self-consistency",
                "chain-of-thought",
                "chain of thought",
                "prompting",
                "program synthesis",
                "latent programmer",
                "code generation",
            ),
        ),
        (
            "vision_and_3d_project",
            (
                "vision",
                "image",
                "video",
                "nerf",
                "3d",
                "segmentation",
                "object detection",
                "optical flow",
                "pose",
                "diffusion",
                "gan",
            ),
        ),
        (
            "graph_and_program_project",
            ("graph neural", "gnn", "ast", "control flow", "knowledge graph", "ontology", "sat", "combinatorial"),
        ),
        (
            "science_and_bio_project",
            (
                "quantum",
                "dft",
                "molecule",
                "protein",
                "genomic",
                "dna",
                "rna",
                "climate",
                "weather",
                "physics",
                "pde",
                "fluid",
                "chemistry",
                "fep",
                "biology",
                "medical",
            ),
        ),
        (
            "speech_and_audio_project",
            ("speech", "audio", "keyword spotting", "asr", "tts", "acoustic", "waveform", "spectrogram", "music"),
        ),
        (
            "privacy_fairness_safety_project",
            (
                "differential privacy",
                "privacy",
                "fairness",
                "adversarial",
                "robustness",
                "interpretability",
                "explainability",
                "calibration",
                "uncertainty",
                "watermark",
                "selective prediction",
                "abstention",
                "conformal prediction",
                "active learning",
                "out-of-distribution",
                "security review",
                "vulnerability",
                "crash reproduction",
                "exploit",
            ),
        ),
        (
            "optimization_and_compression_project",
            (
                "pruning",
                "quantization",
                "distillation",
                "nas",
                "neural architecture search",
                "hyperparameter",
                "optimizer",
                "compression",
                "sparsity",
                "nearest neighbor",
                "vector quantization",
                "mips",
                "learned optimizer",
            ),
        ),
        (
            "systems_and_runtime_project",
            (
                "application kernel",
                "syscall",
                "seccomp",
                "seccomp-bpf",
                "sandbox",
                "gofer",
                "sentry",
                "tracing",
                "perfetto",
                "ebpf",
                "container",
                "oci",
                "virtualization",
                "userspace",
                "hypervisor",
                "sandboxed",
            ),
        ),
        (
            "agent_orchestration_project",
            (
                "agent development kit",
                "adk",
                "multi-agent",
                "agentic",
                "harness",
                "recursive harnessing",
                "mcp",
                "tool use",
                "subagent",
            ),
        ),
    )
)


def resolve_repo_root(repo_path: Path) -> Path:
    """Resolve nested archive wrapper roots (e.g. repo-master/repo-master) up to depth 3."""
    current = repo_path.resolve()
    for _ in range(3):
        if any(
            (current / m).is_file()
            for m in ("pyproject.toml", "setup.py", "package.json", "Cargo.toml", "go.mod", "README.md")
        ):
            return current
        subdirs = [
            d
            for d in sorted(current.iterdir(), key=lambda p: p.name)
            if d.is_dir() and not d.name.startswith(".") and d.name not in _PRUNE_DIRS
        ]
        if len(subdirs) != 1:
            return current
        current = subdirs[0]
    return current


def _classify_domain(raw_name: str, readme_text: str) -> str:
    blob = f"{raw_name.replace('_', ' ').replace('-', ' ')} {readme_text[:4000]}"
    best_domain = "general_ml_project"
    best_hits = 0
    for dom, patterns in _DOMAIN_RULES:
        hits = sum(1 for pat in patterns if pat.search(blob))
        if hits > best_hits:
            best_hits = hits
            best_domain = dom
    return best_domain


def _primary_framework(fws: set[str]) -> str:
    for fw in (
        "jax",
        "flax",
        "haiku",
        "optax",
        "tensorflow",
        "keras",
        "torch",
        "apache_beam",
        "sklearn",
        "scipy",
        "numpy",
        "pydantic",
    ):
        if fw in fws:
            if fw in ("flax", "haiku", "optax") and "jax" in fws:
                return "jax"
            return fw
    return "none"


def _register_learned_token(
    token: Any,
    ki_id: str,
    learned: dict[str, tuple[str, str]],
    *,
    strength: str = "tag",
) -> None:
    """Register exact and underscore-normalized repository identifier tokens with match strength."""
    cleaned = str(token or "").strip().lower()
    if len(cleaned) < 3 or cleaned in _LEARNED_NOISE_TOKENS:
        return
    for variant in (cleaned, cleaned.replace("-", "_")):
        if variant in _LEARNED_NOISE_TOKENS:
            continue
        existing = learned.get(variant)
        if existing is None or (strength == "structured" and existing[1] != "structured"):
            learned[variant] = (ki_id, strength)


def _register_path_tokens(
    raw_path: Any,
    ki_id: str,
    learned: dict[str, tuple[str, str]],
) -> None:
    """Extract structured path/URL segments while skipping prose and intermediate generic directories."""
    if not isinstance(raw_path, str):
        return
    stripped = raw_path.strip()
    if not stripped or " " in stripped:
        return
    parts = [p for p in re.split(r"[\\/]+", stripped) if p]
    if not parts:
        return
    last_idx = len(parts) - 1
    for idx, seg in enumerate(parts):
        seg_low = seg.lower()
        if seg_low.endswith(".git"):
            seg_low = seg_low[:-4]
        if ":" in seg_low or ("." in seg_low and seg_low.endswith((".com", ".org", ".io", ".dev"))):
            continue
        # Only allow generic names (e.g. "runtime") as structured when they are the leaf path target
        norm_seg = seg_low.replace("-", "_")
        if norm_seg in _GENERIC_UNIT_NAMES and idx != last_idx:
            continue
        _register_learned_token(seg_low, ki_id, learned, strength="structured")


def _discover_vault_learned_projects(vault_dir: Path | None) -> dict[str, tuple[str, str]]:
    """Scan existing .harness/knowledge directory to map project tokens -> (ki_id, match_strength)."""
    if vault_dir is None or not vault_dir.is_dir():
        return {}
    learned: dict[str, tuple[str, str]] = {}
    for child in sorted(vault_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name.startswith("."):
            continue
        meta_file = child / "metadata.json"
        if not meta_file.is_file():
            continue
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.debug("Skipping unreadable vault metadata %s: %s", meta_file, exc)
            continue
        if not isinstance(data, dict):
            continue
        ki_id = str(data.get("id") or data.get("ki_id") or child.name)

        raw_tags = [str(tag).strip() for tag in (data.get("tags") or []) if str(tag).strip()]
        tag_norms = {t.lower().replace("-", "_") for t in raw_tags}

        # 1. Explicit tags (weaker signal; filtered later for generic or <=4-char unit names)
        for tag in raw_tags:
            _register_learned_token(tag, ki_id, learned, strength="tag")

        # 2. Upstream repository URLs / local mirror paths / multi-repo sources
        for key in ("source_target", "source_uri", "source_repo"):
            _register_path_tokens(data.get(key), ki_id, learned)
        isnad_data = data.get("isnad")
        if isinstance(isnad_data, dict):
            _register_path_tokens(isnad_data.get("source_repo"), ki_id, learned)
        for src_entry in data.get("sources") or []:
            if isinstance(src_entry, dict):
                _register_path_tokens(src_entry.get("repo"), ki_id, learned)
                _register_path_tokens(src_entry.get("path"), ki_id, learned)

        # 3. KI identifier itself and canonical slug forms (avoid generic prose words)
        for id_key in ("id", "ki_id"):
            id_val = str(data.get(id_key) or "").strip()
            if not id_val:
                continue
            _register_learned_token(id_val, ki_id, learned, strength="structured")
            m = re.match(r"^ki[_-](?:\d{8}[_-])?([a-z0-9_-]+?)(?:[_-]\d{2})?$", id_val.lower())
            if m:
                slug = m.group(1)
                _register_learned_token(slug, ki_id, learned, strength="structured")
                for seg in re.split(r"[-_]+", slug):
                    norm_seg = seg.replace("-", "_")
                    if norm_seg in _GENERIC_UNIT_NAMES:
                        continue
                    if len(seg) >= 4 or (len(seg) >= 3 and norm_seg in tag_norms):
                        _register_learned_token(seg, ki_id, learned, strength="structured")

        for plug in data.get("plugins_scaffolded") or []:
            if isinstance(plug, str):
                _register_learned_token(plug.removeprefix("plugin."), ki_id, learned, strength="structured")
    return learned


def _lookup_learned_ki(
    raw_name: str,
    uid: str,
    learned_map: dict[str, tuple[str, str] | str],
) -> tuple[str, str] | None:
    """Resolve matching (ki_id, strength) while rejecting weak tag matches on generic/short units."""
    norm_unit = raw_name.strip().lower().replace("-", "_")
    candidates = [raw_name.lower(), uid.lower(), norm_unit]
    for suffix in ("-main", "_main", "-master", "_master"):
        if raw_name.lower().endswith(suffix):
            stem = raw_name.lower()[: -len(suffix)]
            candidates.extend((stem, stem.replace("-", "_")))
    for cand in candidates:
        if cand in learned_map:
            entry = learned_map[cand]
            if isinstance(entry, str):
                ki_id, strength = entry, "structured"
            else:
                ki_id, strength = entry
            if strength == "tag" and (norm_unit in _GENERIC_UNIT_NAMES or len(norm_unit) <= 4):
                return None
            return ki_id, strength
    return None


def _detect_go_module(repo_root: Path) -> str:
    """Read Go module path from root go.mod when present."""
    go_mod = repo_root / "go.mod"
    if not go_mod.is_file():
        return ""
    try:
        for line in go_mod.read_text(encoding="utf-8", errors="ignore").splitlines()[:40]:
            stripped = line.strip()
            if stripped.startswith("module "):
                return stripped.split()[1].strip()
    except OSError:
        return ""
    return ""


def _extract_python_signals(
    src: str,
    raw_name: str,
    uid: str,
    candidate_tokens: set[str],
    raw_names: set[str],
    raw_to_safe: dict[str, str],
    root_pkg_alias: str,
    fws: set[str],
    cross_edges: set[tuple[str, str]],
) -> None:
    """Detect Python frameworks and AST-verified cross-unit imports without leaking SyntaxWarnings."""
    matched_tokens = set(_FW_UNION_RE.findall(src))
    for fw_tok in matched_tokens:
        pat = _FW_PATTERNS.get(fw_tok)
        if pat is not None and pat.search(src):
            fws.add(fw_tok)

    import_lines = _PY_IMPORT_LINE_RE.findall(src)
    if not import_lines:
        return
    imported_identifiers: set[str] = set()
    for line in import_lines:
        for tok in re.findall(r"[a-zA-Z0-9_]+", line):
            if tok not in ("import", "from", "as"):
                imported_identifiers.add(tok)
    if candidate_tokens.isdisjoint(imported_identifiers):
        return

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return

    for node in ast.walk(tree):
        mod_names: list[str] = []
        if isinstance(node, ast.Import):
            mod_names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mod_names = [node.module]
            if node.module in ("google_research", root_pkg_alias):
                for alias in node.names:
                    if alias.name in raw_names and alias.name != raw_name:
                        cross_edges.add((uid, raw_to_safe[alias.name]))
        for mod_name in mod_names:
            parts = mod_name.split(".")
            if parts[0] in raw_names and parts[0] != raw_name:
                cross_edges.add((uid, raw_to_safe[parts[0]]))
            elif (
                parts[0] in ("google_research", root_pkg_alias)
                and len(parts) > 1
                and parts[1] in raw_names
                and parts[1] != raw_name
            ):
                cross_edges.add((uid, raw_to_safe[parts[1]]))


def _extract_non_python_signals(
    fpath: Path,
    fl: str,
    ext: str,
    cur: Path,
    raw_name: str,
    uid: str,
    raw_names: set[str],
    raw_to_safe: dict[str, str],
    go_module: str,
    cross_edges: set[tuple[str, str]],
    lang_counts: dict[str, int],
) -> int:
    """Extract language counts, non-Python test presence, and Go/Bazel/TS/Rust/C++ dependency edges."""
    test_delta = 0
    is_test_dir = any(p.lower() in ("test", "tests", "__tests__") for p in cur.parts[-2:])

    if ext == ".go":
        lang_counts["go"] += 1
        if fl.endswith("_test.go") or is_test_dir:
            test_delta = 1
        if go_module:
            try:
                head = fpath.read_text(encoding="utf-8", errors="ignore")[:8192]
                prefix = go_module + "/"
                for imp in _GO_QUOTED_IMPORT_RE.findall(head):
                    if imp.startswith(prefix):
                        target_unit = imp[len(prefix) :].split("/", 1)[0]
                        if target_unit in raw_names and target_unit != raw_name:
                            cross_edges.add((uid, raw_to_safe[target_unit]))
            except OSError:
                pass
    elif fl in ("build", "build.bazel"):
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")[:32768]
            for dep_unit in _BAZEL_DEP_RE.findall(text):
                if dep_unit in raw_names and dep_unit != raw_name:
                    cross_edges.add((uid, raw_to_safe[dep_unit]))
        except OSError:
            pass
    elif ext in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
        lang_counts["typescript"] += 1
        if ".test." in fl or ".spec." in fl or is_test_dir:
            test_delta = 1
        try:
            head = fpath.read_text(encoding="utf-8", errors="ignore")[:8192]
            for rel_unit in _TS_REL_IMPORT_RE.findall(head):
                if rel_unit in raw_names and rel_unit != raw_name:
                    cross_edges.add((uid, raw_to_safe[rel_unit]))
        except OSError:
            pass
    elif ext == ".rs":
        lang_counts["rust"] += 1
        if fl.endswith("_test.rs") or is_test_dir:
            test_delta = 1
        try:
            head = fpath.read_text(encoding="utf-8", errors="ignore")[:8192]
            for crate_tok in _RUST_USE_RE.findall(head):
                if crate_tok in raw_names and crate_tok != raw_name:
                    cross_edges.add((uid, raw_to_safe[crate_tok]))
        except OSError:
            pass
    elif ext in (".cc", ".cpp", ".cu", ".cuh", ".h", ".hpp"):
        lang_counts["cpp"] += 1
        if "test" in fl or is_test_dir:
            test_delta = 1
        try:
            head = fpath.read_text(encoding="utf-8", errors="ignore")[:8192]
            for inc_unit in _CPP_INCLUDE_RE.findall(head):
                if inc_unit in raw_names and inc_unit != raw_name:
                    cross_edges.add((uid, raw_to_safe[inc_unit]))
        except OSError:
            pass
    return test_delta


def discover_portfolio_repos(portfolio_path: str | Path) -> list[Path]:
    """Discover child repositories/monorepos under a multi-repo parent folder."""
    root = Path(portfolio_path).resolve()
    if not root.is_dir():
        return []
    repos: list[Path] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name.startswith(".") or child.name in _PRUNE_DIRS:
            continue
        if (child / ".git").exists() or _unit_looks_like_project(child):
            repos.append(child)
        else:
            sub_resolved = resolve_repo_root(child)
            if sub_resolved != child or _unit_looks_like_project(child):
                repos.append(child)
    return repos


def _unit_looks_like_project(dir_path: Path) -> bool:
    """Return True if a top-level subdirectory contains manifests, README, or Python sources."""
    try:
        for entry in dir_path.iterdir():
            name_low = entry.name.lower()
            if entry.is_file() and (
                name_low in _MANIFEST_FILES
                or name_low in _README_NAMES
                or entry.suffix.lower() in (".py", ".ts", ".js", ".rs", ".go", ".cc", ".cpp", ".cu", ".ipynb")
            ):
                return True
            if entry.is_dir() and entry.name not in _PRUNE_DIRS and not entry.name.startswith("."):
                for sub in entry.iterdir():
                    if sub.is_file() and (sub.suffix.lower() == ".py" or sub.name.lower() in _MANIFEST_FILES):
                        return True
    except OSError:
        return False
    return False


class RepoOntologyModelSource(ModelSource):
    """Extracts a typed, schema-governed OntologyModel directly from a code/research repository."""

    def __init__(
        self,
        repo_path: str | Path,
        *,
        vault_dir: str | Path | None = None,
        max_depth: int = 4,
        max_files_per_unit: int | None = 120,
    ) -> None:
        if not HAS_ONTOLOGY_SPIDER:
            raise RuntimeError(
                "The 'ontology_spider' engine is not installed. "
                "Install it via: pip install -e <path-to-Ontology-Spider>"
            )
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.is_dir():
            raise FileNotFoundError(f"Repository path does not exist or is not a directory: {self.repo_path}")
        self.resolved_root = resolve_repo_root(self.repo_path)
        self.vault_dir = Path(vault_dir).resolve() if vault_dir is not None else None
        self.max_depth = max(1, int(max_depth))
        self.max_files_per_unit = max_files_per_unit

    def _discover_units(self) -> list[Path]:
        """Discover research subprojects in monorepos, or fall back to package roots."""
        candidates = [
            d
            for d in sorted(self.resolved_root.iterdir(), key=lambda p: p.name)
            if d.is_dir() and not d.name.startswith(".") and d.name not in _PRUNE_DIRS and _unit_looks_like_project(d)
        ]
        if len(candidates) >= 2:
            # Check for conventional monorepo wrappers (packages/*, plugins/*)
            non_generic = [c for c in candidates if c.name not in ("tests", "docs", "scripts", "examples")]
            if len(non_generic) >= 2:
                return candidates
        return [self.resolved_root]

    def load(self) -> OntologyModel:
        """Scan repository within bounded depth and construct a schema-checked OntologyModel."""
        repo_safe = _sanitize_identifier(self.resolved_root.name)
        model = OntologyModel(uri=f"urn:repo:{repo_safe}")
        prov = Provenance(source=f"repo:{self.resolved_root.name}", turn_id="repo_scan")

        # Declare canonical repository ontology schema
        schema_triples = [
            ("research_project", SUBCLASS_OF, "repository_unit"),
            ("rl_and_control_project", SUBCLASS_OF, "research_project"),
            ("nlp_and_llm_project", SUBCLASS_OF, "research_project"),
            ("vision_and_3d_project", SUBCLASS_OF, "research_project"),
            ("graph_and_program_project", SUBCLASS_OF, "research_project"),
            ("science_and_bio_project", SUBCLASS_OF, "research_project"),
            ("speech_and_audio_project", SUBCLASS_OF, "research_project"),
            ("privacy_fairness_safety_project", SUBCLASS_OF, "research_project"),
            ("optimization_and_compression_project", SUBCLASS_OF, "research_project"),
            ("systems_and_runtime_project", SUBCLASS_OF, "research_project"),
            ("agent_orchestration_project", SUBCLASS_OF, "research_project"),
            ("general_ml_project", SUBCLASS_OF, "research_project"),
            ("ml_framework", SUBCLASS_OF, "technical_dependency"),
            ("runtime_artifact", SUBCLASS_OF, "build_artifact"),
            ("config_system", SUBCLASS_OF, "technical_dependency"),
            ("arxiv_paper", SUBCLASS_OF, "provenance_artifact"),
            ("harness_artifact", SUBCLASS_OF, "brain_harness_node"),
            ("research_project", DISJOINT_WITH, "ml_framework"),
            ("research_project", DISJOINT_WITH, "arxiv_paper"),
            ("depends_on_project", DOMAIN, "research_project"),
            ("depends_on_project", RANGE, "research_project"),
            ("depends_on_project", ACYCLIC, "true"),
            ("uses_framework", DOMAIN, "research_project"),
            ("uses_framework", RANGE, "ml_framework"),
            ("exports_artifact", DOMAIN, "research_project"),
            ("exports_artifact", RANGE, "runtime_artifact"),
            ("uses_config_system", DOMAIN, "research_project"),
            ("uses_config_system", RANGE, "config_system"),
            ("cites_paper", DOMAIN, "research_project"),
            ("cites_paper", RANGE, "arxiv_paper"),
            ("bridges_to_harness", DOMAIN, "research_project"),
            ("bridges_to_harness", RANGE, "harness_artifact"),
        ]
        for subj, pred, obj in schema_triples:
            model.add_assertion(Relation(subj, pred, obj), prov)

        units = self._discover_units()
        raw_names = {u.name for u in units}
        root_pkg_alias = _sanitize_identifier(self.resolved_root.name).replace("-", "_")
        candidate_py_tokens = raw_names | {n.replace("-", "_") for n in raw_names} | {"google_research", root_pkg_alias}
        go_module = _detect_go_module(self.resolved_root)
        learned_map = _discover_vault_learned_projects(self.vault_dir)

        raw_to_safe: dict[str, str] = {}
        safe_to_raw: dict[str, str] = {}
        for u in units:
            if _sanitize_identifier(u.name) == u.name:
                _alloc_unique_identifier(u.name, raw_to_safe, safe_to_raw)
        for u in units:
            _alloc_unique_identifier(u.name, raw_to_safe, safe_to_raw)

        cross_edges: set[tuple[str, str]] = set()

        for unit_dir in units:
            raw_name = unit_dir.name
            uid = raw_to_safe[raw_name]
            fws: set[str] = set()
            readme_text = ""
            py_count = 0
            test_count = 0
            gin_count = 0
            ipynb_count = 0
            lang_counts = {"go": 0, "typescript": 0, "rust": 0, "cpp": 0}
            has_req = False
            has_setup = False
            has_pyproject = False
            has_go_mod = False
            has_pkg_json = False
            has_cargo = False
            has_run_sh = False
            has_build = False
            has_tflite = False
            has_saved_model = False
            arxiv_ids: list[str] = []
            files_seen = 0
            unit_depth = len(unit_dir.parts)

            for root, dirs, files in os.walk(unit_dir):
                cur = Path(root)
                rel_depth = len(cur.parts) - unit_depth
                dirs[:] = [
                    d
                    for d in sorted(dirs)
                    if d not in _PRUNE_DIRS and not d.startswith(".") and rel_depth < self.max_depth
                ]
                for fname in sorted(files):
                    if self.max_files_per_unit is not None and files_seen >= self.max_files_per_unit:
                        break
                    files_seen += 1
                    fpath = cur / fname
                    fl = fname.lower()
                    ext = fpath.suffix.lower()

                    if fl in _README_NAMES and not readme_text:
                        try:
                            readme_text = fpath.read_text(encoding="utf-8", errors="ignore")[:20000]
                            for m in _ARXIV_RE.findall(readme_text):
                                if m not in arxiv_ids:
                                    arxiv_ids.append(m)
                        except OSError:
                            pass
                    elif fl == "requirements.txt":
                        has_req = True
                    elif fl == "setup.py":
                        has_setup = True
                    elif fl == "pyproject.toml":
                        has_pyproject = True
                    elif fl == "go.mod":
                        has_go_mod = True
                    elif fl == "package.json":
                        has_pkg_json = True
                    elif fl == "cargo.toml":
                        has_cargo = True
                    elif fl == "run.sh":
                        has_run_sh = True
                    elif fl in ("build", "build.bazel"):
                        has_build = True

                    if ext == ".py":
                        py_count += 1
                        if "test" in fl:
                            test_count += 1
                        try:
                            if fpath.stat().st_size <= 400_000:
                                src = fpath.read_text(encoding="utf-8", errors="ignore")
                                _extract_python_signals(
                                    src,
                                    raw_name,
                                    uid,
                                    candidate_py_tokens,
                                    raw_names,
                                    raw_to_safe,
                                    root_pkg_alias,
                                    fws,
                                    cross_edges,
                                )
                        except OSError:
                            pass
                    elif ext == ".gin":
                        gin_count += 1
                    elif ext == ".ipynb":
                        ipynb_count += 1
                    elif ext == ".tflite":
                        has_tflite = True
                    elif fl == "saved_model.pb":
                        has_saved_model = True
                    else:
                        test_count += _extract_non_python_signals(
                            fpath,
                            fl,
                            ext,
                            cur,
                            raw_name,
                            uid,
                            raw_names,
                            raw_to_safe,
                            go_module,
                            cross_edges,
                            lang_counts,
                        )
                if self.max_files_per_unit is not None and files_seen >= self.max_files_per_unit:
                    break

            cpp_count = lang_counts["cpp"]
            all_lang_counts = {"python": py_count, **lang_counts}
            dom_lang, dom_count = max(all_lang_counts.items(), key=lambda kv: kv[1])
            primary_language = dom_lang if dom_count > 0 else "docs_or_config"
            code_files = sum(all_lang_counts.values())

            domain_cls = _classify_domain(raw_name, readme_text)
            prim_fw = _primary_framework(fws)
            packaging = (
                "pyproject"
                if has_pyproject
                else "setup_py"
                if has_setup
                else "requirements"
                if has_req
                else "go_mod"
                if has_go_mod
                else "npm"
                if has_pkg_json
                else "cargo"
                if has_cargo
                else "none"
            )
            size_tier = (
                "large"
                if code_files >= 25
                else "medium"
                if code_files >= 8
                else "small"
                if code_files >= 1
                else "non_python"
            )
            learned_match = _lookup_learned_ki(raw_name, uid, learned_map)
            learned_ki = learned_match[0] if learned_match is not None else None
            learned_match_strength = learned_match[1] if learned_match is not None else "none"
            is_generic_unit = raw_name.strip().lower().replace("-", "_") in _GENERIC_UNIT_NAMES
            harness_learned = learned_ki is not None

            attrs: dict[str, Any] = {
                "raw_name": raw_name,
                "domain_class": domain_cls,
                "primary_framework": prim_fw,
                "primary_language": primary_language,
                "packaging": packaging,
                "size_tier": size_tier,
                "has_readme": bool(readme_text),
                "has_tests": test_count > 0,
                "has_gin": gin_count > 0,
                "has_ipynb": ipynb_count > 0,
                "has_cpp_cuda": cpp_count > 0,
                "has_run_sh": has_run_sh,
                "has_arxiv": len(arxiv_ids) > 0,
                "has_bazel_build": has_build,
                "has_tflite_or_pb": has_tflite or has_saved_model,
                "harness_learned": harness_learned,
                "learned_ki_id": learned_ki or "",
                "learned_match_strength": learned_match_strength,
                "is_generic_unit": is_generic_unit,
                "py_file_count": py_count,
                "test_file_count": test_count,
                "gin_file_count": gin_count,
            }
            model.add_entity(Entity(id=uid, name=raw_name, attributes=attrs))
            model.add_assertion(Relation(uid, INSTANCE_OF, domain_cls), prov)

            for fw in sorted(fws):
                fw_id = f"fw_{fw}"
                if fw_id not in model.entities:
                    model.add_entity(Entity(id=fw_id, name=fw, attributes={"kind": "ml_framework"}))
                    model.add_assertion(Relation(fw_id, INSTANCE_OF, "ml_framework"), prov)
                model.add_assertion(Relation(uid, "uses_framework", fw_id), prov)

            if gin_count > 0:
                if "cfg_gin" not in model.entities:
                    model.add_entity(Entity(id="cfg_gin", name="Gin Config", attributes={"kind": "config_system"}))
                    model.add_assertion(Relation("cfg_gin", INSTANCE_OF, "config_system"), prov)
                model.add_assertion(Relation(uid, "uses_config_system", "cfg_gin"), prov)
            if "absl" in fws:
                if "cfg_absl_flags" not in model.entities:
                    model.add_entity(
                        Entity(id="cfg_absl_flags", name="absl.flags", attributes={"kind": "config_system"})
                    )
                    model.add_assertion(Relation("cfg_absl_flags", INSTANCE_OF, "config_system"), prov)
                model.add_assertion(Relation(uid, "uses_config_system", "cfg_absl_flags"), prov)

            if has_tflite:
                if "art_tflite" not in model.entities:
                    model.add_entity(
                        Entity(id="art_tflite", name="TFLite FlatBuffer", attributes={"kind": "runtime_artifact"})
                    )
                    model.add_assertion(Relation("art_tflite", INSTANCE_OF, "runtime_artifact"), prov)
                model.add_assertion(Relation(uid, "exports_artifact", "art_tflite"), prov)
            if has_saved_model:
                if "art_saved_model" not in model.entities:
                    model.add_entity(
                        Entity(id="art_saved_model", name="TF SavedModel", attributes={"kind": "runtime_artifact"})
                    )
                    model.add_assertion(Relation("art_saved_model", INSTANCE_OF, "runtime_artifact"), prov)
                model.add_assertion(Relation(uid, "exports_artifact", "art_saved_model"), prov)

            for ax in arxiv_ids[:3]:
                ax_id = f"arxiv_{ax.replace('.', '_')}"
                if ax_id not in model.entities:
                    model.add_entity(Entity(id=ax_id, name=f"arXiv:{ax}", attributes={"arxiv_id": ax}))
                    model.add_assertion(Relation(ax_id, INSTANCE_OF, "arxiv_paper"), prov)
                model.add_assertion(Relation(uid, "cites_paper", ax_id), prov)

            if learned_ki:
                kid = _sanitize_identifier(learned_ki)
                if kid not in model.entities:
                    model.add_entity(Entity(id=kid, name=learned_ki, attributes={"kind": "harness_artifact"}))
                    model.add_assertion(Relation(kid, INSTANCE_OF, "harness_artifact"), prov)
                model.add_assertion(Relation(uid, "bridges_to_harness", kid), prov)

        for src_uid, dst_uid in sorted(cross_edges):
            model.add_assertion(Relation(src_uid, "depends_on_project", dst_uid), prov)

        return model


__all__ = ["RepoOntologyModelSource", "discover_portfolio_repos", "resolve_repo_root"]
