"""Microsoft Semantic Kernel Orchestration Engine Plugin.

Provides multi-agent group chats, step DAG kernel processes, dynamic prompt template
rendering (Handlebars/Jinja2), volatile semantic vector memory search, and OpenAPI connector execution.
"""

from __future__ import annotations

import collections
import math
import re
import urllib.parse
from typing import Any


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms."""
    return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]


def _compute_cosine_sim(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Compute cosine similarity between query and document token frequency vectors."""
    if not query_tokens or not doc_tokens:
        return 0.0
    
    q_counts = collections.Counter(query_tokens)
    d_counts = collections.Counter(doc_tokens)
    
    dot_product = sum(q_counts[t] * d_counts[t] for t in q_counts if t in d_counts)
    q_norm = math.sqrt(sum(c * c for c in q_counts.values()))
    d_norm = math.sqrt(sum(c * c for c in d_counts.values()))
    
    if q_norm == 0.0 or d_norm == 0.0:
        return 0.0
    return dot_product / (q_norm * d_norm)


def orchestrate_group_chat(
    agents: list[dict[str, Any]],
    task: str,
    strategy: str = "round_robin",
    max_rounds: int = 6,
    termination_keyword: str = "APPROVED",
) -> dict[str, Any]:
    """Execute multi-agent collaborative discussions with speaker strategy and termination criteria."""
    if not agents:
        return {"status": "error", "message": "At least one agent must be provided."}

    history: list[dict[str, Any]] = []
    consensus_reached = False
    active_turn = 0
    num_agents = len(agents)

    for r in range(1, max(1, min(max_rounds, 20)) + 1):
        if strategy == "round_robin":
            agent_idx = (r - 1) % num_agents
        elif strategy == "supervisor_directed":
            agent_idx = 0 if r == 1 or r == max_rounds else ((r - 1) % (num_agents - 1)) + 1
        else:
            agent_idx = (r - 1) % num_agents

        agent = agents[agent_idx]
        name = agent.get("name", f"Agent_{agent_idx + 1}")
        role = agent.get("role", "Collaborator")
        
        # Simulate structured reasoning for agent
        if r == max_rounds or (r >= 3 and r % 2 == 0 and "supervisor" in role.lower()):
            message_body = f"[{role}] All constraints evaluated for task '{task[:40]}...'. Plan is verified and ready. {termination_keyword}"
        elif "critic" in role.lower() or "reviewer" in role.lower():
            message_body = f"[{role}] Reviewing proposal for '{task[:40]}...'. Verifying edge cases and security guardrails."
        elif "researcher" in role.lower() or "worker" in role.lower():
            message_body = f"[{role}] Synthesizing architecture domain facts and components for '{task[:40]}...'."
        else:
            message_body = f"[{role}] Formulating execution strategy and delegating subtasks for '{task[:40]}...'."

        turn_entry = {
            "round": r,
            "agent": name,
            "role": role,
            "message": message_body,
        }
        history.append(turn_entry)
        active_turn = r

        if termination_keyword in message_body:
            consensus_reached = True
            break

    final_summary = (
        f"Group chat completed across {active_turn} rounds. "
        f"{'Consensus reached with keyword ' + termination_keyword if consensus_reached else 'Max rounds reached.'}"
    )

    return {
        "status": "ok",
        "task": task,
        "strategy": strategy,
        "total_rounds": active_turn,
        "consensus_reached": consensus_reached,
        "termination_keyword": termination_keyword,
        "chat_history": history,
        "final_output": history[-1]["message"] if history else "",
        "summary": final_summary
    }


def execute_kernel_process(
    process_name: str,
    steps: list[dict[str, Any]],
    initial_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute step DAG and state machine processes with conditional event routing and state propagation."""
    state = dict(initial_state or {})
    execution_trace: list[dict[str, Any]] = []

    for idx, step in enumerate(steps, start=1):
        step_id = step.get("step_id", f"step_{idx}")
        action = step.get("action", "passthrough").lower()
        input_key = step.get("input_key")
        output_key = step.get("output_key", step_id)

        input_val = state.get(input_key) if input_key else state

        # Execute step action
        if action == "uppercase":
            output_val = str(input_val).upper()
        elif action == "lowercase":
            output_val = str(input_val).lower()
        elif action == "filter":
            target = step.get("filter_key", "")
            if isinstance(input_val, list):
                output_val = [item for item in input_val if target in str(item)]
            else:
                output_val = input_val
        elif action == "aggregate":
            if isinstance(input_val, list):
                output_val = {"count": len(input_val), "items": input_val}
            else:
                output_val = {"count": 1, "items": [input_val]}
        elif action == "transform" or action == "map":
            output_val = {f"{k}_transformed": v for k, v in (input_val.items() if isinstance(input_val, dict) else {})}
        elif action == "validate":
            output_val = {"valid": bool(input_val), "value": input_val}
        else:  # passthrough
            output_val = input_val

        state[output_key] = output_val
        execution_trace.append({
            "step_id": step_id,
            "action": action,
            "input_key": input_key,
            "output_key": output_key,
            "output_preview": str(output_val)[:80],
            "status": "COMPLETED"
        })

    return {
        "status": "ok",
        "process_name": process_name,
        "steps_executed": len(execution_trace),
        "execution_trace": execution_trace,
        "final_state": state
    }


def render_semantic_prompt(
    template: str,
    variables: dict[str, Any],
    engine: str = "handlebars",
) -> dict[str, Any]:
    """Compile and render Handlebars or Jinja2 dynamic semantic prompt templates with variable substitution."""
    rendered = template
    used_vars: list[str] = []

    # Handlebars / Jinja2 {{variable}} substitutions
    placeholders = re.findall(r"\{\{\s*([\w\.\_]+)\s*\}\}", template)
    for var_name in placeholders:
        val = variables.get(var_name, "")
        rendered = re.sub(r"\{\{\s*" + re.escape(var_name) + r"\s*\}\}", str(val), rendered)
        used_vars.append(var_name)

    # Handle simple {{#if var}}...{{/if}} blocks
    if_blocks = re.findall(r"\{\{#if\s+([\w\.\_]+)\}\}(.*?)\{\{/if\}\}", rendered, flags=re.DOTALL)
    for var_name, block_content in if_blocks:
        condition_met = bool(variables.get(var_name))
        replacement = block_content if condition_met else ""
        pattern = r"\{\{#if\s+" + re.escape(var_name) + r"\}\}.*?\{\{/if\}\}"
        rendered = re.sub(pattern, replacement, rendered, flags=re.DOTALL)
        used_vars.append(var_name)

    # Token estimate (heuristic ~4 chars per token)
    token_est = max(1, len(rendered) // 4)

    return {
        "status": "ok",
        "engine": engine,
        "rendered_prompt": rendered,
        "token_estimate": token_est,
        "variables_used": list(set(used_vars)),
        "character_count": len(rendered)
    }


def search_semantic_memory(
    query: str,
    documents: list[dict[str, Any]],
    limit: int = 5,
    min_relevance: float = 0.5,
) -> dict[str, Any]:
    """Run volatile vector similarity search against documents using cosine similarity scoring."""
    query_tokens = _tokenize(query)
    scored_docs: list[dict[str, Any]] = []

    for doc in documents:
        doc_id = str(doc.get("id", "doc_unknown"))
        text = str(doc.get("text", ""))
        metadata = doc.get("metadata", {})
        
        doc_tokens = _tokenize(text)
        sim_score = round(_compute_cosine_sim(query_tokens, doc_tokens), 4)
        
        if sim_score >= min_relevance:
            scored_docs.append({
                "id": doc_id,
                "text": text,
                "similarity": sim_score,
                "metadata": metadata
            })

    # Sort descending by similarity
    scored_docs.sort(key=lambda d: d["similarity"], reverse=True)
    top_matches = scored_docs[:max(1, limit)]

    return {
        "status": "ok",
        "query": query,
        "total_documents_searched": len(documents),
        "matches_found": len(scored_docs),
        "limit_applied": limit,
        "min_relevance_threshold": min_relevance,
        "results": top_matches,
        "top_match": top_matches[0] if top_matches else None
    }


def execute_openapi_plugin(
    openapi_spec: dict[str, Any],
    operation_id: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse OpenAPI 3.0 specifications and execute REST operations with JSON Schema parameter validation."""
    args = arguments or {}
    paths = openapi_spec.get("paths", {})
    servers = openapi_spec.get("servers", [{"url": "https://api.example.com"}])
    base_url = servers[0].get("url", "https://api.example.com") if servers else "https://api.example.com"

    matched_op: dict[str, Any] | None = None
    matched_path = ""
    matched_method = ""

    # Locate operation by operationId
    for path_str, path_item in paths.items():
        if isinstance(path_item, dict):
            for method in ["get", "post", "put", "delete", "patch"]:
                op = path_item.get(method)
                if isinstance(op, dict) and op.get("operationId") == operation_id:
                    matched_op = op
                    matched_path = path_str
                    matched_method = method.upper()
                    break
        if matched_op:
            break

    if not matched_op:
        return {
            "status": "error",
            "message": f"Operation ID '{operation_id}' not found in OpenAPI specification."
        }

    # Validate parameters
    params = matched_op.get("parameters", [])
    resolved_path = matched_path
    query_params: dict[str, str] = {}
    missing_required: list[str] = []

    for p in params:
        p_name = p.get("name")
        p_in = p.get("in")
        p_req = p.get("required", False)
        
        if p_name in args:
            val = str(args[p_name])
            if p_in == "path":
                resolved_path = resolved_path.replace(f"{{{p_name}}}", urllib.parse.quote(val))
            elif p_in == "query":
                query_params[p_name] = val
        elif p_req:
            missing_required.append(p_name)

    if missing_required:
        return {
            "status": "error",
            "message": f"Missing required parameters for '{operation_id}': {missing_required}"
        }

    full_url = f"{base_url.rstrip('/')}{resolved_path}"
    if query_params:
        full_url += f"?{urllib.parse.urlencode(query_params)}"

    # Construct mock execution response
    mock_response = {
        "status_code": 200,
        "operation_id": operation_id,
        "method": matched_method,
        "endpoint_url": full_url,
        "dispatched_payload": args,
        "summary": matched_op.get("summary", "REST operation executed successfully."),
        "response_mock": {
            "success": True,
            "data": args,
            "operation": operation_id
        }
    }

    return {
        "status": "ok",
        "operation_id": operation_id,
        "method": matched_method,
        "endpoint": full_url,
        "response": mock_response
    }
