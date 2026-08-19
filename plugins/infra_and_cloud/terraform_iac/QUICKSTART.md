# Quick Start Guide: `domain.terraform_iac` (v1.0.0)

> Terraform / OpenTofu HCL parser, state drift detector, and cloud resource cost estimator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`parse_hcl_blocks`**: Parse Terraform HCL blocks (resource, variable, provider, output, module) from text
- **`detect_state_drift`**: Compare declared Terraform resource attributes against actual cloud state
- **`estimate_resource_costs`**: Estimate monthly cloud infrastructure costs based on resource type heuristics

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.terraform_iac.parse_hcl_blocks', {'hcl_content': '<hcl_content>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.terraform_iac
harness plugin enable domain.terraform_iac
```

## ⚡ Available Entrypoints & Skills
- **`parse_hcl_blocks(hcl_content: string)`**
  Parse Terraform HCL blocks (resource, variable, provider, output, module) from text
- **`detect_state_drift(declared_state: object, actual_state: object)`**
  Compare declared Terraform resource attributes against actual cloud state
- **`estimate_resource_costs(resources: array)`**
  Estimate monthly cloud infrastructure costs based on resource type heuristics