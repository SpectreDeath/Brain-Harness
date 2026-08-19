# GitHub Ingestion Pipeline

## Overview

Brain Harness can ingest third-party repositories or zip archives directly into live plugins via `PluginIngestionEngine`.

```
GitHub / ZIP / Local Folder
           │
           ▼
 [PluginFetcher]  (Downloads / Extracts)
           │
           ▼
[PluginInspector] (AST scan & Manifest synthesis)
           │
           ▼
[SandboxedPlugin] (Wraps execution in isolated subprocess)
```

```python
from harness.ingestion.engine import PluginIngestionEngine

engine = PluginIngestionEngine()
plugin = await engine.ingest("https://github.com/example/weather-tool")
```
