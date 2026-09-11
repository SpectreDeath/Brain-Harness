# How-To: Practical Security & Forensics Recipes for Magika

Task-oriented guides for solving concrete problems with the Magika plugins.

---

## Recipe 1: Batch Classify a Directory and Generate Content Breakdown

Use `magika_batch_scan` to index and summarize all file groups across a workspace:

```python
from plugins.security_and_forensics.magika_content_detector.main import magika_batch_scan

summary = magika_batch_scan("workspace/downloads", recursive=True, max_files=1000)
print(f"Total scanned: {summary['scanned_count']}")
for group, count in summary["group_counts"].items():
    print(f"  {group}: {count} files")
```

---

## Recipe 2: Gate Untrusted Uploads with Quarantine Scan

Prevent users or external agents from uploading dangerous executables, shell scripts, or archives into a documentation or media folder:

```python
from plugins.security_and_forensics.magika_format_forensics.main import magika_quarantine_scan

scan = magika_quarantine_scan(
    "uploads/user_resume.docx",
    blocked_groups=["executable", "code", "archive"]
)

if scan["quarantined"]:
    raise ValueError(f"Upload rejected: {scan['violation_reason']}")
```

---

## Recipe 3: Detect Polyglot Files and Hidden Appended ZIPs

Check if a file exhibits dual-format signatures, such as a JPEG with an appended ZIP payload:

```python
from plugins.security_and_forensics.magika_format_forensics.main import magika_polyglot_check

polyglot = magika_polyglot_check("suspicious_image.png", threshold=0.70)
if polyglot["is_polyglot_candidate"]:
    print(f"Polyglot warning on {polyglot['file_path']}:")
    for indicator in polyglot["indicators"]:
        print(f" - {indicator}")
```
