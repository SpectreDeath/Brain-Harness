# Authoring Custom Plugins

## Overview

In Brain Harness, plugins can either be written as trusted Python classes inheriting from `HarnessPlugin` or defined via a `plugin.json` manifest.

```python
from harness.plugins.base import HarnessPlugin
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

class MathPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "math.tools"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    async def on_enable(self) -> None:
        registry: ToolRegistry = self.context.require(TOOL_REGISTRY_KEY)
        registry.register(
            name="math.multiply",
            description="Multiply two integers",
            executor=lambda a, b: a * b,
            provider=self.name,
        )
```

## Structure of `plugin.json`

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "entrypoint": "main.py",
  "isolation": "in_process",
  "entrypoints": [
    {
      "name": "my_tool",
      "description": "Performs custom tool logic",
      "parameters": [{"name": "input_str", "type": "string", "required": true}]
    }
  ]
}
```
