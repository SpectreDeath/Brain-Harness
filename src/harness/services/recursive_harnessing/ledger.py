"""Budget accounting: R = 4k rollouts and P = 3k improvement stages per mode.

Distilled from google/harness2 `core.ledger`. Each mode runs k shared base rollouts, 2k INV/DOM
candidate rollouts and k final rollouts (R = 4k), plus k INV, k DOM and k composition sessions
(P = 3k). Duplicate labels are checked *before* counts because a duplicate can satisfy them
while silently hiding an overwritten candidate.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def expected_rollouts(k: int) -> int:
    """R = 4k: k shared base + 2k candidates + k finals."""
    return 4 * int(k)


def expected_sessions(k: int) -> int:
    """P = 3k: k INV + k DOM + k compositions."""
    return 3 * int(k)


class BudgetError(AssertionError):
    """The ledger did not land on the budget identity."""


@dataclass(slots=True)
class Entry:
    kind: str
    label: str
    usd: float = 0.0
    cached: bool = False
    attempts: int = 1


@dataclass(slots=True)
class BudgetLedger:
    """Everything one mode spent on one task, recorded as it happens."""

    mode: str
    task_id: str
    k: int
    entries: list[Entry] = field(default_factory=list)

    def rollout(self, label: str, usd: float = 0.0, *, cached: bool = False) -> None:
        self.entries.append(Entry("rollout", label, usd, cached))

    def session(self, label: str, usd: float = 0.0, *, cached: bool = False, attempts: int = 1) -> None:
        self.entries.append(Entry("session", label, usd, cached, attempts))

    def labels(self, kind: str) -> list[str]:
        return [e.label for e in self.entries if e.kind == kind]

    @property
    def R(self) -> int:  # noqa: N802 - mirrors the paper's notation
        return len(self.labels("rollout"))

    @property
    def P(self) -> int:  # noqa: N802
        return len(self.labels("session"))

    def _usd(self, kind: str | None = None) -> float:
        return round(sum(e.usd for e in self.entries if kind in (None, e.kind)), 6)

    @property
    def usd(self) -> float:
        return self._usd()

    def assert_identity(self) -> None:
        """Raise unless the entries show exactly R=4k and P=3k with no duplicate label."""
        want_r, want_p = expected_rollouts(self.k), expected_sessions(self.k)
        rl, sl = self.labels("rollout"), self.labels("session")
        dupes = sorted({x for x in rl if rl.count(x) > 1} | {x for x in sl if sl.count(x) > 1})
        if not dupes and self.R == want_r and self.P == want_p:
            return
        lines = [
            f"{self.mode}-{self.k} {self.task_id}: R={self.R} (want {want_r}), P={self.P} (want {want_p})",
            f"  rollouts: {', '.join(rl) or '(none)'}",
            f"  sessions: {', '.join(sl) or '(none)'}",
        ]
        if dupes:
            lines.append(
                f"  DUPLICATE labels: {dupes} -- two stages wrote the same run id and one silently overwrote the other"
            )
        raise BudgetError("\n".join(lines))

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "task_id": self.task_id,
            "k": self.k,
            "R": self.R,
            "expected_R": expected_rollouts(self.k),
            "P": self.P,
            "expected_P": expected_sessions(self.k),
            "session_attempts": sum(e.attempts for e in self.entries if e.kind == "session"),
            "usd": self.usd,
            "rollout_usd": self._usd("rollout"),
            "session_usd": self._usd("session"),
            "rollouts": self.labels("rollout"),
            "sessions": self.labels("session"),
        }
