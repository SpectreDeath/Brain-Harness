"""O(1) binary byte-offset seek table index for large transcript logs (Rule 48)."""

from __future__ import annotations

from pathlib import Path


class ByteOffsetSeekTable:
    """O(1) binary byte-offset seek index for large transcript logs (Rule 48)."""

    def __init__(self, file_path: Path | str) -> None:
        self.file_path = Path(file_path)
        self.offsets: dict[int, tuple[int, int]] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Scan file once in binary mode to record byte offset and length per line."""
        if not self.file_path.exists():
            return

        with open(self.file_path, "rb") as f:
            idx = 0
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                length = len(line)
                self.offsets[idx] = (offset, length)
                idx += 1

    def get_line(self, line_idx: int) -> str | None:
        """Fetch line by index in O(1) time without loading entire file."""
        if line_idx not in self.offsets:
            return None
        offset, length = self.offsets[line_idx]
        with open(self.file_path, "rb") as f:
            f.seek(offset)
            raw = f.read(length)
            return raw.decode("utf-8", errors="ignore")

    def total_lines(self) -> int:
        return len(self.offsets)


__all__ = [
    "ByteOffsetSeekTable",
]
