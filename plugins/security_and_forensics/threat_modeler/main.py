"""STRIDE threat modeling, MITRE ATT&CK mapping, and attack graph generator plugin."""

from __future__ import annotations

from typing import Any

# MITRE ATT&CK enterprise mappings
_MITRE_TAXONOMY: dict[str, dict[str, str]] = {
    "credential_dumping": {
        "id": "T1003",
        "name": "OS Credential Dumping",
        "tactic": "Credential Access",
        "mitigation": "Enable LSA protection and restrict administrative credentials.",
    },
    "sql_injection": {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "mitigation": "Use parameterized queries and ORM abstractions.",
    },
    "privilege_escalation": {
        "id": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "tactic": "Privilege Escalation",
        "mitigation": "Apply least privilege and kernel patch management.",
    },
    "data_exfiltration": {
        "id": "T1048",
        "name": "Exfiltration Over Alternative Protocol",
        "tactic": "Exfiltration",
        "mitigation": "Enforce egress filtering and DLP monitoring.",
    },
    "phishing": {
        "id": "T1566",
        "name": "Phishing",
        "tactic": "Initial Access",
        "mitigation": "Enforce FIDO2 MFA and email security filters.",
    },
}


def model_stride_threats(components: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate STRIDE threat vectors for system components."""
    threats: list[dict[str, Any]] = []

    for comp in components:
        name = comp.get("name", "Unknown Component")
        comp_type = comp.get("type", "service")
        has_auth = comp.get("auth", True)
        stores_data = comp.get("stores_data", False)

        # S - Spoofing
        if not has_auth:
            threats.append({
                "component": name,
                "category": "Spoofing",
                "risk": "High",
                "description": f"Unauthenticated endpoint on {name} allows identity spoofing.",
            })

        # T - Tampering
        threats.append({
            "component": name,
            "category": "Tampering",
            "risk": "Medium",
            "description": f"Ensure payload validation and digital signatures on data passed to {name}.",
        })

        # I - Information Disclosure
        if stores_data:
            threats.append({
                "component": name,
                "category": "Information Disclosure",
                "risk": "High",
                "description": f"Data at rest in {name} requires AES-256 encryption and access logging.",
            })

        # D - Denial of Service
        if comp_type in ("web_service", "api_gateway"):
            threats.append({
                "component": name,
                "category": "Denial of Service",
                "risk": "Medium",
                "description": f"Public surface {name} requires rate-limiting and burst throttling.",
            })

        # E - Elevation of Privilege
        threats.append({
            "component": name,
            "category": "Elevation of Privilege",
            "risk": "High",
            "description": f"Enforce role-based access control (RBAC) boundaries in {name}.",
        })

    return {
        "status": "ok",
        "components_evaluated": len(components),
        "threats_count": len(threats),
        "threats": threats,
    }


def map_mitre_attack(observed_techniques: list[str]) -> dict[str, Any]:
    """Map detected threat behaviors to MITRE ATT&CK taxonomy."""
    mapped: list[dict[str, Any]] = []
    unmapped: list[str] = []

    for tech in observed_techniques:
        key = tech.lower().replace(" ", "_").replace("-", "_")
        if key in _MITRE_TAXONOMY:
            item = dict(_MITRE_TAXONOMY[key])
            item["query_term"] = tech
            mapped.append(item)
        else:
            unmapped.append(tech)

    return {
        "status": "ok",
        "mapped_count": len(mapped),
        "unmapped_count": len(unmapped),
        "mapped_techniques": mapped,
        "unmapped_techniques": unmapped,
    }


def generate_attack_tree(adversary_goal: str, attack_vectors: list[str]) -> dict[str, Any]:
    """Synthesize an attack tree graph in Mermaid diagram format."""
    mermaid_lines = ["graph TD", f'    Goal["🎯 Goal: {adversary_goal}"]']

    for i, vec in enumerate(attack_vectors, start=1):
        node_id = f"Vector_{i}"
        mermaid_lines.append(f'    Goal --> {node_id}["Vector {i}: {vec}"]')

    mermaid_code = "\n".join(mermaid_lines)
    return {
        "status": "ok",
        "adversary_goal": adversary_goal,
        "vectors_count": len(attack_vectors),
        "mermaid": mermaid_code,
    }
