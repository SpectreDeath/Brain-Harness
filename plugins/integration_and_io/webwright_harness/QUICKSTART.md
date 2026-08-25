# Webwright Harness Plugin Quickstart

The **Webwright Harness Plugin** provides SWE-style trajectory skill synthesis, semantic retrieval, parameterized execution, local Chromium daemon lifecycle management, multimodal vision QA, and post-trajectory self-reflection.

## 🚀 Quick Usage

### 1. Learning a Skill from Trajectories
```python
from harness.kernel.container import Container
from harness.services.webwright_harness import WEBWRIGHT_HARNESS_KEY

service = container.resolve(WEBWRIGHT_HARNESS_KEY)
result = await service.learn_skill(
    trajectory_dirs=["examples/trajectories/sea_jfk", "examples/trajectories/sfo_bos"],
    template="Find earliest nonstop flight from {origin} to {destination}",
    library_dir="skills",
)
print(result.skill_id, result.signature)
```

### 2. Retrieving and Routing
```python
retrieval = await service.retrieve_skills(task="Find flights from Seattle to JFK")
print(retrieval.candidates)

route_res = await service.route_and_execute(
    task="Find earliest nonstop flight from SEA to JFK",
    start_url="https://flights.google.com",
    library_dir="skills",
)
print(route_res.decision, route_res.result)
```

### 3. Chromium Daemon Management
```python
status = await service.manage_browser_session(action="create", port=9222, headless=True)
print(status.cdp_url, status.pid)

info = await service.manage_browser_session(action="info", port=9222)
print(info.status)

await service.manage_browser_session(action="release", port=9222)
```
