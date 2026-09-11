# How-To Guides: Mantis Security Review & Sandbox Verifier

Actionable recipes for common security operations using the Mantis plugins.

---

## 1. How to Chain Individual Bugs into a High-Impact Exploit
When multiple lower-severity flaws (such as information leakage and internal network access) can be compounded into arbitrary code execution:

```python
from plugins.security_and_forensics.mantis_security_review.main import mantis_chain_exploits

findings = [
    {
        "id": "find_001",
        "title": "Hardcoded API Key in config",
        "cwe": "CWE-798",
        "severity": "medium",
    },
    {
        "id": "find_002",
        "title": "Remote Code Execution in evaluation handler",
        "cwe": "CWE-95",
        "severity": "critical",
    }
]

chain_res = mantis_chain_exploits(
    findings=findings,
    target_objective="Full Remote Server Compromise"
)

for chain in chain_res["exploit_chains"]:
    print(f"Constructed Chain: {chain['objective']} ({chain['compound_severity']})")
    for step in chain["steps"]:
        print(f"  Step {step['step']}: {step['tactic']} -> {step['description']}")
```

---

## 2. How to Calibrate Risk Based on Asset Criticality
Adjust raw CVSS base ratings according to system environment (e.g. production database vs. internal staging sandbox):

```python
from plugins.security_and_forensics.mantis_security_review.main import mantis_calibrate_risk

findings = [
    {"id": "f1", "title": "SQL Injection in User Search", "cwe": "CWE-89", "severity": "high"},
    {"id": "f2", "title": "Missing Rate Limiting", "cwe": "CWE-799", "severity": "low"},
]

# Calibrate for Critical Production Asset
calibrated = mantis_calibrate_risk(findings=findings, asset_criticality="critical")

for item in calibrated["calibrated_findings"]:
    print(f"{item['title']}: {item['base_severity']} -> {item['calibrated_severity']} (CVSS {item['calibrated_cvss_score']})")
```

---

## 3. How to Query the AST Structural Index for Fast Symbol Audits
Avoid loading entire multi-megabyte source trees by querying the content-addressed SQLite index:

```python
from plugins.software_engineering.mantis_structural_index.main import (
    mantis_build_structural_index,
    mantis_query_symbol,
)

# 1. Build index
mantis_build_structural_index(repo_path="src", db_path="structural_index.db")

# 2. Query definitions & callers of sensitive function
result = mantis_query_symbol(
    symbol_name="authenticate_token",
    db_path="structural_index.db",
    query_type="all"
)

print(f"Definitions found: {result['definitions_count']}")
print(f"Callers found: {result['references_count']}")
```

---

## 4. How to Filter Assertion Traps with the Critic
Ensure your findings do not report vulnerabilities that are disabled when running under `python -O` (where assertions are compiled out):

```python
from plugins.security_and_forensics.mantis_security_review.main import mantis_critic_filter

false_finding = {
    "title": "Crash via assert statement in validator",
    "description": "Triggering assertion error via assert user != None",
    "filepath": "auth.py"
}

verdict = mantis_critic_filter(finding=false_finding, check_release_assertions=True)
print("Viable in production?", verdict["viable_in_production"])  # False
print("Reason:", verdict["reason"])
```
