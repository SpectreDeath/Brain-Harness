# Problem: Spawn and Communicate with a JSON-RPC Subprocess

## Objective

Initialize a `StdioJsonRpcTransport` instance pointing to a Python one-liner echo responder, start the process, make an RPC call, and shut it down cleanly.

## Tasks

1. Create a script responding to JSON-RPC request lines on stdin.
2. Initialize and start `StdioJsonRpcTransport`.
3. Dispatch an RPC method call and verify the result.
4. Stop the transport.
