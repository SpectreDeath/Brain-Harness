## Frontend Integration Gap

### Discovery
A React + Vite frontend exists in `frontend/` but is not wired to the harness
CLI command layer or WebSocket telemetry endpoint.

### Integration Path
1. Add `harness ui` CLI group in commands/ that starts uvicorn server
2. Wire ui/server.py WebSocket endpoint to broadcast EventBus events
3. frontend/ React app connects to ws://localhost:PORT/ws/events
4. Deploy vite build artifacts to static file serving in FastAPI

### Source
- frontend/ (unconnected Vite app, commit 9ff3a00)
- src/harness/ui/ (FastAPI WebSocket server present but unregistered in CLI)
