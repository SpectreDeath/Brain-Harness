# Reference: Omarchy Quattro Bridge API & Schemas

This reference documents the service protocols, exposed tool signatures, metadata specifications, and template syntaxes for the Omarchy Quattro Bridge.

---

## Service Keys & Protocols

| Service Name | Key Identifier | Protocol Class | Category |
|---|---|---|---|
| Command Router | `service.omarchy_command_router` | `OmarchyCommandRouterService` | `developer_tooling` |
| Theming Engine | `service.omarchy_theming_engine` | `OmarchyThemingEngineService` | `developer_tooling` |
| Agent Telemetry | `service.omarchy_agent_telemetry` | `OmarchyAgentTelemetryService` | `agent_orchestration` |

---

## Exposed Tool Reference

### Command Router Plugin (`plugin.omarchy_command_router`)

#### 1. `omarchy_list_commands`
- **Parameters:**
  - `group` (`str | None`, default: `None`): Functional group filter.
  - `include_hidden` (`bool`, default: `False`): Include commands with `# omarchy:hidden=true`.
- **Returns:** `list[dict]` containing command metadata entries.

#### 2. `omarchy_get_command`
- **Parameters:**
  - `command_name` (`str`, required): Name of command (with or without `omarchy-` prefix or alias).
- **Returns:** `dict` with command metadata, shebang, size, and tags.

#### 3. `omarchy_search_commands`
- **Parameters:**
  - `query` (`str`, required): Search string to match against name, summary, usage, and examples.
- **Returns:** `list[dict]` sorted by match relevance.

#### 4. `omarchy_list_groups`
- **Parameters:** None.
- **Returns:** `list[dict]` summarizing groups with total, visible, and hidden command counts.

---

### Theming Engine Plugin (`plugin.omarchy_theming_engine`)

#### 5. `omarchy_list_themes`
- **Parameters:** None.
- **Returns:** `list[dict]` of bundled themes with mode, background, foreground, and accent.

#### 6. `omarchy_get_theme_palette`
- **Parameters:**
  - `theme_name` (`str`, required): Name of theme (e.g. `'catppuccin'`, `'tokyo-night'`).
- **Returns:** `dict` of resolved colors (both semantic and ANSI mappings).

#### 7. `omarchy_render_theme_template`
- **Parameters:**
  - `template_content` (`str`, required): Template text with placeholders.
  - `theme_name` (`str`, required): Target theme palette.
- **Returns:** `str` rendered text.

#### 8. `omarchy_validate_theme_contrast`
- **Parameters:**
  - `theme_name` (`str`, required): Name of theme.
- **Returns:** `dict` with WCAG 2.1 relative luminance and contrast ratio diagnostics.

---

### Agent Telemetry Plugin (`plugin.omarchy_agent_telemetry`)

#### 9. `omarchy_list_agent_skills`
- **Parameters:** None.
- **Returns:** `list[dict]` of skills in `agents/skills/` and `default/agents/skills/`.

#### 10. `omarchy_get_agent_skill`
- **Parameters:**
  - `skill_name` (`str`, required): Identifier of the skill.
- **Returns:** `dict` with markdown text, outline headings, and companion documents.

#### 11. `omarchy_inspect_agent_usage_scripts`
- **Parameters:** None.
- **Returns:** `list[dict]` of usage scripts with arguments, docstrings, and required environment variables.

---

## Omarchy Metadata Header Specification

Omarchy commands declare metadata in lines 1–80 using the `# omarchy:key=value` format:

| Header Tag | Type | Required | Description |
|---|---|---|---|
| `omarchy:group` | string | Recommended | Functional subsystem group (e.g., `theme`, `menu`, `agent`) |
| `omarchy:summary` | string | Recommended | One-line description of command purpose |
| `omarchy:usage` | string | Optional | Command syntax line |
| `omarchy:args` | string | Optional | Positional and optional argument syntax |
| `omarchy:examples` | string | Optional | Invocation example commands |
| `omarchy:requires_sudo` | boolean | Optional | `true` if command requires elevated permissions |
| `omarchy:hidden` | boolean | Optional | `true` if internal helper script |
| `omarchy:aliases` | comma-list | Optional | Comma-separated alternative names |

---

## Template Token Cheatsheet

| Token Syntax | Description | Example Replacement |
|---|---|---|
| `{{ key }}` | Literal color value | `#1e1e2e` |
| `{{ key_strip }}` | Hex code without leading `#` | `1e1e2e` |
| `{{ key_rgb }}` | Decimal RGB comma-separated | `30,30,46` |
| `{{ mix start end pct }}` | Linear RGB blend | `#2a2b3d` |
| `{{ mix_strip start end pct }}` | Linear RGB blend without `#` | `2a2b3d` |
| `{{ mix_rgb start end pct }}` | Linear RGB blend in decimal RGB | `42,43,61` |
| `{{ hypr_gradient key fallback }}` | Hyprland-formatted gradient string | `{ colors = { "#1e1e2e", "#89b4fa" } }` |
| `{{ gradient_start key fallback }}` | First color of gradient | `#1e1e2e` |
| `{{ shell_gradient key fallback }}` | Space-separated gradient colors | `#1e1e2e #89b4fa 45deg` |
