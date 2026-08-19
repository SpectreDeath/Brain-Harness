# Stdio JSON-RPC Sandboxing

## Overview

Untrusted plugins run in isolated child processes using `StdioJsonRpcTransport`. This design:
1. Prevents untrusted code from modifying kernel globals or mutating memory.
2. Uses standard line-delimited JSON-RPC 2.0 framing over `stdin`/`stdout`.
3. Handles process timeouts and graceful shutdown with SIGTERM $\rightarrow$ SIGKILL escalation.

```python
from harness.plugins.transport import StdioJsonRpcTransport

transport = StdioJsonRpcTransport(
    command=["python", "worker.py"],
    cwd=plugin_dir,
)
await transport.start()

# Send a JSON-RPC request
response = await transport.call("get_weather", {"city": "Tokyo"}, timeout=5.0)

await transport.stop()
```
