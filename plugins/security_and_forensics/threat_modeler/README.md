# domain.threat_modeler (v1.0.0)

STRIDE threat modeling, MITRE ATT&CK taxonomy mapping, and attack graph generator

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/security_and_forensics/threat_modeler` |
| Category | `security_and_forensics` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `model_stride_threats` | `(components)` | Model STRIDE threats (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege) for architectural components |
| `map_mitre_attack` | `(observed_techniques)` | Map observed threat behaviors or technical findings to MITRE ATT&CK Enterprise tactics and techniques |
| `generate_attack_tree` | `(adversary_goal, attack_vectors)` | Synthesize a hierarchical attack tree graph (in Mermaid and structured format) toward an adversary objective |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

STRIDE threat modeling, MITRE ATT&CK mapping, and attack graph generator plugin.

#### Functions

- `def model_stride_threats(components) -> dict[str, Any]` — Generate STRIDE threat vectors for system components.
- `def map_mitre_attack(observed_techniques) -> dict[str, Any]` — Map detected threat behaviors to MITRE ATT&CK taxonomy.
- `def generate_attack_tree(adversary_goal, attack_vectors) -> dict[str, Any]` — Synthesize an attack tree graph in Mermaid diagram format.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.security_and_forensics.threat_modeler.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
