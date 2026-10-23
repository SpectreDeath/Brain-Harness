"""System Design Architect Domain Engine.

Provides slotted/frozen domain models and command-line automation for capacity
calculations, 5-dimension interview evaluations, architecture validation, and
production case studies (Spotify, Booking.com, WhatsApp).

Complies with AGENTS.md Rule 12 (Slotted & Frozen Dataclasses), Rule 23 (UTF-8
Stream Codec), and Rule 44 (Zero-Fork Baseline Config).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Any

# Ensure UTF-8 streams on Windows environments (Rule 23)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Workspace sys.path resolution (Rule 50)
_workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_workspace_root / "src") not in sys.path:
    sys.path.insert(0, str(_workspace_root / "src"))
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))


# ==============================================================================
# Slotted & Frozen Domain Models (Rule 12)
# ==============================================================================


@dataclass(slots=True, frozen=True)
class CapacityEstimate:
    """Slotted and immutable record of quantitative capacity calculations."""

    dau: int
    read_write_ratio: float
    read_requests_per_user_day: float
    write_requests_per_user_day: float
    avg_read_payload_bytes: int
    avg_write_payload_bytes: int
    peak_multiplier: float
    avg_read_qps: float
    peak_read_qps: float
    avg_write_qps: float
    peak_write_qps: float
    daily_storage_bytes: int
    yearly_storage_bytes: int
    five_year_storage_bytes: int
    network_ingress_mbps: float
    network_egress_mbps: float

    def __post_init__(self) -> None:
        if self.dau <= 0:
            raise ValueError(f"DAU must be positive, got {self.dau}")
        if self.read_write_ratio <= 0:
            raise ValueError(f"Read:Write ratio must be positive, got {self.read_write_ratio}")
        if self.peak_multiplier < 1.0:
            raise ValueError(f"Peak multiplier must be >= 1.0, got {self.peak_multiplier}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dau": self.dau,
            "read_write_ratio": self.read_write_ratio,
            "avg_read_qps": round(self.avg_read_qps, 2),
            "peak_read_qps": round(self.peak_read_qps, 2),
            "avg_write_qps": round(self.avg_write_qps, 2),
            "peak_write_qps": round(self.peak_write_qps, 2),
            "daily_storage_gb": round(self.daily_storage_bytes / (1024**3), 3),
            "yearly_storage_tb": round(self.yearly_storage_bytes / (1024**4), 3),
            "five_year_storage_tb": round(self.five_year_storage_bytes / (1024**4), 3),
            "network_ingress_mbps": round(self.network_ingress_mbps, 2),
            "network_egress_mbps": round(self.network_egress_mbps, 2),
        }


@dataclass(slots=True, frozen=True)
class DimensionScore:
    """Evaluation score for a single senior engineering dimension."""

    dimension_name: str
    score: int  # 1 to 5 scale
    weight: float
    notes: str = ""

    def __post_init__(self) -> None:
        if not (1 <= self.score <= 5):
            raise ValueError(f"Dimension score must be between 1 and 5, got {self.score}")
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")

    @property
    def weighted_points(self) -> float:
        """Calculate weighted score out of 100 percentage points."""
        return round((self.score / 5.0) * self.weight * 100.0, 4)


@dataclass(slots=True, frozen=True)
class EvaluationReport:
    """Aggregated evaluation across all five senior engineering dimensions."""

    scores: tuple[DimensionScore, ...]
    weighted_percentage: float
    hire_recommendation: str
    strengths: tuple[str, ...] = field(default_factory=tuple)
    growth_areas: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not (0.0 <= self.weighted_percentage <= 100.0):
            raise ValueError(f"Weighted percentage must be between 0 and 100, got {self.weighted_percentage}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "weighted_percentage": round(self.weighted_percentage, 1),
            "hire_recommendation": self.hire_recommendation,
            "dimension_scores": [
                {
                    "dimension": s.dimension_name,
                    "score": s.score,
                    "weight": s.weight,
                    "weighted_points": round(s.weighted_points, 1),
                    "notes": s.notes,
                }
                for s in self.scores
            ],
            "strengths": list(self.strengths),
            "growth_areas": list(self.growth_areas),
        }


@dataclass(slots=True, frozen=True)
class CaseStudy:
    """Canonical production case study extracted from the mastercourse."""

    name: str
    domain: str
    core_problem: str
    primary_architecture: str
    data_layer: str
    concurrency_strategy: str
    key_tradeoffs: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "core_problem": self.core_problem,
            "primary_architecture": self.primary_architecture,
            "data_layer": self.data_layer,
            "concurrency_strategy": self.concurrency_strategy,
            "key_tradeoffs": self.key_tradeoffs,
        }


# ==============================================================================
# Domain Engine Capabilities & Calculators
# ==============================================================================


class SystemDesignEngine:
    """Core domain calculator and verification engine for system design."""

    @staticmethod
    def calculate_capacity(
        dau: int,
        read_write_ratio: float = 10.0,
        reads_per_user_day: float = 50.0,
        avg_read_payload_bytes: int = 4096,
        avg_write_payload_bytes: int = 1024,
        peak_multiplier: float = 3.0,
    ) -> CapacityEstimate:
        """Compute comprehensive capacity, throughput, storage, and bandwidth estimates."""
        writes_per_user_day = reads_per_user_day / read_write_ratio

        total_daily_reads = dau * reads_per_user_day
        total_daily_writes = dau * writes_per_user_day

        seconds_per_day = 86400.0
        avg_read_qps = total_daily_reads / seconds_per_day
        peak_read_qps = avg_read_qps * peak_multiplier

        avg_write_qps = total_daily_writes / seconds_per_day
        peak_write_qps = avg_write_qps * peak_multiplier

        daily_storage_bytes = int(total_daily_writes * avg_write_payload_bytes)
        yearly_storage_bytes = int(daily_storage_bytes * 365)
        five_year_storage_bytes = int(yearly_storage_bytes * 5)

        # Network bandwidth in Mbps: (QPS * payload_bytes * 8 bits) / 1,000,000
        ingress_mbps = (avg_write_qps * avg_write_payload_bytes * 8.0) / 1_000_000.0
        egress_mbps = (avg_read_qps * avg_read_payload_bytes * 8.0) / 1_000_000.0

        return CapacityEstimate(
            dau=dau,
            read_write_ratio=read_write_ratio,
            read_requests_per_user_day=reads_per_user_day,
            write_requests_per_user_day=writes_per_user_day,
            avg_read_payload_bytes=avg_read_payload_bytes,
            avg_write_payload_bytes=avg_write_payload_bytes,
            peak_multiplier=peak_multiplier,
            avg_read_qps=avg_read_qps,
            peak_read_qps=peak_read_qps,
            avg_write_qps=avg_write_qps,
            peak_write_qps=peak_write_qps,
            daily_storage_bytes=daily_storage_bytes,
            yearly_storage_bytes=yearly_storage_bytes,
            five_year_storage_bytes=five_year_storage_bytes,
            network_ingress_mbps=ingress_mbps,
            network_egress_mbps=egress_mbps,
        )

    @staticmethod
    def evaluate_interview(
        communication: int,
        structured_thinking: int,
        technical_judgment: int,
        practical_depth: int,
        time_management: int,
        notes: dict[str, str] | None = None,
    ) -> EvaluationReport:
        """Evaluate a candidate or design session across the five senior engineering dimensions."""
        notes = notes or {}

        scores = (
            DimensionScore("Communication & Collaboration", communication, 0.20, notes.get("communication", "")),
            DimensionScore("Structured Decomposition", structured_thinking, 0.20, notes.get("structured", "")),
            DimensionScore("Technical Judgment", technical_judgment, 0.25, notes.get("technical", "")),
            DimensionScore("Practical Depth", practical_depth, 0.25, notes.get("depth", "")),
            DimensionScore("Time Management", time_management, 0.10, notes.get("pacing", "")),
        )

        total_percentage = round(sum(s.weighted_points for s in scores), 2)

        if total_percentage >= 85.0:
            recommendation = "Strong Hire (Senior/Staff Level)"
        elif total_percentage >= 70.0:
            recommendation = "Hire (Senior Level)"
        elif total_percentage >= 55.0:
            recommendation = "Leaning Hire (Mid/Senior Borderline)"
        else:
            recommendation = "No Hire"

        strengths = tuple(s.dimension_name for s in scores if s.score >= 4)
        growth_areas = tuple(s.dimension_name for s in scores if s.score <= 2)

        return EvaluationReport(
            scores=scores,
            weighted_percentage=total_percentage,
            hire_recommendation=recommendation,
            strengths=strengths,
            growth_areas=growth_areas,
        )

    @staticmethod
    def get_canonical_case_study(system_key: str) -> CaseStudy:
        """Retrieve canonical system design case study extracted from the mastercourse."""
        key = system_key.strip().lower()
        if "spotify" in key:
            return CaseStudy(
                name="Spotify (Audio Streaming Platform)",
                domain="Media Streaming & High Ingress Audio Delivery",
                core_problem="Delivering low-latency audio playback to 500M+ users with offline synchronization.",
                primary_architecture="Global Edge CDN (Cloudflare/Fastly) caching audio chunks with HTTP Range headers; S3 Blob Storage as origin; stateless API gateway.",
                data_layer="Relational PostgreSQL for catalog/metadata (artists, albums, tracks); Redis cluster for playlists, user sessions, and cache-aside query caching.",
                concurrency_strategy="CDN edge pre-buffering (first 30s) achieving > 95% cache hit ratio; asynchronous Kafka workers for audio transcoding pipelines.",
                key_tradeoffs="Eventual consistency on user play-count and playlist updates to prioritize 99.999% audio playback availability.",
            )
        elif "booking" in key or "hotel" in key or "reservation" in key:
            return CaseStudy(
                name="Booking.com (Hotel Reservation & Inventory System)",
                domain="E-Commerce & High-Contention Inventory Allocation",
                core_problem="Guaranteeing zero double-bookings during peak seasonal spikes across 1.1B annual reservations.",
                primary_architecture="CQRS architecture separating hotel search and filtering (Elasticsearch/OpenSearch) from transactional booking and inventory engines.",
                data_layer="Relational PostgreSQL with ACID transactions for inventory and booking ledger; Redis cluster for distributed locking and session caches.",
                concurrency_strategy="2-phase reservation state machine (Pending -> Reserved -> Confirmed); Redis Redlock with 10-15m TTL lease; DB optimistic locking (version column).",
                key_tradeoffs="Strict serializability / strong consistency for inventory writes at the cost of higher booking latency; CQRS eventual consistency for search results.",
            )
        elif "whatsapp" in key or "chat" in key or "messaging" in key:
            return CaseStudy(
                name="WhatsApp (Global Real-Time Messaging Platform)",
                domain="Low-Latency Persistent Bidirectional Messaging",
                core_problem="Maintaining millions of active socket connections and routing ephemeral encrypted messages with zero server content inspection.",
                primary_architecture="Stateful WebSocket / TCP connection gateway cluster; ephemeral Redis session registry routing User IDs to Gateway Nodes; push notifications fallback.",
                data_layer="Transient Cassandra / ScyllaDB mailbox store with automatic message purging upon recipient delivery ACK; PostgreSQL for user accounts and group memberships.",
                concurrency_strategy="Client-side message fanout for small groups and server-assisted fanout for large groups; heartbeat leases pruning dead socket connections.",
                key_tradeoffs="Zero server-side message persistence once delivered; Signal Protocol double-ratchet E2EE where keys reside exclusively on client endpoints.",
            )
        else:
            raise KeyError(f"Unknown case study '{system_key}'. Available: 'spotify', 'booking.com', 'whatsapp'")


# ==============================================================================
# CLI Entrypoint (Headless Seam)
# ==============================================================================


def main() -> None:
    """CLI dispatcher for system design calculations, evaluations, and case studies."""
    parser = argparse.ArgumentParser(description="System Design Architect Domain Engine")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: estimate
    estimate_parser = subparsers.add_parser("estimate", help="Calculate capacity, throughput, and storage metrics")
    estimate_parser.add_argument("--dau", type=int, required=True, help="Daily Active Users")
    estimate_parser.add_argument("--ratio", type=float, default=10.0, help="Read-to-Write ratio (default: 10.0)")
    estimate_parser.add_argument("--reads-per-user", type=float, default=50.0, help="Average reads per user day")
    estimate_parser.add_argument("--read-bytes", type=int, default=4096, help="Average read payload bytes")
    estimate_parser.add_argument("--write-bytes", type=int, default=1024, help="Average write payload bytes")
    estimate_parser.add_argument("--peak-multiplier", type=float, default=3.0, help="Peak traffic multiplier")

    # Subcommand: score
    score_parser = subparsers.add_parser("score", help="Score a system design interview across 5 dimensions (1-5)")
    score_parser.add_argument("--communication", type=int, required=True, help="Communication & Collaboration score")
    score_parser.add_argument("--structured", type=int, required=True, help="Structured Decomposition score")
    score_parser.add_argument("--technical", type=int, required=True, help="Technical Judgment score")
    score_parser.add_argument("--depth", type=int, required=True, help="Practical Depth score")
    score_parser.add_argument("--pacing", type=int, required=True, help="Time Management & Pacing score")

    # Subcommand: case-study
    case_parser = subparsers.add_parser("case-study", help="Retrieve canonical case study details")
    case_parser.add_argument("--system", type=str, required=True, choices=["spotify", "booking.com", "whatsapp"])

    args = parser.parse_args()

    if args.subcommand == "estimate":
        est = SystemDesignEngine.calculate_capacity(
            dau=args.dau,
            read_write_ratio=args.ratio,
            reads_per_user_day=args.reads_per_user,
            avg_read_payload_bytes=args.read_bytes,
            avg_write_payload_bytes=args.write_bytes,
            peak_multiplier=args.peak_multiplier,
        )
        print(json.dumps(est.to_dict(), indent=2))

    elif args.subcommand == "score":
        report = SystemDesignEngine.evaluate_interview(
            communication=args.communication,
            structured_thinking=args.structured,
            technical_judgment=args.technical,
            practical_depth=args.depth,
            time_management=args.pacing,
        )
        print(json.dumps(report.to_dict(), indent=2))

    elif args.subcommand == "case-study":
        cs = SystemDesignEngine.get_canonical_case_study(args.system)
        print(json.dumps(cs.to_dict(), indent=2))


if __name__ == "__main__":
    main()
