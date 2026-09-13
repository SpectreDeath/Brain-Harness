# Zero-Dependency Standalone Animated SVG Embedding Pattern

## Context
GitHub PR descriptions and markdown comments strictly sanitize untrusted HTML, stripping `<script>` tags, custom canvas elements, and iframe embeds. Traditional dynamic diagrams (e.g., Mermaid with JS or interactive WebGL) cannot execute inside PR review comments.

## Distilled Learning
PR Lens overcomes PR sandbox sanitization by compiling full interactive and animated diagrams into self-contained SVGs:
- **Pure CSS Keyframes**: Flow and data-pulse animations along directed edges are achieved using SVG `<path>` stroke-dasharray and stroke-dashoffset animation via inline `<style>` CSS rules.
- **Responsive Dark/Light Mode**: Incorporates `@media (prefers-color-scheme: dark)` directly inside the SVG `<style>` tag, adapting node fills, borders, and text colors dynamically to the reviewer's IDE or GitHub theme.
- **Zero External Dependencies**: Standalone SVGs require no external fonts, JS bundles, or CDN stylesheets, rendering with 100% fidelity offline or across firewall-restricted enterprise GitHub Enterprise instances.

## Triggers & Seam Choices
- **Trigger**: Generating PR summaries, visual diff reports, and CI comment scaffolding.
- **Seam Choice**: Renderer service implementations (`PrLensGraphService.render_svg()`) and agent output formatting.
