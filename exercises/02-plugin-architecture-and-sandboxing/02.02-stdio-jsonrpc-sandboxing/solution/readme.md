# Solution: Spawn and Communicate with a JSON-RPC Subprocess

## Explanation

The solution starts `StdioJsonRpcTransport`, sends an async request with ID multiplexing, waits for the structured JSON response, and ensures clean process termination in a `try...finally` block.
