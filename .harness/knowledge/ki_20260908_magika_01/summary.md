# Knowledge Item: Google Magika Deep Learning Content Type & MIME Detection

## Summary
Google Magika (cloned from `D:\GitHub\cloned\Google\magika` @ commit `b20121e`) introduces a modern, deep-learning based approach to file content type identification, overcoming the fragility and security flaws of legacy `libmagic` pattern tables.

## Core Invariants & Patterns Bridged into Brain Harness

### 1. Three-Point Sampling & Compact ONNX Architecture
Magika samples 512 bytes from the header, center, and footer of a file. This bounds memory consumption to ~1.5 KB per file while extracting both format prelude tokens (e.g. `<!DOCTYPE html>`, `ELF`, `PK`) and archive trailer tables (e.g. ZIP central directories, PDF `%%EOF`).

### 2. Multi-Tiered Confidence Thresholding
Predictions are filtered through three operational confidence tiers:
- `HIGH_CONFIDENCE`: Zero-tolerance for false positives; falls back to generic text/binary if uncertain.
- `MEDIUM_CONFIDENCE`: Balanced threshold suitable for general triage.
- `BEST_EFFORT`: Always returns the top-1 neural network logit.

### 3. Forensic Defense & Polyglot Detection
By comparing the deep learning label with filename extensions, Brain Harness can immediately isolate:
- Executable files masquerading with innocent extensions (`.jpg`, `.pdf`, `.docx`).
- Polyglot containers with appended ZIP payloads.
- Script injections into media containers.

### 4. Canonical Seam Verification
- `service.magika_content_detector`: Core detection engine registered into IoC.
- `service.magika_format_forensics`: Advanced security and quarantine verification.
