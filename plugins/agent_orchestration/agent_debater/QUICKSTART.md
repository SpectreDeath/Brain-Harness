# Quick Start Guide: `domain.agent_debater` (v1.0.0)

> Dialectical multi-agent reasoning, Proposer vs Challenger debate rounds, and arbiter verdict synthesizer

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`conduct_dialectical_debate`**: Run structured dialectical debate rounds (Thesis / Proposer vs Antithesis / Challenger)
- **`synthesize_debate_verdict`**: Synthesize final arbiter verdict, identifying concessions, unaddressed risks, and final recommendation

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.agent_debater.conduct_dialectical_debate', {'topic': '<topic>', 'pro_arguments': '<pro_arguments>', 'con_arguments': '<con_arguments>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.agent_debater
harness plugin enable domain.agent_debater
```

## ⚡ Available Entrypoints & Skills
- **`conduct_dialectical_debate(topic: string, pro_arguments: array, con_arguments: array)`**
  Run structured dialectical debate rounds (Thesis / Proposer vs Antithesis / Challenger)
- **`synthesize_debate_verdict(debate_summary: object)`**
  Synthesize final arbiter verdict, identifying concessions, unaddressed risks, and final recommendation