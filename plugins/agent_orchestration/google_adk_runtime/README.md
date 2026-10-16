# Google ADK Runtime Plugin

Orchestrates ADK agent workflows, sessions, and skills.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `adk_run_agent` | `(agent_name, prompt, session_id, model)` | Execute an ADK agent workflow on a user prompt with session state tracking and multi-turn memory |
| `adk_list_sessions` | `(limit)` | List active and historical ADK session states and metadata |
| `adk_rewind_session` | `(session_id, checkpoint_index)` | Rewind an ADK agent session to a previous event checkpoint |
| `adk_register_skill` | `(skill_name, description, prompt_template)` | Register a dynamic capability skill or prompt pattern into the ADK runtime |
