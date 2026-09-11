# Explanation: Deep Learning File Identification & Sandbox Isolation

Architectural background and design decisions behind the Google Magika integration.

---

## Why Deep Learning Instead of Magic Bytes?

Traditional file type identification has relied on the Unix `file` command and `libmagic` rules for decades. These tools check for specific magic numbers (fixed byte sequences) at known offsets.

However, magic numbers suffer from severe systemic limitations:
1. **Heuristic Collisions:** Text formats (JSON, CSV, Markdown, YAML, Shell) frequently lack unique headers and collide with generic ASCII/UTF-8 rules.
2. **Fragile Rule Complexity:** The `file` database contains thousands of lines of handwritten C-like rules, creating security vulnerabilities (e.g. CVE-2014-9620, CVE-2019-18218).
3. **Spoofing Vulnerability:** Attackers can easily prepend a legitimate JPEG or PNG header (`ÿØÿà`) to an executable script or payload, deceiving standard file filters.

### Magika's Machine Learning Architecture

Google Magika solves this by training a compact custom CNN/MLP neural network. The model:
- Takes 3 fixed-size slices of the file: the **header** (first 512 bytes), **center** (512 bytes), and **footer** (last 512 bytes).
- Feeds these byte sequences through embedding layers, convolutional feature extractors, and dense classification layers.
- Outputs probabilities across 216 content types.
- Weighs only 3.16 MB in ONNX format and executes in ~5ms on standard CPU architectures without requiring GPU hardware.

---

## Subprocess Sandbox Isolation (Rule 5 & Rule 14)

Untrusted user files and third-party binaries should never be executed or parsed unsafely in the main agent process. 

Even though Magika's model is pure inference, running it within a subprocess sandbox ensures:
1. **Memory Isolation:** Any segmentation faults or native ONNX runtime exceptions in C++ libraries cannot terminate the Brain Harness kernel.
2. **Proactor Resource Safety:** All async transports drain and dispose of standard I/O pipes inside `finally` blocks, preventing Windows handle leaks.
3. **Lazy Staging (Rule 7):** Subprocess runners remain validated without cold-start timeouts.

---

## Domain Partitioning Strategy (Rule 18)

Rather than dumping all detection, forensics, and quarantine functions into one monolithic plugin, Magika is cleanly bifurcated:
- `magika_content_detector`: Focuses purely on content type inference and metadata retrieval.
- `magika_format_forensics`: Focuses on defensive analysis, risk scoring, and policy enforcement.

This separation of concerns prevents bloated interfaces and allows upstream agent loops to depend only on the specific capability they need.
