# Omarchy Theming Engine Plugin

The `plugin.omarchy_theming_engine` plugin brings Omarchy Quattro's complete theme and styling architecture into the Brain Harness ecosystem.

## Architecture

Omarchy Quattro uses a unified theming system where themes define a 16-color ANSI base and semantic roles in `colors.toml`. Configuration files across window managers (Hyprland, Sway), terminals (Ghostty, Alacritty, Kitty), editors (Neovim), and shells (Starship) are generated from templates in `default/themed/*.tpl`.

This plugin implements:
- Full TOML palette loading with legacy fallback aliases (e.g., `bg` -> `background`, `fg` -> `foreground`, `color0-15` ANSI mappings)
- Automatic shade derivation via linear RGB interpolation (`mix_colors()`)
- Template substitution matching Omarchy's sed rendering:
  - `{{ key }}`
  - `{{ key_strip }}`
  - `{{ key_rgb }}`
  - `{{ mix start end pct }}`
  - `{{ mix_strip start end pct }}`
  - `{{ mix_rgb start end pct }}`
  - `{{ hypr_gradient key fallback }}`
  - `{{ gradient_start key fallback }}`
  - `{{ shell_gradient key fallback }}`
- WCAG 2.1 relative luminance and contrast ratio auditing for accessibility

## Exposed Tools

1. `omarchy_list_themes()`: Enumerate all bundled themes with mode, background, foreground, and accent preview.
2. `omarchy_get_theme_palette(theme_name: str)`: Extract and resolve the complete dictionary of color definitions.
3. `omarchy_render_theme_template(template_content: str, theme_name: str)`: Interpolate theme tokens into arbitrary configuration templates.
4. `omarchy_validate_theme_contrast(theme_name: str)`: Evaluate contrast ratios between key surface and text colors against WCAG AA and AAA standards.

## Configuration

Specified in `config.default.yaml`.
