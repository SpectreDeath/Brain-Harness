# Google Magika Content Detector Plugin

`plugin.magika_content_detector` integrates Google Magika's deep learning file content type and MIME identification system into Brain Harness.

## Features
- **3.16 MB ONNX Model:** Evaluates file header, body, and footer chunks with custom CNN/MLP inference.
- **216 Model Output Classes & 353 KB Types:** Differentiates programming languages, configuration files, binary executables, and media.
- **Zero-Disk In-Memory Bytes Inspection:** Classifies base64 byte streams directly without temporary disk artifacts.
- **Batch Directory Profiling:** Generates hierarchical distributions across content groups (`code`, `document`, `executable`, `archive`, `media`).

## Exported Tools
- `magika_identify_path`: Classify file by path.
- `magika_identify_bytes`: Classify in-memory base64 bytes.
- `magika_batch_scan`: Classify directory hierarchy with group aggregations.
- `magika_list_content_types`: Query supported content types.
- `magika_get_model_info`: Return active model metadata.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `magika_identify_path` | `(path, prediction_mode)` | Identify file content type, MIME, group, confidence score, and text/binary flag from a file path |
| `magika_identify_bytes` | `(content_b64, prediction_mode)` | Identify content type and MIME metadata from in-memory base64-encoded bytes without disk writes |
| `magika_batch_scan` | `(dir_path, recursive, max_files)` | Scan and classify all files in a directory hierarchy with aggregated group statistics and confidence scoring |
| `magika_list_content_types` | `(filter_group)` | Query supported output labels, MIME types, and groups from the Magika knowledge base |
| `magika_get_model_info` | `()` | Retrieve metadata about the active Magika ONNX model, output dimension, and runtime features |
