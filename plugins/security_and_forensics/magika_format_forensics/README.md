# Google Magika Format Forensics Plugin

`plugin.magika_format_forensics` provides advanced security verification, extension mismatch auditing, polyglot detection, and upload quarantine gating.

## Features
- **Extension Spoofing Detection:** Identifies malicious files masquerading as harmless formats (e.g. ELF/PE binary disguised with `.png` or `.pdf` extension).
- **Polyglot File Analysis:** Discovers dual-format constructs, embedded ZIP archives in image footers, and low-confidence prediction anomalies.
- **Upload Quarantine Gating:** Evaluates untrusted artifacts against an allowlist/denylist policy to block dangerous groups (`executable`, `code`, `archive`).

## Exported Tools
- `magika_audit_extension_mismatch`: Detect extension spoofing across files or directories.
- `magika_polyglot_check`: Inspect files for polyglot markers and anomalous confidence scores.
- `magika_quarantine_scan`: Evaluate files against quarantine rules.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `magika_audit_extension_mismatch` | `(target_path, recursive)` | Scan files to detect extension spoofing where the deep learning content type contradicts the file extension |
| `magika_polyglot_check` | `(file_path, threshold)` | Inspect a file for low prediction margins, ambiguous classifications, or composite headers characteristic of polyglots |
| `magika_quarantine_scan` | `(file_path, blocked_groups)` | Evaluate a file against an untrusted upload policy, quarantining files belonging to prohibited content groups |
