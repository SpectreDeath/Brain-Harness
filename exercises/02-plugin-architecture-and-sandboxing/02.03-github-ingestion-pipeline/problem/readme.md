# Problem: Ingest a Local Python Directory as a Sandboxed Plugin

## Objective

Use `PluginIngestionEngine` to ingest a folder containing an unmanifested Python script, synthesize a manifest automatically, and load it into a test kernel.

## Tasks

1. Create a directory with a Python function.
2. Ingest the directory with `PluginIngestionEngine`.
3. Verify that the synthesized manifest contains the detected function entrypoint.
