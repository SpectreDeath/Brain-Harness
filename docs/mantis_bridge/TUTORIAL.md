# Tutorial: Zero to Sandboxed Crash Verification with Mantis

Welcome to the Google Mantis security review tutorial for Brain Harness. In this hands-on guide, you will attach a repository, run an automated security sweep, deduplicate raw findings, execute a sandboxed crash reproducer, and verify a candidate patch.

---

## 1. Prerequisites
Ensure you have Python 3.10+ and Git available in your environment. The Mantis plugins are registered in the Brain Harness IoC container:
- `service.mantis_security_review`
- `service.mantis_sandbox_verifier`
- `service.mantis_structural_index`

---

## 2. Step 1: Scan Historical Security Commits
Before auditing live code, discover how past vulnerabilities were introduced and patched:

```python
from plugins.security_and_forensics.mantis_security_review.main import mantis_history_scan

# Mine up to 50 commits for vulnerability patterns
history = mantis_history_scan(
    repo_path=".",
    max_commits=50,
    pattern_filter="fix"
)
print(f"Discovered {history['security_commits_found']} past security fixes.")
```

---

## 3. Step 2: Formulate a Targeted Review Plan
Combine your threat model and directory map to prioritize high-risk code paths:

```python
from plugins.security_and_forensics.mantis_security_review.main import mantis_plan_review

plan = mantis_plan_review(
    threat_model={"trust_boundary": "public_api", "auth_required": False},
    target_paths=["src/api/auth.py", "src/services/executor.py"],
    focus_cwe=["CWE-78", "CWE-89", "CWE-95"]
)
print(f"Generated review plan with ID: {plan['plan_id']}")
```

---

## 4. Step 3: Run Static Code Audit & Deduplication Ladder
Perform static AST analysis on the target file and eliminate duplicate or overlapping reports:

```python
from plugins.security_and_forensics.mantis_security_review.main import (
    mantis_research_audit,
    mantis_dedupe_ladder,
)

sample_code = '''
def handle_request(user_input):
    import os
    os.system("echo " + user_input)  # Vulnerable to command injection
'''

# 1. Audit code
audit = mantis_research_audit(target_file="app.py", code_content=sample_code)

# 2. Deduplicate findings
deduped = mantis_dedupe_ladder(findings=audit["findings"], mode="syntactic_and_ast")
print(f"Identified {deduped['deduped_count']} unique finding(s).")
```

---

## 5. Step 4: Execute a Crash Reproducer in Sandbox Isolation
Verify the finding empirically by running a Proof-of-Concept script inside an isolated sandbox:

```python
from plugins.security_and_forensics.mantis_sandbox_verifier.main import mantis_reproduce_crash

reproducer_code = '''
import sys
# Trigger intentional failure/crash
raise RuntimeError("Command injection payload triggered!")
'''

result = mantis_reproduce_crash(
    reproducer_script=reproducer_code,
    target_file="app.py",
    sanitizers=["asan"]
)
print(f"Crash reproduction status: {result['verdict']}")
```

---

## 6. Step 5: Verify Candidate Patch & Re-Attack
Apply a candidate fix diff inside a temporary shadow sandbox to guarantee the exploit is neutralized:

```python
from plugins.security_and_forensics.mantis_sandbox_verifier.main import mantis_patch_verify

diff = '''--- app.py
+++ app.py
@@ -2,2 +2,3 @@
-    os.system("echo " + user_input)
+    import shlex, subprocess
+    subprocess.run(["echo", shlex.quote(user_input)], check=True)
'''

# Test reproducer that previously succeeded
safe_reproducer = 'import sys; sys.exit(0) # Fixed payload does not trigger crash'

patch_result = mantis_patch_verify(
    diff_content=diff,
    reproducer_script=safe_reproducer,
    run_bypass_reattack=True
)
print(f"Patch verification verdict: {patch_result['verdict']}")
```

Congratulations! You have completed a full end-to-end Mantis review, reproduction, and patch verification cycle.
