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
