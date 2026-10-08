"""Interactive HTML visual brief generator for network forensics."""

from __future__ import annotations

import tempfile
from pathlib import Path


def generate_visual_brief(output_path: str | None = None) -> str:
    """Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%."""
    if output_path is None:
        temp_dir = Path(tempfile.gettempdir())
        out_file = temp_dir / "network-forensics-visual-brief.html"
    else:
        out_file = Path(output_path)

    html_content = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Forensics & Diagnostics Visual Brief</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#0B0F17',
                        cardbg: '#111827',
                        accentcyan: '#06B6D4',
                        accentemerald: '#10B981',
                        accentamber: '#F59E0B',
                        accentrose: '#F43F5E'
                    }
                }
            }
        };
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose'
        });
    </script>
    <style>
        body { background-color: #0B0F17; color: #E2E8F0; }
        .mermaid svg { max-width: 100%; height: auto; margin: 0 auto; }
    </style>
</head>
<body class="min-h-screen px-4 py-8 md:px-12 font-sans">
    <div class="max-w-6xl mx-auto space-y-8">
        <header class="border-b border-gray-800 pb-6">
            <span class="px-3 py-1 text-xs font-semibold bg-cyan-950 text-cyan-400 border border-cyan-800 rounded-full">
                Interactive Diagnostics Brief
            </span>
            <h1 class="text-3xl font-extrabold text-white mt-3">Network Forensics & Protocol Inspection</h1>
            <p class="text-gray-400 text-sm">Automated protocol telemetry, tri-state recon, and 7-layer fault isolation.</p>
        </header>

        <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-3">
                <h2 class="text-lg font-bold text-cyan-400">Tri-State Port Reachability</h2>
                <div class="bg-gray-950 p-4 rounded-lg border border-gray-800 text-xs">
                    <pre class="mermaid">
stateDiagram-v2
    [*] --> ProbeEmit : Send TCP SYN Probe
    ProbeEmit --> Open : SYN/ACK Received
    ProbeEmit --> Closed : RST/ACK Received
    ProbeEmit --> Filtered : Drop / Timeout / ICMP Unreachable
    Open --> ActiveService : Handshake Finalized
    Closed --> UnallocatedPort : Target Active, Socket Unbound
    Filtered --> MiddleboxBlock : Stateful Firewall / IDS Drop
                    </pre>
                </div>
            </div>

            <div class="bg-gray-900/60 border border-gray-800 rounded-xl p-5 space-y-3">
                <h2 class="text-lg font-bold text-emerald-400">7-Layer OSI Fault Tree</h2>
                <div class="bg-gray-950 p-4 rounded-lg border border-gray-800 text-xs">
                    <pre class="mermaid">
flowchart TD
    L1[Layer 1: Physical Link] -->|Pass| L2[Layer 2: ARP Resolution]
    L1 -->|Fail| R1[Reconnect Cable / Adapter]
    L2 -->|Pass| L3[Layer 3: IP Route & Gateway]
    L2 -->|Fail| R2[Clear ARP / Check VLAN]
    L3 -->|Pass| L4[Layer 4: TCP Port Socket]
    L3 -->|Fail| R3[Check Subnet Route / Default GW]
    L4 -->|Pass| L7[Layer 7: Application / DNS]
    L4 -->|Fail| R4[Check Firewall / Service Listener]
    L7 -->|Pass| Verified[End-to-End Connectivity]
    L7 -->|Fail| R7[Inspect DNS / App Server Logs]
                    </pre>
                </div>
            </div>
        </section>

        <footer class="border-t border-gray-800 pt-4 text-xs text-gray-500">
            Brain Harness &bull; Network Forensics Engine
        </footer>
    </div>
</body>
</html>"""

    out_file.write_text(html_content, encoding="utf-8")
    return str(out_file.resolve())
