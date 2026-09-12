# Ecosystem Bridges (`harness.bridges`)

The `harness.bridges` package connects Brain Harness to the wider neuro-symbolic, memory, and domain skill ecosystem.

---

## Architecture & Design

Ecosystem bridges are specialized `HarnessPlugin` implementations that wrap external services and legacy runtime surfaces:

- **`EcosystemLocator`**: Locates peer ecosystem repositories (`Em-Cubed`, `Memtext`, `Skill Flywheel`) via environment variables, sibling directories, or configuration paths.
- **`EcosystemBridgePlugin`**: Base class providing structured discovery, state health checks, and fallback degradation when external services are unavailable.
- **Typed Service Keys**: Registered under authoritative keys (`EM_CUBED_BRIDGE_KEY`, `FLYWHEEL_BRIDGE_KEY`, `MEMORY_SERVICE_KEY`) to eliminate loose string lookups.

---

## Core Modules & Bridges

| Module | Key Class / Service | Description |
| --- | --- | --- |
| [`base.py`](base.py) | `EcosystemBridgePlugin` | Abstract base class establishing bridge lifecycle and status reporting. |
| [`em_cubed.py`](em_cubed.py) | `EmCubedPlugin` (`EM_CUBED_BRIDGE_KEY`) | Bridges Em-Cubed neuro-symbolic OS, Prolog theorem provers, and Z3 solvers. |
| [`flywheel.py`](flywheel.py) | `FlywheelBridgePlugin` (`FLYWHEEL_BRIDGE_KEY`) | Discovers and indexes 800+ domain skills from the local or shared Skill Flywheel catalog. |
| [`locator.py`](locator.py) | `EcosystemLocator` | Multi-strategy filesystem locator for discovery of sibling projects. |
| [`memtext.py`](memtext.py) | `MemtextServicePlugin` (`MEMORY_SERVICE_KEY`) | Bridges Memtext persistent episodic memory and autobiographical retrieval. |

---

## Programmatic Usage Example

```python
from harness.kernel.runtime import HarnessRuntime
from harness.bridges import FLYWHEEL_BRIDGE_KEY, FlywheelBridgePlugin

async with HarnessRuntime.create() as runtime:
    flywheel = runtime.context.require(FLYWHEEL_BRIDGE_KEY)
    skills = await flywheel.discover_skills()
    print(f"Discovered {len(skills)} ecosystem skills.")
```

---

## Related Documentation

- [Kernel Service Registry](../kernel/README.md)
- [Plugin System Architecture](../plugins/README.md)
