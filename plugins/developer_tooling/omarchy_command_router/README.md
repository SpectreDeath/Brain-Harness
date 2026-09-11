# Omarchy Command Router Plugin

The `plugin.omarchy_command_router` plugin exposes programmatic introspection, discovery, and routing capabilities over Omarchy Quattro's 455+ modular CLI commands.

## Architecture

Omarchy Quattro structures its operating system commands as standalone scripts in `bin/omarchy-*`. Rather than maintaining a hardcoded centralized dispatcher, Omarchy parses `# omarchy:key=value` metadata comments directly from the top 80 lines of each executable script.

This plugin mirrors that architecture into the Brain Harness IoC container, providing:
- Lazy in-memory indexing of commands and groups
- Sub-millisecond keyword and fuzzy lookup
- Full metadata extraction (shebang, usage patterns, required arguments, sudo requirements, hidden status, aliases)
- Fallback resolution for short names and legacy aliases

## Exposed Tools

1. `omarchy_list_commands(group: str | None = None, include_hidden: bool = False)`: List commands filtered by group or visibility.
2. `omarchy_get_command(command_name: str)`: Retrieve comprehensive metadata for a specific command.
3. `omarchy_search_commands(query: str)`: Multi-field search across name, summary, usage, and examples.
4. `omarchy_list_groups()`: List all functional command groups and command statistics.

## Configuration

Default configuration is specified in `config.default.yaml`. Override the Omarchy root repository via the `OMARCHY_PATH` environment variable or direct service injection.
