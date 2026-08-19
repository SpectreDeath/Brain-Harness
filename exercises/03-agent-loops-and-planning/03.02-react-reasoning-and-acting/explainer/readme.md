# ReAct Reasoning and Acting Loop

## Overview

The `ReActAgentService` executes autonomous tasks using the ReAct (Reasoning + Acting) loop:

```
           ┌──────────────────────┐
           │      User Task       │
           └──────────┬───────────┘
                      │
           ┌──────────▼───────────┐
     ┌────►│  Thought (Reasoning) │
     │     └──────────┬───────────┘
     │                │
     │     ┌──────────▼───────────┐
     │     │ Action (Tool Call)   │
     │     └──────────┬───────────┘
     │                │
     │     ┌──────────▼───────────┐
     └─────┤ Observation (Result) │
           └──────────┬───────────┘
                      │
           ┌──────────▼───────────┐
           │     Final Answer     │
           └──────────────────────┘
```

```python
from harness.agent.react import ReActAgentService
from harness.services.tools import ToolRegistry
from harness.services.llm import LiteLLMService

agent = ReActAgentService(llm=llm_service, tools=tool_registry, max_steps=10)
result = await agent.run("Find all python files and summarize the architecture.")
```
