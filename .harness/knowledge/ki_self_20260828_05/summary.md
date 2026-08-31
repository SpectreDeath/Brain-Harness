# Knowledge Item: Dual-Mode UI Serving & Zero-Build SPA Fallback

- **ID**: `ki_self_20260828_05`
- **Category**: `ui_architecture` / `serving`
- **Status**: `VERIFIED`

## Summary & Heuristic

When building developer harnesses and CLI-driven applications, imposing Node.js and NPM build prerequisites on every user causes cold-start friction and broke pure-Python installations.

### Core Guidelines:
1. **Zero-Build Baseline**: Provide an embedded, zero-dependency single-file HTML/CSS/JS dashboard in `src/harness/ui/static/index.html` as the baseline.
2. **Auto-Detecting Bundle Mount**: In the Python backend server, inspect `frontend/dist/index.html`. If present, mount the compiled bundle directory and serve `dist/index.html`.
3. **Graceful Fallback**: If `frontend/dist/` is absent or unbuilt, seamlessly serve `src/harness/ui/static/index.html` without warnings or exceptions.
4. **Universal REST & WebSocket Contracts**: Ensure the API and real-time WebSocket protocol are strictly identical across both frontend implementations so switching modes requires zero backend reconfiguration.
