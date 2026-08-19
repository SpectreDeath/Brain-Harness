# Solution: Ingest a Local Python Directory as a Sandboxed Plugin

## Explanation

`PluginIngestionEngine` inspects the directory structure with `PluginInspector`, parses AST function definitions, synthesizes a valid `PluginManifest`, and instantiates an isolated `SandboxedPlugin`.
