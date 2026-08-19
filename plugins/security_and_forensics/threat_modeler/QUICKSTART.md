# Quick Start Guide: `domain.threat_modeler` (v1.0.0)

> STRIDE threat modeling, MITRE ATT&CK taxonomy mapping, and attack graph generator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`model_stride_threats`**: Model STRIDE threats (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege) for architectural components
- **`map_mitre_attack`**: Map observed threat behaviors or technical findings to MITRE ATT&CK Enterprise tactics and techniques
- **`generate_attack_tree`**: Synthesize a hierarchical attack tree graph (in Mermaid and structured format) toward an adversary objective

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.threat_modeler.model_stride_threats', {'components': '<components>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.threat_modeler
harness plugin enable domain.threat_modeler
```

## ⚡ Available Entrypoints & Skills
- **`model_stride_threats(components: array)`**
  Model STRIDE threats (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation of Privilege) for architectural components
- **`map_mitre_attack(observed_techniques: array)`**
  Map observed threat behaviors or technical findings to MITRE ATT&CK Enterprise tactics and techniques
- **`generate_attack_tree(adversary_goal: string, attack_vectors: array)`**
  Synthesize a hierarchical attack tree graph (in Mermaid and structured format) toward an adversary objective