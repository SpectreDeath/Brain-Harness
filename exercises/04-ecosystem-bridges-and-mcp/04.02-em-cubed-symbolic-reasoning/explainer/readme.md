# Em-Cubed Neuro-Symbolic Reasoning Bridge

## Overview

The `EmCubedPlugin` exposes formal symbolic surfaces (logic rules, Z3 constraints, schema reasoning) to autonomous agents.

```python
from harness.bridges.em_cubed import EMCUBED_SERVICE_KEY, EmCubedPlugin, EmCubedService

bridge = EmCubedPlugin()
await bridge.on_load(ctx)
await bridge.on_enable()

em3: EmCubedService = ctx.require(EMCUBED_SERVICE_KEY)

# Solve constraints
res = await em3.solve_constraints([
    "x > 10",
    "y < 5",
    "x + y == 15",
])
# {"status": "sat", "model": {"x": 11, "y": 4}}
```
