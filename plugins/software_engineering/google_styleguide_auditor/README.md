# Google Style Guide Auditor Plugin

Audits code style against Google standards.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `styleguide_audit_file` | `(file_path, language)` | Audit a source code file against Google style rules (Python, C++, TypeScript, Java, Shell) |
| `styleguide_get_rule` | `(language, topic)` | Query specific Google style guidelines and best-practice rationales by language and topic |
| `styleguide_generate_linter_config` | `(tool_name, target_dir)` | Emit Google-compliant configuration files (.pylintrc, .clang-format, or style settings) |
