# Quick Start Guide: `plugin.artifact_generator` (v1.0.0)

> Interactive HTML report generation, Mermaid diagram visualization, and executive briefings

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`report_generate_html`**: Generate an interactive, responsive HTML report with charts and formatted tables
- **`diagram_generate_mermaid`**: Synthesize valid Mermaid diagram syntax from nodes and edges
- **`report_create_briefing`**: Create an executive markdown and HTML briefing summary

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.artifact_generator.report_generate_html', {'title': '<title>', 'sections': '<sections>', 'output_path': '<output_path>', 'theme': '<theme>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.artifact_generator
harness plugin enable plugin.artifact_generator
```

## ⚡ Available Entrypoints & Skills
- **`report_generate_html(title: string, sections: array, output_path: string, theme: string)`**
  Generate an interactive, responsive HTML report with charts and formatted tables
- **`diagram_generate_mermaid(nodes: array, edges: array, direction: string)`**
  Synthesize valid Mermaid diagram syntax from nodes and edges
- **`report_create_briefing(title: string, summary: string, metrics: object, recommendations: array, output_path: string)`**
  Create an executive markdown and HTML briefing summary