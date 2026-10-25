"""Frontmatter shelf indexer for Interpretable Context Methodology (ICM)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import IcmIndexReport


def _split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[3:end], text[end + 4 :]
    return "", text


def _extract_field(front: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.+)$", front, re.M)
    if not m:
        return ""
    val = m.group(1).strip()
    if val and val[0] not in "\"'":
        val = re.split(r"\s+#", val, maxsplit=1)[0]
    if len(val) > 1 and val[0] == val[-1] == '"':
        try:
            return json.loads(val)
        except ValueError:
            return val[1:-1]
    return val[1:-1] if len(val) > 1 and val[0] == val[-1] == "'" else val


class IcmIndexer:
    """Generates and updates _index.md files across records and shelves."""

    def rebuild_index(self, folders: list[str | Path], root: str | Path | None = None) -> IcmIndexReport:
        root_path = Path(root).resolve() if root else Path.cwd()
        folders_indexed: list[str] = []
        index_files_written: list[str] = []
        total_notes = 0

        for f in folders:
            folder_path = (root_path / f).resolve() if not Path(f).is_absolute() else Path(f)
            if not folder_path.exists() or not folder_path.is_dir():
                continue

            folders_indexed.append(str(folder_path.relative_to(root_path)).replace("\\", "/"))
            lines = [f"# Index of {folder_path.name}\n", "Generated index. Do not edit by hand.\n"]

            notes = sorted(
                [p for p in folder_path.glob("*.md") if p.name not in ("_index.md", "index.md")],
                key=lambda x: x.name,
            )

            for sub in sorted(folder_path.iterdir()):
                if sub.is_dir() and (sub / "CONTEXT.md").exists():
                    notes.append(sub / "CONTEXT.md")

            for note in notes:
                total_notes += 1
                content = note.read_text(encoding="utf-8", errors="replace")
                front, body = _split_frontmatter(content)
                title = _extract_field(front, "title")
                status = _extract_field(front, "status")
                desc = _extract_field(front, "description")

                if not title:
                    hm = re.search(r"^#+\s+(.+)$", body, re.M)
                    title = hm.group(1).strip() if hm else note.stem

                target_rel = note.name if note.parent == folder_path else f"{note.parent.name}/CONTEXT.md"
                desc_str = f" — {desc}" if desc else ""
                status_str = f" ({status})" if status else ""
                lines.append(f"- [{title}]({target_rel}){desc_str}{status_str}")

            out_file = folder_path / "_index.md"
            out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            index_files_written.append(str(out_file.relative_to(root_path)).replace("\\", "/"))

        return IcmIndexReport(
            folders_indexed=folders_indexed,
            total_notes=total_notes,
            index_files_written=index_files_written,
        )
