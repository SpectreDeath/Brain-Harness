# Stagehand Browser Plugin Quickstart

The **Stagehand Browser Plugin** provides Browserbase's next-generation AI web automation framework, featuring natural language actions (`act`), schema-driven DOM data extraction (`extract`), interactive element discovery (`observe`), Web Model Context Protocol (`webmcp`) tool invocation, and complete browser session control.

## 🚀 Quick Usage

### 1. Initializing and Navigating a Session
```python
from harness.kernel.container import Container
from harness.services.stagehand_browser import STAGEHAND_BROWSER_KEY

service = container.resolve(STAGEHAND_BROWSER_KEY)

# Initialize and navigate
session = await service.control_session(action="init", url="https://example.com")
print(session.session_id, session.current_url)

# Navigate to a new page
await service.control_session(action="goto", url="https://github.com/trending")
```

### 2. Natural Language Actions (`act`)
```python
act_res = await service.act(
    action="click the 'Sign up for free' button",
    model="gpt-4o",
    timeout_s=30,
)
print(act_res.success, act_res.action_performed)
```

### 3. Structured Data Extraction (`extract`)
```python
schema = {
    "type": "object",
    "properties": {
        "repositories": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of trending repository names",
        },
        "time_period": {"type": "string"},
    },
    "required": ["repositories"],
}

extract_res = await service.extract(
    instruction="Extract trending repositories list and current time period",
    schema=schema,
)
print(extract_res.data)
```

### 4. DOM Element Discovery (`observe`)
```python
obs_res = await service.observe(instruction="Find navigation and search buttons")
for el in obs_res.elements:
    print(el.selector, el.description, el.action_suggested)
```

### 5. WebMCP (Web Model Context Protocol)
```python
# List available WebMCP tools on the active page
list_res = await service.invoke_webmcp_tool(tool_name="__list__")
print(list_res.available_tools)

# Invoke a specific WebMCP tool
tool_res = await service.invoke_webmcp_tool(
    tool_name="get_product_details",
    arguments={"product_id": "prod_12345"},
)
print(tool_res.output)
```
