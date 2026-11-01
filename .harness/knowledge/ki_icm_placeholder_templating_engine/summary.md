# ICM Factory-Configuration Templating & Whole-Section Conditionals

## Architectural Principle: Configure the Factory, Not the Product
Traditional AI agents ask for user preferences on every conversational turn. ICM configures the **Factory** (Layer 3 reference materials, design systems, voice rules) once during onboarding using `setup/questionnaire.md`. After onboarding, every run of the pipeline produces deliverables using the initialized factory with zero redundant questions.

## Syntax Specification
1. **Variable Placeholders**:
   ```markdown
   # {{BRAND_NAME}} Style Guide
   Target audience: {{TARGET_AUDIENCE}}
   Primary palette: {{PRIMARY_COLOR}}
   ```
2. **Whole-Section Conditional Blocks**:
   Conditional blocks wrap entire sections including headings. If the user indicates a feature or channel is unneeded, the parser removes the entire section cleanly:
   ```markdown
   {{?VIDEO_PRODUCTION}}

   ## Video Production Settings
   - Resolution: 1920x1080
   - Frame rate: 30fps

   {{/VIDEO_PRODUCTION}}
   ```
   **The Whole-Section Invariant**: Inline conditionals like `The voice is {{?FORMAL}}formal{{/FORMAL}}` are strictly prohibited. Wrapping complete sections guarantees that post-removal markdown remains structurally valid without orphaned markers.
