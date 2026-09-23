#!/usr/bin/env python3
"""network_diagnostics.py - Standalone skill runner and dispatcher for ethical-hacker-networking.

Bifurcates standalone execution from full kernel bootstrapping by delegating
directly to the slotted NetworkForensicsEngine (Rule 49).
Configures UTF-8 standard streams on Windows (Rule 23, Rule 50).
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Rule 50: Prepend workspace root and src/ to sys.path
_ws_root = Path(__file__).resolve().parents[4]
_src_dir = _ws_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if str(_ws_root) not in sys.path:
    sys.path.insert(0, str(_ws_root))

from plugins.security_and_forensics.network_forensics.engine import (
    NetworkForensicsEngine,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for standalone diagnostics."""
    parser = argparse.ArgumentParser(
        description="Ethical Hacker Networking — Standalone Protocol Diagnostics & Recon"
    )
    parser.add_argument(
        "--traceroute",
        type=str,
        help="Path to traceroute output file or raw text to parse",
    )
    parser.add_argument(
        "--decode-flags",
        type=str,
        help="Hexadecimal TCP flags to decode (e.g. 0x02, 0x29)",
    )
    parser.add_argument(
        "--subnet",
        type=str,
        help="IPv4 CIDR prefix to calculate geometry for (e.g. 192.168.1.0/24)",
    )
    parser.add_argument(
        "--diagnose-7layer",
        type=str,
        help="Target host or IP to run 7-layer fault isolation chain against",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=80,
        help="Target port for 7-layer diagnostics (default: 80)",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Generate interactive HTML visual brief in %TEMP%",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON results",
    )
    return parser


def main() -> None:
    """Execute standalone diagnostic workflows."""
    parser = build_parser()
    args = parser.parse_args()

    engine = NetworkForensicsEngine()
    executed = False

    if args.traceroute:
        executed = True
        path = Path(args.traceroute)
        raw_text = (
            path.read_text(encoding="utf-8") if path.is_file() else args.traceroute
        )
        report = engine.analyze_traceroute_hops(raw_text)
        if args.json:
            print(json.dumps(report.model_dump(), indent=2))
        else:
            print(
                f"Traceroute Target: {report.target} | Total Hops: {report.total_hops}"
            )
            for h in report.hops:
                print(
                    f"  Hop {h.hop_number:2d}: {h.ip_address:20s} {h.rtt_ms:6.1f} ms [{h.status}]"
                )

    if args.decode_flags:
        executed = True
        flag_report = engine.decode_tcp_flags(args.decode_flags)
        if args.json:
            print(json.dumps(flag_report.model_dump(), indent=2))
        else:
            print(
                f"TCP Flags ({args.decode_flags}): {', '.join(flag_report.flags_set) or 'NONE'}"
            )
            if flag_report.anomalous:
                print(f"  [!] Anomalous Evasion: {flag_report.evasion_type}")

    if args.subnet:
        executed = True
        sub_report = engine.calculate_subnet_geometry(args.subnet)
        if args.json:
            print(json.dumps(sub_report.model_dump(), indent=2))
        else:
            print(f"Subnet Geometry ({args.subnet}):")
            print(
                f"  Netmask: {sub_report.netmask} | Usable Hosts: {sub_report.usable_hosts}"
            )
            print(f"  Usable Range: {sub_report.usable_host_range}")

    if args.diagnose_7layer:
        executed = True
        diag_report = engine.run_7layer_diagnostic_chain(
            args.diagnose_7layer, port=args.port
        )
        if args.json:
            print(json.dumps(diag_report.model_dump(), indent=2))
        else:
            print(f"7-Layer Diagnostic: {args.diagnose_7layer}:{args.port}")
            for r in diag_report.results:
                badge = "[PASS]" if r.passed else "[FAIL]"
                print(f"  Layer {r.layer} ({r.layer_name}): {badge} {r.details}")
            if diag_report.earliest_failing_layer:
                print(
                    f"  Root Cause: Layer {diag_report.earliest_failing_layer} Failure"
                )

    if args.brief:
        executed = True
        out_path = engine.generate_visual_brief()
        print(f"Visual Brief generated: {out_path}")

    if not executed:
        parser.print_help()


if __name__ == "__main__":
    main()
