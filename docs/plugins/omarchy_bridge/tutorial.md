# Tutorial: Getting Started with Omarchy Quattro Bridge Plugins

Welcome to the Omarchy Quattro Bridge in Brain Harness. This tutorial will walk you through interacting with Omarchy Quattro's operating system capabilities directly from the Harness agent environment.

You will learn how to:
1. Discover and query Omarchy's modular CLI commands.
2. Resolve a desktop theme palette and render dynamic configuration templates.
3. Inspect Omarchy's bundled AI agent skills and diagnostic runbooks.

---

## Prerequisites

Before starting, ensure the three Omarchy bridge plugins are enabled in your Harness configuration:
- `plugin.omarchy_command_router`
- `plugin.omarchy_theming_engine`
- `plugin.omarchy_agent_telemetry`

By default, the plugins inspect the local clone at `D:\GitHub\cloned\omarchy-quattro\omarchy-quattro`. You can also configure the `OMARCHY_PATH` environment variable.

---

## Step 1: Discovering CLI Commands

Omarchy Quattro does not use a bloated monolithic dispatcher. Instead, it maintains over 450 discrete command scripts in `bin/`, each annotated with `# omarchy:key=value` headers.

Let's list the command groups and inspect a theme command.

### Python Code

```python
from harness.kernel.context import ServiceContext
from plugins.developer_tooling.omarchy_command_router.main import (
    OMARCHY_COMMAND_ROUTER_SERVICE_KEY,
)

# Resolve the service from IoC context
context = ServiceContext()
# (Assume plugins are loaded via lifecycle manager)
router = context.require(OMARCHY_COMMAND_ROUTER_SERVICE_KEY)

# 1. List functional groups
groups = router.list_groups()
print("Discovered Groups:")
for g in groups[:5]:
    print(f"- {g['group']}: {g['total_commands']} commands ({g['visible_commands']} public)")

# 2. Search for wallpaper or theme commands
theme_commands = router.search_commands("wallpaper")
for cmd in theme_commands:
    print(f"Command: {cmd['name']} — {cmd['summary']}")
```

### Expected Output

```text
Discovered Groups:
- agent: 6 commands (2 public)
- audio: 8 commands (8 public)
- bluetooth: 5 commands (5 public)
- font: 12 commands (12 public)
- theme: 28 commands (25 public)

Command: omarchy-theme-set-wallpaper — Set desktop wallpaper from active theme
```

---

## Step 2: Resolving Theme Palettes and Rendering Templates

Omarchy uses a unified `colors.toml` palette for each desktop theme. Let's inspect the `catppuccin` palette and render a terminal configuration snippet.

### Python Code

```python
from plugins.developer_tooling.omarchy_theming_engine.main import (
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
)

theming = context.require(OMARCHY_THEMING_ENGINE_SERVICE_KEY)

# 1. Inspect palette
palette = theming.get_theme_palette("catppuccin")
print(f"Theme mode: {palette['mode']}")
print(f"Background: {palette['background']}, Foreground: {palette['foreground']}")
print(f"Auto-derived Dark Background: {palette['dark_background']}")

# 2. Render a configuration template
template = """
[colors]
surface = "{{ background }}"
surface_stripped = "{{ background_strip }}"
surface_rgb = "{{ background_rgb }}"
border_blend = "{{ mix background accent 30% }}"
"""

rendered = theming.render_theme_template(template, "catppuccin")
print("\nRendered Config:")
print(rendered)
```

### Expected Output

```text
Theme mode: dark
Background: #1e1e2e, Foreground: #cdd6f4
Auto-derived Dark Background: #161622

Rendered Config:
[colors]
surface = "#1e1e2e"
surface_stripped = "1e1e2e"
surface_rgb = "30,30,46"
border_blend = "#3e4ba0"
```

---

## Step 3: Inspecting Agent Skills and Telemetry

Omarchy includes AI agent instructions and diagnostics. Let's inspect the bundled skills without executing non-portable shell commands.

### Python Code

```python
from plugins.agent_orchestration.omarchy_agent_telemetry.main import (
    OMARCHY_AGENT_TELEMETRY_SERVICE_KEY,
)

telemetry = context.require(OMARCHY_AGENT_TELEMETRY_SERVICE_KEY)

# 1. Enumerate available skills
skills = telemetry.list_agent_skills()
print(f"Discovered {len(skills)} agent skills and guides.")

# 2. Inspect the desktop customization skill
omarchy_skill = telemetry.get_agent_skill("omarchy")
print(f"Skill: {omarchy_skill['name']}")
print(f"Sections ({len(omarchy_skill['outline'])}):")
for section in omarchy_skill['outline'][:5]:
    print(f"  {'  ' * (section['level'] - 1)}- {section['title']}")
```

---

## Next Steps

- Consult the [How-To Guides](how_to.md) for practical tasks such as adding commands and auditing contrast ratios.
- Review the [Reference](reference.md) for tool schemas and parameter details.
- Read the [Architecture Explanation](explanation.md) to understand the design trade-offs behind decentralized metadata and sed-compatible templating.
