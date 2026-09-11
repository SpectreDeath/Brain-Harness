# Tutorial: Getting Started with Google Magika in Brain Harness

This tutorial guides you through configuring and using the Google Magika file content detection and format forensics plugins in Brain Harness.

---

## 1. Introduction

Google Magika uses a compact, highly-optimized deep learning model (custom CNN/MLP in ONNX format, ~3.16 MB) to identify the content type and MIME type of files. Unlike traditional tools like `file` or `libmagic` that rely on static byte patterns (magic numbers), Magika evaluates byte distribution across file headers, content bodies, and footers.

In Brain Harness, Magika is exposed as two domain-partitioned plugins:
- `plugin.magika_content_detector`: Core deep-learning MIME and content type detection engine.
- `plugin.magika_format_forensics`: Extension spoofing auditing, polyglot candidate detection, and upload quarantine gating.

---

## 2. Resolving the Service in Code

In a ReAct agent step or service component, resolve the typed service key:

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.magika_content_detector.main import (
    MAGIKA_CONTENT_DETECTOR_KEY,
    MagikaContentDetectorService,
)

async def run_inspection(ctx: ServiceContext, file_path: str):
    # Resolve typed service key (Rule 2)
    detector: MagikaContentDetectorService = ctx.require(MAGIKA_CONTENT_DETECTOR_KEY)

    # Run deep learning identification
    result = detector.identify_path(file_path, prediction_mode="high_confidence")

    print(f"Detected Label: {result['label']}")
    print(f"MIME Type:      {result['mime_type']}")
    print(f"Content Group:  {result['group']}")
    print(f"Confidence:     {result['score']:.2%}")
```

---

## 3. Running an In-Memory Bytes Inspection

When handling untrusted data streams, base64 payloads, or clipboard text, Magika analyzes raw in-memory bytes without writing temporary files to disk:

```python
import base64

raw_content = b'{"status": "ok", "agent_id": "debater_01"}'
b64_data = base64.b64encode(raw_content).decode("ascii")

result = detector.identify_bytes(b64_data)
# result['label'] -> 'json'
# result['is_text'] -> True
```

---

## 4. Auditing for Extension Spoofing

Detect files whose true content contradicts their extension (e.g. an executable disguised as an image):

```python
from plugins.security_and_forensics.magika_format_forensics.main import (
    MAGIKA_FORMAT_FORENSICS_KEY,
    MagikaFormatForensicsService,
)

async def check_uploads(ctx: ServiceContext, upload_dir: str):
    forensics: MagikaFormatForensicsService = ctx.require(MAGIKA_FORMAT_FORENSICS_KEY)
    audit = forensics.audit_extension_mismatch(upload_dir, recursive=True)

    if audit["mismatches_count"] > 0:
        for mismatch in audit["mismatches"]:
            print(f"ALERT: {mismatch['file_path']} has extension .{mismatch['file_extension']} but is actually {mismatch['detected_label']} (Risk: {mismatch['risk_level']})")
```
