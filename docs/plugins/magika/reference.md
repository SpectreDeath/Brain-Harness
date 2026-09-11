# Reference: Magika Service Keys, Tool Schemas & Return Types

Technical reference specifications for all Magika tools and service contracts.

---

## Service Keys

| ServiceKey | Type | Provider Plugin | Required Dependencies |
| :--- | :--- | :--- | :--- |
| `service.magika_content_detector` | `MagikaContentDetectorService` | `plugin.magika_content_detector` | None |
| `service.magika_format_forensics` | `MagikaFormatForensicsService` | `plugin.magika_format_forensics` | `service.magika_content_detector` |

---

## Tool Specifications: `plugin.magika_content_detector`

### `magika_identify_path`
- **Parameters:**
  - `path` (`string`, required): File path to classify.
  - `prediction_mode` (`string`, optional): Confidence mode (`high_confidence`, `medium_confidence`, `best_effort`). Default: `high_confidence`.
- **Returns (`dict`):**
  - `status`: `"ok"` or `"error"`
  - `path`: Normalized path string
  - `label`: Predicted content type label (e.g. `python`, `json`, `pdf`, `elf`)
  - `mime_type`: Standard MIME type (e.g. `text/x-python`, `application/json`)
  - `group`: Content group category (`code`, `document`, `executable`, `archive`, `media`, `inode`)
  - `description`: Human-readable description
  - `extensions`: List of canonical filename extensions
  - `score`: Model confidence probability (`0.0` to `1.0`)
  - `is_text`: Boolean indicating textual vs binary content
  - `overwrite_reason`: Rule applied over raw ONNX prediction (`none`, `empty`, etc.)

### `magika_identify_bytes`
- **Parameters:**
  - `content_b64` (`string`, required): Base64-encoded byte content.
  - `prediction_mode` (`string`, optional): Confidence mode. Default: `high_confidence`.
- **Returns (`dict`):**
  - Same schema as `magika_identify_path` (excluding `path`).

### `magika_batch_scan`
- **Parameters:**
  - `dir_path` (`string`, required): Target directory.
  - `recursive` (`boolean`, optional): Recurse into subdirectories. Default: `true`.
  - `max_files` (`integer`, optional): Max files limit. Default: `500`.
- **Returns (`dict`):**
  - `status`: `"ok"`
  - `directory`: Scanned directory
  - `scanned_count`: Number of files evaluated
  - `group_counts`: Mapping of group names to file counts
  - `files`: List of individual file summary objects

### `magika_list_content_types`
- **Parameters:**
  - `filter_group` (`string`, optional): Filter by group name (`code`, `document`, etc.).
- **Returns (`dict`):**
  - `status`: `"ok"`
  - `total_count`: Integer count
  - `content_types`: Array of content type definition objects

### `magika_get_model_info`
- **Parameters:** None
- **Returns (`dict`):**
  - `model_name`: Active model identifier (`standard_v3_3`)
  - `version`: Module version
  - `output_types_count`: Total output classes (216)
  - `onnx_available`: Boolean indicating ONNX runtime status

---

## Tool Specifications: `plugin.magika_format_forensics`

### `magika_audit_extension_mismatch`
- **Parameters:**
  - `target_path` (`string`, required): File or directory path.
  - `recursive` (`boolean`, optional): Recurse if directory. Default: `true`.
- **Returns (`dict`):**
  - `audited_count`: Total files checked
  - `mismatches_count`: Discrepancies detected
  - `mismatches`: List of mismatch records with `risk_level` (`critical`, `medium`, `low`)

### `magika_polyglot_check`
- **Parameters:**
  - `file_path` (`string`, required): Path to file.
  - `threshold` (`number`, optional): Confidence threshold. Default: `0.70`.
- **Returns (`dict`):**
  - `is_polyglot_candidate`: Boolean flag
  - `indicators_count`: Number of suspicious characteristics detected
  - `indicators`: List of alert strings

### `magika_quarantine_scan`
- **Parameters:**
  - `file_path` (`string`, required): Path to file.
  - `blocked_groups` (`array[string]`, optional): Prohibited content groups. Default: `["executable", "code"]`.
- **Returns (`dict`):**
  - `quarantined`: Boolean flag
  - `detected_group`: String group name
  - `violation_reason`: Descriptive explanation
