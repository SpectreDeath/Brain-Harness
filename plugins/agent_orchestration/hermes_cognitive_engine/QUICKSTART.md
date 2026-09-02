# Quick Start Guide: `domain.hermes_cognitive_engine`

## 🎯 When to Use
Use this plugin when managing closed learning loops, autonomous skill extraction, verification evidence checking, and thinking stream parsing.

## 🛠️ Available Entrypoints
- `create_skill_from_trajectory(trajectory_id, skill_name, domain, tool_sequence)`
- `evaluate_verification_evidence(session_id, executed_commands, file_mutations)`
- `scrub_think_stream(raw_chunk, capture_telemetry)`
- `nudge_learning_persistence(turn_count, complexity_score)`
