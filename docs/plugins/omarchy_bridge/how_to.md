# How-To Guides: Omarchy Quattro Bridge

This document provides actionable recipes for common tasks when working with the Omarchy Quattro Bridge plugins in Brain Harness.

---

## How to Author a New Command with Auto-Discovered Metadata

Omarchy's command router automatically discovers commands in `bin/` by scanning the first 80 lines for `# omarchy:key=value` headers.

### Step-by-Step

1. Create a new executable script under `bin/omarchy-<subsystem>-<action>` (or your development path).
2. Add a standard shebang on line 1:
   ```bash
   #!/usr/bin/env bash
   ```
3. Add the required and optional Omarchy metadata headers:
   ```bash
   # omarchy:group=audio
   # omarchy:summary=Switch default pipewire audio sink
   # omarchy:usage=omarchy-audio-switch-sink <sink-name>
   # omarchy:args=[--volume <0-100>] <sink-name>
   # omarchy:examples=omarchy-audio-switch-sink alsa_output.pci-0000_00_1f.3
   # omarchy:requires_sudo=false
   # omarchy:hidden=false
   # omarchy:aliases=audio-sink,switch-sink
   ```
4. Query the command router in Python to verify discovery:
   ```python
   router = context.require(OMARCHY_COMMAND_ROUTER_SERVICE_KEY)
   cmd = router.get_command("switch-sink")
   assert cmd["group"] == "audio"
   assert cmd["summary"] == "Switch default pipewire audio sink"
   ```

---

## How to Audit and Fix WCAG Contrast in a Theme

To ensure accessibility across all desktop terminals and editors, run the contrast verification tool.

### Running the Audit

```python
from plugins.developer_tooling.omarchy_theming_engine.main import (
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
)

theming = context.require(OMARCHY_THEMING_ENGINE_SERVICE_KEY)
report = theming.validate_theme_contrast("catppuccin")

print(f"Compliant with WCAG AA: {report['overall_compliant_wcag_aa']}")
for check_name, details in report["checks"].items():
    print(f"- {check_name}: {details['ratio']}:1 (AA: {details['passes_wcag_aa']})")
```

### Remedying Low Contrast

If `dark_foreground_on_background` fails the 4.5:1 ratio:
1. Open `themes/<theme_name>/colors.toml`.
2. Adjust `dark_foreground` to a lighter hex value (or darker for light themes).
3. Alternatively, adjust `dark_background` to deepen the background surface.
4. Re-run `validate_theme_contrast` to verify compliance.

---

## How to Render Omarchy Template Files (`.tpl`)

Omarchy bundles 19 configuration templates in `default/themed/`. To render any of these templates against a specific theme:

```python
from pathlib import Path
from plugins.developer_tooling.omarchy_theming_engine.main import (
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
)

theming = context.require(OMARCHY_THEMING_ENGINE_SERVICE_KEY)

# Read any .tpl file
tpl_path = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro\default\themed\ghostty.tpl")
if tpl_path.exists():
    content = tpl_path.read_text(encoding="utf-8")
    rendered = theming.render_theme_template(content, "tokyo-night")
    print(rendered)
```

---

## How to Configure the Omarchy Repository Path Dynamically

If your Omarchy clone resides in a non-standard location or in CI:

### Via Environment Variable

Set `OMARCHY_PATH` prior to application startup:
```bash
export OMARCHY_PATH="/path/to/omarchy-quattro"
```

### Via Service Constructor

Instantiate the service with an explicit path:
```python
from plugins.developer_tooling.omarchy_command_router.main import (
    OmarchyCommandRouterServiceImpl,
)

router = OmarchyCommandRouterServiceImpl(source_dir="/custom/path/to/omarchy")
```
