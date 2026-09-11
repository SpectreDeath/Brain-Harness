# Reference: Google Mantis Plugin Suite API & Tool Contracts

Technical specification of service keys, tool signatures, parameter schemas, and return structures.

---

## 1. Service Key Registry

| Service Key | Target Interface | Providing Plugin | Isolation Mode |
| :--- | :--- | :--- | :--- |
| `service.mantis_security_review` | `MantisSecurityReviewService` | `plugin.mantis_security_review` | `in_process` |
| `service.mantis_sandbox_verifier` | `MantisSandboxVerifierService` | `plugin.mantis_sandbox_verifier` | `subprocess` |
| `service.mantis_structural_index` | `MantisStructuralIndexService` | `plugin.mantis_structural_index` | `in_process` |

---

## 2. Tool Reference: `plugin.mantis_security_review`

### `mantis_history_scan`
- **Description:** Mines Git repository history for commits with vulnerability or security fix keywords.
- **Parameters:**
  - `repo_path` (`string`, required): Path to local Git repository.
  - `max_commits` (`integer`, optional, default `100`): Maximum commits to scan.
  - `pattern_filter` (`string`, optional, default `""`): Keyword or regex pattern.
- **Return Type:**
  ```json
  {
    "status": "ok",
    "repo_path": "string",
    "total_commits_scanned": 100,
    "security_commits_found": 5,
    "historical_learnings": [
      {
        "hash": "commit_hash",
        "author": "author_name",
        "date": "YYYY-MM-DD",
        "subject": "commit_message",
        "matched_keywords": ["fix", "vuln"]
      }
    ]
  }
  ```

### `mantis_directory_summary`
- **Description:** Generates a structured directory summary with code, config, and documentation breakdowns.
- **Parameters:**
  - `dir_path` (`string`, required): Root directory to inspect.
  - `recursive` (`boolean`, optional, default `true`): Whether to crawl subdirectories.
- **Return Type:**
  ```json
  {
    "status": "ok",
    "root_directory": "string",
    "code_files_count": 42,
    "config_files_count": 8,
    "doc_files_count": 4,
    "total_estimated_lines": 5200,
    "code_files": ["..."],
    "config_files": ["..."]
  }
  ```

### `mantis_plan_review`
- **Description:** Formulates a targeted defensive review roadmap from threat boundaries.
- **Parameters:**
  - `threat_model` (`object`, required): Threat model dictionary.
  - `target_paths` (`array` of strings, required): List of candidate paths.
  - `focus_cwe` (`array` of strings, optional, default `[]`): Priority CWE identifiers.

### `mantis_dedupe_ladder`
- **Description:** Deduplicates findings using syntactic, AST symbol, and stable signature rungs.
- **Parameters:**
  - `findings` (`array` of objects, required): Raw finding dictionaries.
  - `mode` (`string`, optional, default `"syntactic_and_ast"`): Deduplication mode.

### `mantis_review_gate`
- **Description:** Independent semantic verification of findings against actual code context.
- **Parameters:**
  - `finding` (`object`, required): Finding dictionary.
  - `source_content` (`string`, required): Full source text.
  - `strictness` (`string`, optional, default `"high"`): Validation rigor (`high`, `medium`, `low`).

### `mantis_critic_filter`
- **Description:** Production viability gate eliminating assertion traps and debug-only findings.
- **Parameters:**
  - `finding` (`object`, required): Finding dictionary.
  - `check_release_assertions` (`boolean`, optional, default `true`).

### `mantis_chain_exploits`
- **Description:** Identifies combinations of findings that construct multi-stage exploit paths.
- **Parameters:**
  - `findings` (`array` of objects, required).
  - `target_objective` (`string`, optional, default `""`).

### `mantis_calibrate_risk`
- **Description:** Calibrates CVSS scores based on environment and asset criticality.
- **Parameters:**
  - `findings` (`array` of objects, required).
  - `asset_criticality` (`string`, optional, default `"high"`): `critical`, `high`, `medium`, `low`.

---

## 3. Tool Reference: `plugin.mantis_sandbox_verifier`

### `mantis_sandbox_exec`
- **Description:** Runs commands inside isolated child processes with Rule 14 pipe disposal guarantees.
- **Parameters:**
  - `command` (`string`, required): Shell or executable command.
  - `timeout_seconds` (`integer`, optional, default `120`).
  - `env_vars` (`object`, optional, default `{}`).

### `mantis_reproduce_crash`
- **Description:** Executes PoC crash reproducer scripts in shadow sandbox directories with ASAN/UBSAN monitoring.
- **Parameters:**
  - `reproducer_script` (`string`, required): Python/shell script.
  - `target_file` (`string`, required): Audited file.
  - `sanitizers` (`array` of strings, optional, default `["asan"]`).

### `mantis_patch_verify`
- **Description:** Applies candidate patch diff in shadow isolation and validates against reproducer and re-attacks.
- **Parameters:**
  - `diff_content` (`string`, required): Candidate patch diff.
  - `reproducer_script` (`string`, required): Baseline crash script.
  - `run_bypass_reattack` (`boolean`, optional, default `true`).

---

## 4. Tool Reference: `plugin.mantis_structural_index`

### `mantis_build_structural_index`
- **Description:** Crawls repository, parses ASTs, and caches content-addressed units into SQLite.
- **Parameters:**
  - `repo_path` (`string`, required).
  - `db_path` (`string`, optional, default `"structural_index.db"`).

### `mantis_query_symbol`
- **Description:** Queries definition, callers, signatures, and AST hashes from SQLite index.
- **Parameters:**
  - `symbol_name` (`string`, required).
  - `db_path` (`string`, optional, default `"structural_index.db"`).
  - `query_type` (`string`, optional, default `"definition"`): `definition`, `references`, `all`.
