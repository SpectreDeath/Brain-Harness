# Quick-Reference Summary Card: plugin.icm_architect

```
┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: plugin.icm_architect                                            │
├────────────────────────────────────────────────────────────────────────┤
│ Method:     Interpretable Context Methodology (arXiv:2603.16021)       │
│ Role:       Folder Structure as Agent Architecture Engine              │
│ Service:    harness.services.icm_architect (Rule 1 & Rule 2)           │
│ Tools:      Audit, Verify Links, Verify Quotes, Rebuild Index,         │
│             Scaffold Form, Scaffold Workspace, Interpolate Template    │
│ Isolation:  InProcessExecutor (Rule 5 Trusted Internal Plugin)         │
└────────────────────────────────────────────────────────────────────────┘
```

## Tool Matrix

| Tool Entrypoint | Primary Responsibility | Input Parameters | Return Type |
|---|---|---|---|
| `icm_audit_workspace` | Audit workspace against 10 invariants & token limits | `root: str = "."` | `IcmWorkspaceAuditReport` |
| `icm_verify_links` | Verify relative markdown links & input paths | `root: str = ".", skip: list, graph: str` | `IcmLinkCheckReport` |
| `icm_verify_quotes` | Check quote citations against raw sources | `root: str = ".", show_cuts: bool` | `IcmQuoteCheckReport` |
| `icm_rebuild_index` | Regenerate `_index.md` from frontmatter | `folders: list[str], root: str` | `IcmIndexReport` |
| `icm_scaffold_form` | Scaffold one of 5 canonical ICM forms | `target_dir: str, form: str, name: str` | `IcmScaffoldResult` |
| `icm_scaffold_workspace` | Instantiate production workspace from templates | `target_dir: str, template: str, vars: dict` | `IcmScaffoldResult` |
| `icm_interpolate_template` | Substitute `{{VARIABLE}}` per placeholder syntax | `template_path: str, vars: dict, out_path: str` | `dict` |

## Mandatory Invariants Checklist

- [ ] Every working folder carries a `CONTEXT.md` defining Inputs, Process, Outputs, and Check (Invariant 4).
- [ ] Root `AGENTS.md` remains strictly under 60 lines and acts purely as an entry routing catalog (Invariant 2).
- [ ] Step context remains bounded strictly under 8,000 tokens prior to agent dispatch (Invariant 7).
- [ ] Every stage handoff terminates at an auditable check emitting `check.md` before downstream execution (Invariant 6).
- [ ] All relative markdown links and contract inputs resolve without breakage (Invariant 8).
- [ ] Placeholders follow double-brace screaming snake case `{{VARIABLE}}` per `_core/placeholder-syntax.md`.
