# Tool Registry and Schema Validation

## Overview

The `ToolRegistry` service provides a typed dispatch table for tools accessible by autonomous agents. Each tool registers:
- `name`: Unique identifier (e.g. `fs.read_file`).
- `description`: LLM-readable purpose.
- `executor`: Async or sync callable.
- `parameters_schema`: JSON schema defining arguments.

```python
from harness.services.tools import ToolRegistry

registry = ToolRegistry()

registry.register(
    name="math.add",
    description="Add two integers",
    executor=lambda a, b: a + b,
    parameters_schema={
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
        },
        "required": ["a", "b"],
    },
)

# Invoke with arguments dict
res = await registry.invoke("math.add", {"a": 5, "b": 10})
# {"status": "ok", "result": 15}
```
