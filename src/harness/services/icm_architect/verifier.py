"""Link and quote verification engines for Interpretable Context Methodology (ICM)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .auditor import SKIP_DIRS
from .models import IcmLinkCheckReport, IcmQuoteCheckReport


def _split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[3:end], text[end + 4 :]
    return "", text


class IcmVerifier:
    """Verifies markdown link graphs and verbatim quotes against raw sources."""

    def verify_links(
        self,
        root: str | Path = ".",
        skip_folders: list[str] | None = None,
        graph_file: str | Path | None = None,
    ) -> IcmLinkCheckReport:
        root_path = Path(root).resolve()
        skips = set(skip_folders or []) | SKIP_DIRS
        link_regex = re.compile(r"\[[^\]]*\]\((<[^>]+>|[^)\s]+)\)")
        tick_regex = re.compile(r"`([^`\s]+)`")
        import_regex = re.compile(r"^@(\S+\.md)\s*$")
        link_keys = re.compile(r"^(?:consumes|produces):\s*(.+)$", re.M)

        total_links, resolved_links = 0, 0
        broken_links: list[dict[str, str]] = []
        graph_nodes: list[dict[str, Any]] = []
        graph_edges: list[dict[str, Any]] = []

        if not root_path.exists():
            return IcmLinkCheckReport(
                total_links=0, resolved_links=0,
                broken_links=[{"file": str(root_path), "link": "Directory does not exist"}],
            )

        md_files = [p for p in root_path.rglob("*.md") if not any(part in skips for part in p.parts)]

        for p in md_files:
            rel_file = str(p.relative_to(root_path)).replace("\\", "/")
            graph_nodes.append({"path": rel_file, "title": p.stem})
            content = p.read_text(encoding="utf-8", errors="replace")
            front, body = _split_frontmatter(content)

            # 1. Markdown Links
            for m in link_regex.finditer(body):
                target = m.group(1).strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")) or "{" in target:
                    continue
                total_links += 1
                target_clean = target.split("#")[0]
                target_path = (p.parent / target_clean).resolve()
                if target_path.exists():
                    resolved_links += 1
                    graph_edges.append({"source": rel_file, "target": target_clean})
                else:
                    broken_links.append({"file": rel_file, "link": target, "type": "markdown_link"})

            # 2. Consumes/Produces Frontmatter
            for m in link_keys.finditer(front):
                val = m.group(1).strip()
                targets = [t.strip() for t in val.split(",") if t.strip().endswith(".md")]
                for target in targets:
                    total_links += 1
                    target_path = (p.parent / target).resolve()
                    if target_path.exists():
                        resolved_links += 1
                        graph_edges.append({"source": rel_file, "target": target})
                    else:
                        broken_links.append({"file": rel_file, "link": target, "type": "frontmatter_link"})

            # 3. Pointer Imports (@AGENTS.md)
            for line in content.splitlines():
                imp = import_regex.match(line.strip())
                if imp:
                    target = imp.group(1).lstrip("./")
                    total_links += 1
                    target_path = (root_path / target).resolve()
                    if target_path.exists():
                        resolved_links += 1
                        graph_edges.append({"source": rel_file, "target": target})
                    else:
                        broken_links.append({"file": rel_file, "link": target, "type": "import_pointer"})

            # 4. Inputs Backticked Paths
            in_inputs = False
            for line in body.splitlines():
                if re.match(r"^#{1,6}\s+Inputs", line, re.I):
                    in_inputs = True
                    continue
                elif in_inputs and re.match(r"^#{1,6}\s+", line):
                    in_inputs = False
                    continue
                if in_inputs and line.strip().startswith("-"):
                    for tm in tick_regex.finditer(line):
                        cand = tm.group(1)
                        if any(c in cand for c in "/\\") and not cand.startswith(("http", "$")):
                            total_links += 1
                            cand_path = (p.parent / cand).resolve()
                            cand_root = (root_path / cand).resolve()
                            if cand_path.exists() or cand_root.exists() or cand_path.parent.exists():
                                resolved_links += 1
                            else:
                                broken_links.append({"file": rel_file, "link": cand, "type": "input_path"})

        if graph_file:
            g_path = Path(graph_file).resolve()
            g_path.parent.mkdir(parents=True, exist_ok=True)
            with open(g_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({"root": "."}) + "\n")
                for node in graph_nodes:
                    f.write(json.dumps({"node": node}) + "\n")
                for edge in graph_edges:
                    f.write(json.dumps({"edge": edge}) + "\n")

        return IcmLinkCheckReport(
            total_links=total_links, resolved_links=resolved_links, broken_links=broken_links,
            graph_nodes=len(graph_nodes), graph_edges=len(graph_edges),
        )

    def verify_quotes(self, root: str | Path = ".", show_cuts: bool = False) -> IcmQuoteCheckReport:
        root_path = Path(root).resolve()
        raw_dir = root_path / "sources" / "raw"
        quote_regex = re.compile(r'"([^"\n]+?)"\s*\(([A-Za-z0-9_.-]+)(?:\s+([^)]*))?\)')

        total_quotes, verified_quotes = 0, 0
        broken_quotes: list[dict[str, str]] = []
        warnings: list[str] = []
        keep_out_violations: list[str] = []

        raw_sources: dict[str, str] = {}
        if raw_dir.exists():
            for f in raw_dir.glob("*"):
                if f.is_file():
                    raw_sources[f.stem.lower()] = f.read_text(encoding="utf-8", errors="replace").lower()

        keep_out_file = root_path / "_meta" / "keep-out.txt"
        keep_outs: list[str] = []
        if keep_out_file.exists():
            keep_outs = [
                line.strip().lower()
                for line in keep_out_file.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

        for p in root_path.rglob("*.md"):
            if any(part in SKIP_DIRS or part in ("raw", "_meta", "_tools", "_templates") for part in p.parts):
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            rel_file = str(p.relative_to(root_path)).replace("\\", "/")

            lower_text = text.lower()
            for ko in keep_outs:
                if re.search(rf"\b{re.escape(ko)}\b", lower_text):
                    keep_out_violations.append(f"{rel_file}: contains keep-out phrase '{ko}'")

            for m in quote_regex.finditer(text):
                total_quotes += 1
                quote_str = m.group(1)
                src_key = m.group(2).lower()
                src_text = raw_sources.get(src_key)

                if not src_text:
                    broken_quotes.append({"file": rel_file, "quote": quote_str[:60], "reason": f"Source key '{src_key}' not found in sources/raw/"})
                    continue

                pieces = [pc.strip() for pc in quote_str.split("...") if pc.strip()]
                all_found, curr_idx = True, 0
                for pc in pieces:
                    clean_pc = re.sub(r"\s+", " ", pc.lower())
                    idx = src_text.find(clean_pc, curr_idx)
                    if idx == -1:
                        all_found = False
                        break
                    curr_idx = idx + len(clean_pc)

                if all_found:
                    verified_quotes += 1
                else:
                    broken_quotes.append({"file": rel_file, "quote": quote_str[:60], "reason": "Verbatim quote not found in source text"})

        return IcmQuoteCheckReport(
            total_quotes=total_quotes, verified_quotes=verified_quotes,
            broken_quotes=broken_quotes, warnings=warnings,
            keep_out_violations=keep_out_violations,
        )
