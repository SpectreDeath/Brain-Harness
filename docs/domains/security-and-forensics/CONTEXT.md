# Security & Forensics Context

The Security & Forensics context governs threat modeling, vulnerability detection, structured log pattern extraction, port auditing, and execution trajectory verification.

## Language

**Threat Modeler**:
A structured risk assessment pipeline that enumerates system attack surfaces and formulates defensive mitigation trees using STRIDE.
_Avoid_: Risk analyzer, security checker

**Security Scanner**:
An automated audit tool that scans codebases for hardcoded credentials, known dependency vulnerabilities, and unsafe syscalls.
_Avoid_: Vulnerability finder, secret detector

**Trajectory Auditor**:
An epistemic verification engine that replays agent execution steps to assert that no safety invariants or file boundaries were violated.
_Avoid_: Action logger, history checker, trace viewer

**Log Forensics**:
A pattern extraction parser that isolates anomalies, stack traces, and failure cascades across high-volume log streams.
_Avoid_: Log searcher, grep tool
