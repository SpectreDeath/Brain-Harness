"""Federated Brain Bridge & Knowledge Library Attachment Plugin for Brain Harness."""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# In-memory registry of attached external brains
# Schema: alias -> {
#   "alias": str,
#   "path": str,
#   "format": str,
#   "mode": str,
#   "chunks": list[dict[str, Any]],
#   "doc_freq": dict[str, int],
#   "total_docs": int,
#   "trajectories": list[dict[str, Any]],
#   "summary": dict[str, Any]
# }
_MOUNTS: dict[str, dict[str, Any]] = {}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words and subwords."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    tokens: list[str] = []
    for w in words:
        low = w.lower()
        if len(low) > 1:
            tokens.append(low)
    return tokens


def _compute_vector(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    """Compute normalized TF-IDF vector for tokens."""
    tf = Counter(tokens)
    vec: dict[str, float] = {}
    norm_sq = 0.0

    for term, count in tf.items():
        tf_weight = 1.0 + math.log(count)
        idf_weight = math.log((total_docs + 1.0) / (doc_freq.get(term, 0) + 1.0)) + 1.0
        weight = tf_weight * idf_weight
        vec[term] = weight
        norm_sq += weight * weight

    norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
    for term in vec:
        vec[term] /= norm

    return vec


def _detect_brain_format(root: Path) -> str:
    """Detect format of the external brain or knowledge store."""
    if (root / ".system_generated" / "logs").exists() or (root / "transcript.jsonl").exists():
        return "antigravity_brain"
    if any(root.glob("**/transcript.jsonl")):
        return "antigravity_brain"
    if (root / ".harness").exists() or (root / "src" / "harness").exists():
        return "harness_instance"
    if (root / ".claude").exists() or (root / ".cursor").exists() or (root / ".cursorrules").exists():
        return "ide_memo"
    if (root / ".obsidian").exists():
        return "obsidian_vault"
    # Check for markdown density with wikilinks
    md_files = list(root.glob("*.md"))[:10]
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
            if "[[" in content and "]]" in content:
                return "obsidian_vault"
        except (OSError, UnicodeDecodeError):
            pass
    return "raw_docs"


def _index_text_files(root: Path, target_exts: set[str], chunk_lines: int = 30) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Scan and chunk text and code files."""
    chunks: list[dict[str, Any]] = []
    doc_freq: dict[str, int] = defaultdict(int)

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv", "node_modules")]
        for file_name in files:
            file_path = Path(current_root) / file_name
            if file_path.suffix.lower() not in target_exts:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            lines = content.splitlines()
            if not lines:
                continue

            step = max(10, chunk_lines - 5)
            for i in range(0, len(lines), step):
                chunk_slice = lines[i : i + chunk_lines]
                if not chunk_slice:
                    continue
                chunk_text = "\n".join(chunk_slice)
                tokens = _tokenize(chunk_text)
                if not tokens:
                    continue

                chunk_obj = {
                    "id": len(chunks),
                    "file": str(file_path.relative_to(root)),
                    "start_line": i + 1,
                    "end_line": min(len(lines), i + len(chunk_slice)),
                    "content": chunk_text,
                    "tokens": tokens,
                    "type": "document_chunk",
                }
                chunks.append(chunk_obj)
                for term in set(tokens):
                    doc_freq[term] += 1

    return chunks, doc_freq


def _parse_transcripts(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Parse transcript JSONL files for conversational and trajectory memory."""
    transcript_files: list[Path] = []
    if (root / "transcript.jsonl").exists():
        transcript_files.append(root / "transcript.jsonl")
    transcript_files.extend(root.glob("**/.system_generated/logs/transcript*.jsonl"))
    transcript_files.extend(root.glob("**/transcript*.jsonl"))

    # Deduplicate paths
    unique_paths = list({p.resolve(): p for p in transcript_files}.values())
    chunks: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    doc_freq: dict[str, int] = defaultdict(int)

    for tf in unique_paths:
        try:
            with tf.open("r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                    except json.JSONDecodeError:
                        continue

                    step_type = record.get("type", "UNKNOWN")
                    content = record.get("content", "")
                    tool_calls = record.get("tool_calls", [])

                    # Summarize trajectory
                    traj_entry = {
                        "file": str(tf.relative_to(root) if tf.is_relative_to(root) else tf.name),
                        "step_index": record.get("step_index", line_idx),
                        "type": step_type,
                        "status": record.get("status", "DONE"),
                        "tool_names": [tc.get("name") if isinstance(tc, dict) else str(tc) for tc in tool_calls] if tool_calls else [],
                        "summary": str(content)[:200] if content else "",
                    }
                    trajectories.append(traj_entry)

                    # Build searchable chunk
                    text_blob = f"Type: {step_type}\nContent: {content}\nTools: {json.dumps(tool_calls)}"
                    tokens = _tokenize(text_blob)
                    if tokens:
                        chunk_obj = {
                            "id": len(chunks),
                            "file": traj_entry["file"],
                            "start_line": line_idx + 1,
                            "end_line": line_idx + 1,
                            "content": text_blob[:800],
                            "tokens": tokens,
                            "type": "transcript_step",
                            "step_index": traj_entry["step_index"],
                        }
                        chunks.append(chunk_obj)
                        for term in set(tokens):
                            doc_freq[term] += 1
        except (OSError, UnicodeDecodeError):
            continue

    return chunks, trajectories, doc_freq


def brain_attach(
    folder_path: str,
    alias: str | None = None,
    read_transcripts: bool = True,
    attach_mode: str = "lens",
) -> dict[str, Any]:
    """Inspect and mount an external brain, IDE state, or knowledge directory."""
    global _MOUNTS

    root = Path(folder_path).resolve()
    if not root.exists() or not root.is_dir():
        return {"status": "error", "error": f"Directory not found: {folder_path}"}

    detected_format = _detect_brain_format(root)
    mount_alias = alias or root.name.lower().replace(" ", "_").replace("-", "_")

    # Index text and code files
    target_exts = {".py", ".md", ".json", ".txt", ".yaml", ".yml", ".toml", ".rst"}
    doc_chunks, doc_freq = _index_text_files(root, target_exts)

    transcript_chunks: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    if read_transcripts:
        transcript_chunks, trajectories, t_doc_freq = _parse_transcripts(root)
        for term, cnt in t_doc_freq.items():
            doc_freq[term] += cnt

    all_chunks = doc_chunks + transcript_chunks
    # Renumber chunk ids
    for idx, c in enumerate(all_chunks):
        c["id"] = idx

    total_docs = len(all_chunks)

    # Precalculate TF-IDF vectors
    for c in all_chunks:
        c["vector"] = _compute_vector(c["tokens"], doc_freq, total_docs)

    summary = {
        "format": detected_format,
        "mode": attach_mode,
        "total_chunks": len(all_chunks),
        "document_chunks": len(doc_chunks),
        "transcript_chunks": len(transcript_chunks),
        "trajectories_recorded": len(trajectories),
        "unique_terms": len(doc_freq),
    }

    _MOUNTS[mount_alias] = {
        "alias": mount_alias,
        "path": str(root),
        "format": detected_format,
        "mode": attach_mode,
        "chunks": all_chunks,
        "doc_freq": doc_freq,
        "total_docs": total_docs,
        "trajectories": trajectories,
        "summary": summary,
    }

    return {
        "status": "ok",
        "alias": mount_alias,
        "path": str(root),
        "detected_format": detected_format,
        "mode": attach_mode,
        "summary": summary,
    }


def brain_query(
    query: str,
    brain_alias: str | None = None,
    include_trajectories: bool = True,
    top_k: int = 5,
) -> dict[str, Any]:
    """Query across one or all mounted external brains for knowledge, solutions, or transcripts."""
    if not _MOUNTS:
        return {"status": "ok", "query": query, "results_count": 0, "results": [], "note": "No brains attached. Run brain_attach first."}

    targets = [_MOUNTS[brain_alias]] if brain_alias and brain_alias in _MOUNTS else list(_MOUNTS.values())
    if brain_alias and brain_alias not in _MOUNTS:
        return {"status": "error", "error": f"Attached brain alias '{brain_alias}' not found."}

    query_tokens = _tokenize(query)
    if not query_tokens:
        return {"status": "ok", "query": query, "results_count": 0, "results": []}

    scored_results: list[dict[str, Any]] = []

    for mount in targets:
        q_vec = _compute_vector(query_tokens, mount["doc_freq"], mount["total_docs"])
        for chunk in mount["chunks"]:
            if not include_trajectories and chunk.get("type") == "transcript_step":
                continue

            score = sum(q_weight * chunk["vector"].get(term, 0.0) for term, q_weight in q_vec.items())
            if score > 0.01:
                scored_results.append({
                    "score": round(score, 4),
                    "brain_alias": mount["alias"],
                    "brain_format": mount["format"],
                    "type": chunk.get("type", "chunk"),
                    "file": chunk["file"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "snippet": chunk["content"][:350] + ("..." if len(chunk["content"]) > 350 else ""),
                })

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    top_results = scored_results[:top_k]

    return {
        "status": "ok",
        "query": query,
        "searched_brains": [m["alias"] for m in targets],
        "results_count": len(top_results),
        "results": top_results,
    }


def brain_list_attached() -> dict[str, Any]:
    """List all currently mounted external brains, their detected formats, and index statistics."""
    mount_list = [
        {
            "alias": m["alias"],
            "path": m["path"],
            "format": m["format"],
            "mode": m["mode"],
            "summary": m["summary"],
        }
        for m in _MOUNTS.values()
    ]
    return {
        "status": "ok",
        "attached_count": len(mount_list),
        "brains": mount_list,
    }


def brain_detach(brain_alias: str) -> dict[str, Any]:
    """Unmount a foreign brain and release its memory indexes."""
    global _MOUNTS
    if brain_alias not in _MOUNTS:
        return {"status": "error", "error": f"Attached brain alias '{brain_alias}' not found."}

    removed = _MOUNTS.pop(brain_alias)
    return {
        "status": "ok",
        "detached_alias": brain_alias,
        "path": removed["path"],
    }
