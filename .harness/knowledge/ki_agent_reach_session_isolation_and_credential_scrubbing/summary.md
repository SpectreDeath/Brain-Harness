# Private HOME Sandboxing, Symlink Defense & Automated URL Credential Redaction

## Context & Theoretical Grounding
CLI tools often dump sensitive session cookies, auth tokens, and plaintext passwords directly into `$HOME`. Running untrusted scrapers risks exposing host credentials and polluting the global environment.

## Distilled Mental Models & Heuristics
1. **Per-Tool HOME Redirection**:
   - When executing external tools, `sessions.session_env(tool)` redirects `HOME`, `USERPROFILE`, and `APPDATA` to `~/.agent-reach/sessions/<tool>/`.
   - Tool logins never touch the host user's actual home directory.
2. **Symlink Boundary Enforcement**:
   - `ensure_no_symlink_path()` verifies that paths within session directories are not symlinks pointing to sensitive host directories (`/etc/passwd`, `~/.ssh`).
3. **Automated URL Credential Redaction**:
   - `scrub_url_credentials()` strips inline HTTP basic authentication (`user:pass@host`) from all returned metadata, URLs, and error diagnostics before serializing into the agent result envelope.

## Anti-Pattern Defenses
- **Global Home Directory Contamination**: Letting external scraping CLIs write authentication state to the default user home directory.
- **Credential Leakage in LLM Transcripts**: Leaving plaintext passwords or tokens in query URLs logged in the agent's context window.
