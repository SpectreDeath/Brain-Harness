# Harness Plugin & Skill Creator (`harness.creator`)

The `harness.creator` package provides autonomous scaffolding, dynamic synthesis, AST validation, and quality auditing for Brain Harness plugins and agent skills.

---

## Central Function & Capabilities

The creator package enables agents and developers to build, inspect, and verify new capabilities:
1. **Archetype Scaffolding**: Standardized templates for tools, services, MCP bridges, and agent workflows via `ArchetypeRegistry` and `PluginScaffoldEngine`.
2. **Autonomous Synthesis**: LLM-driven synthesis of production-ready plugins with zero-fork configuration (`config.default.yaml`) and typed IoC service registration.
3. **Multi-Stage Validation**: Multi-rule verification engines enforcing AST syntax validity, manifest schema compliance, safe sandbox dry-runs, and entrypoint signatures.
4. **Skill SDLC & Linting**: Specialized scaffolding and validation for `.agents/skills/` adhering to craft standards, frontmatter character limits, and companion `CARD.md` metadata cards.

---

## Architectural Invariants

- **ValidationReport Contract (Rule 34)**: Validators return a structured `ValidationReport` where overall status is checked via `report.valid` (never `report.passed`), with granular rules in `report.checks`.
- **Async Coroutine & Sync Helper (Rule 38)**: `PluginValidator.validate()` is asynchronous (`async def validate()`); synchronous scripts and test fixtures must invoke `PluginValidator.validate_sync()`.
- **Skill Card Delimiters (Rule 37)**: `CARD.md` metadata boxes must use standard single-pipe borders (`|`), contain `SKILL: <skill-name>`, anti-patterns under `## Anti-Patterns`, and a `## Mandatory Invariants Checklist`.
- **Catalog Budget & Negative Boundaries (Rule 44)**: Skill descriptions must be bounded between 100 and 350 characters and include explicit negative boundaries ("Do not use for...").
- **Plugin Module Singleton (Rule 45)**: All scaffolded plugins must subclass `HarnessPlugin`, declare typed service keys in `provides`, and export a module-level `plugin = MyPlugin()` singleton.

---

## Key Modules & Symbols

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`archetypes.py`](archetypes.py) | `ArchetypeRegistry`, `ToolArchetype`, `ServiceArchetype`, `McpBridgeArchetype` | Pattern registry generating boilerplate structures for domain plugin types. |
| [`creator.py`](creator.py) | `PluginCreator` | High-level orchestrator combining scaffolding, synthesis, and validation. |
| [`dynamic.py`](dynamic.py) | `DynamicPluginBuilder`, `DynamicPythonPlugin` | Generates and loads in-memory ephemeral plugins without touching the filesystem. |
| [`introspection.py`](introspection.py) | `RuntimeIntrospector` | Introspects active kernel state and registered services to infer needed dependencies. |
| [`scaffold.py`](scaffold.py) | `PluginScaffoldEngine`, `ScaffoldOptions`, `ScaffoldResult` | Scaffolds plugin directory trees, manifests, default configurations, and test files. |
| [`schema.py`](schema.py) | `SchemaInferrer` | Generates JSONSchema definitions from Python types and function signatures. |
| [`skills.py`](skills.py) | `SkillScaffoldEngine`, `SkillValidator`, `SkillCardRule` | Scaffolds and audits agent skills in `.agents/skills/` against SDLC craft standards. |
| [`synthesis.py`](synthesis.py) | `CreatorService`, `PluginSynthesisEngine`, `CREATOR_SERVICE_KEY` | Orchestrates LLM prompt pipelines for automated capability synthesis. |
| [`validator.py`](validator.py) | `PluginValidator`, `ValidationReport`, `ValidationCheck`, `RuleSeverity` | Multi-rule AST and sandbox validator ensuring plugin safety before loading. |

---

## Programmatic Usage Example

```python
import asyncio
from pathlib import Path
from harness.creator.scaffold import PluginScaffoldEngine, ScaffoldOptions
from harness.creator.validator import PluginValidator

async def scaffold_and_verify_plugin(name: str, category: str):
    # 1. Scaffold plugin directory and files
    engine = PluginScaffoldEngine()
    result = engine.scaffold(
        ScaffoldOptions(
            plugin_id=name,
            category=category,
            archetype="tool",
            output_dir=Path(f"plugins/{category}/{name}"),
        )
    )
    print(f"Scaffolded files: {len(result.created_files)}")
    
    # 2. Validate plugin against architectural invariants
    validator = PluginValidator()
    report = await validator.validate(result.plugin_dir)
    if not report.valid:
        for check in report.checks:
            if not check.passed:
                print(f"[{check.rule}] FAILED: {check.message}")
    else:
        print(f"Plugin '{name}' passed all architectural validation gates.")

if __name__ == "__main__":
    asyncio.run(scaffold_and_verify_plugin("weather_tool", "data_engineering"))
```

---

## Related Documentation

- [Plugin Architecture Guide](../../../docs/EXPLANATION.md)
- [How-To: Author a New Plugin](../../../docs/HOWTO.md#authoring-a-custom-plugin)
- [Plugin Validator Reference](../../../docs/reference/plugin-manifest.md)
- [Kernel Lifecycle](../kernel/README.md)
