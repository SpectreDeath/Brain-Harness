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

_DOMAIN_RULES: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = tuple(
    (
        dom,
        tuple(re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in kws),
    )
    for dom, kws in (
        (
            "rl_and_control_project",
            ("reinforcement learning", "rl", "mdp", "q-learning", "actor-critic", "policy gradient", "mujoco", "atari", "bandit", "offline rl"),
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
            ),
        ),
        (
            "vision_and_3d_project",
            ("vision", "image", "video", "nerf", "3d", "segmentation", "object detection", "optical flow", "pose", "diffusion", "gan"),
        ),
        (
            "graph_and_program_project",
            ("graph neural", "gnn", "program synthesis", "ast", "control flow", "knowledge graph", "ontology", "sat", "combinatorial"),
        ),
        (
            "science_and_bio_project",
            ("quantum", "dft", "molecule", "protein", "genomic", "dna", "rna", "climate", "weather", "physics", "pde", "fluid", "chemistry", "fep", "biology", "medical"),
        ),
        (
            "speech_and_audio_project",
            ("speech", "audio", "keyword spotting", "asr", "tts", "acoustic", "waveform", "spectrogram", "music"),
        ),
        (
            "privacy_fairness_safety_project",
            ("differential privacy", "privacy", "fairness", "adversarial", "robustness", "interpretability", "explainability", "calibration", "uncertainty", "watermark"),
        ),
        (
            "optimization_and_compression_project",
            ("pruning", "quantization", "distillation", "nas", "neural architecture search", "hyperparameter", "optimizer", "compression", "sparsity"),
        ),
    )
)


def resolve_repo_root(repo_path: Path) -> Path:
    """Resolve nested archive wrapper roots (e.g. repo-master/repo-master) up to depth 3."""
    current = repo_path.resolve()
    for _ in range(3):
        if any((current / m).is_file() for m in ("pyproject.toml", "setup.py", "package.json", "Cargo.toml", "go.mod", "README.md")):
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
    for fw in ("jax", "flax", "haiku", "optax", "tensorflow", "keras", "torch", "apache_beam", "sklearn", "scipy", "numpy", "pydantic"):
        if fw in fws:
            if fw in ("flax", "haiku", "optax") and "jax" in fws:
                return "jax"
            return fw
    return "none"


def _discover_vault_learned_projects(vault_dir: Path | None) -> dict[str, str]:
    """Scan existing .harness/knowledge directory to map project tokens -> KI IDs."""
    if vault_dir is None or not vault_dir.is_dir():
        return {}
    learned: dict[str, str] = {}
    for child in sorted(vault_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name.startswith("."):
            continue
        meta_file = child / "metadata.json"
        if not meta_file.is_file():
            continue
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        ki_id = str(data.get("id") or data.get("ki_id") or child.name)
        for tag in data.get("tags") or []:
            tag_s = str(tag).strip()
            if tag_s:
                learned.setdefault(tag_s.lower(), ki_id)
        for key in ("id", "ki_id", "source_target", "title"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                for token in re.findall(r"[a-zA-Z0-9_]{3,}", val):
                    learned.setdefault(token.lower(), ki_id)
    return learned


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
            if d.is_dir()
            and not d.name.startswith(".")
            and d.name not in _PRUNE_DIRS
            and _unit_looks_like_project(d)
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
            cpp_count = 0
            has_req = False
            has_setup = False
            has_pyproject = False
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
                    elif fl == "run.sh":
                        has_run_sh = True
                    elif fl == "build":
                        has_build = True

                    if ext == ".py":
                        py_count += 1
                        if "test" in fl:
                            test_count += 1
                        try:
                            if fpath.stat().st_size <= 400_000:
                                src = fpath.read_text(encoding="utf-8", errors="ignore")
                                for fw_name, pat in _FW_PATTERNS.items():
                                    if pat.search(src):
                                        fws.add(fw_name)
                                try:
                                    tree = ast.parse(src)
                                    for node in ast.walk(tree):
                                        mod_names: list[str] = []
                                        if isinstance(node, ast.Import):
                                            mod_names = [a.name for a in node.names]
                                        elif isinstance(node, ast.ImportFrom) and node.module:
                                            mod_names = [node.module]
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
                                except SyntaxError:
                                    pass
                        except OSError:
                            pass
                    elif ext == ".gin":
                        gin_count += 1
                    elif ext == ".ipynb":
                        ipynb_count += 1
                    elif ext in (".cc", ".cpp", ".cu", ".cuh", ".h", ".hpp"):
                        cpp_count += 1
                    elif ext == ".tflite":
                        has_tflite = True
                    elif fl == "saved_model.pb":
                        has_saved_model = True
                if self.max_files_per_unit is not None and files_seen >= self.max_files_per_unit:
                    break

            domain_cls = _classify_domain(raw_name, readme_text)
            prim_fw = _primary_framework(fws)
            packaging = (
                "pyproject"
                if has_pyproject
                else "setup_py"
                if has_setup
                else "requirements"
                if has_req
                else "none"
            )
            size_tier = (
                "large"
                if py_count >= 25
                else "medium"
                if py_count >= 8
                else "small"
                if py_count >= 1
                else "non_python"
            )
            learned_ki = learned_map.get(raw_name.lower()) or learned_map.get(uid.lower())
            harness_learned = learned_ki is not None

            attrs: dict[str, Any] = {
                "raw_name": raw_name,
                "domain_class": domain_cls,
                "primary_framework": prim_fw,
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
                    model.add_entity(Entity(id="cfg_absl_flags", name="absl.flags", attributes={"kind": "config_system"}))
                    model.add_assertion(Relation("cfg_absl_flags", INSTANCE_OF, "config_system"), prov)
                model.add_assertion(Relation(uid, "uses_config_system", "cfg_absl_flags"), prov)

            if has_tflite:
                if "art_tflite" not in model.entities:
                    model.add_entity(Entity(id="art_tflite", name="TFLite FlatBuffer", attributes={"kind": "runtime_artifact"}))
                    model.add_assertion(Relation("art_tflite", INSTANCE_OF, "runtime_artifact"), prov)
                model.add_assertion(Relation(uid, "exports_artifact", "art_tflite"), prov)
            if has_saved_model:
                if "art_saved_model" not in model.entities:
                    model.add_entity(Entity(id="art_saved_model", name="TF SavedModel", attributes={"kind": "runtime_artifact"}))
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


__all__ = ["RepoOntologyModelSource", "resolve_repo_root"]
