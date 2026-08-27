"""Unit tests for domain.semantic_kernel_engine plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.semantic_kernel_engine.main import (
    execute_kernel_process,
    execute_openapi_plugin,
    orchestrate_group_chat,
    render_semantic_prompt,
    search_semantic_memory,
)


@pytest.mark.unit
class TestSemanticKernelEnginePlugin:
    def test_orchestrate_group_chat(self) -> None:
        agents = [
            {"name": "Supervisor", "role": "Supervisor", "instructions": "Coordinate and verify"},
            {"name": "Researcher", "role": "Domain Researcher", "instructions": "Extract knowledge"},
            {"name": "Critic", "role": "Security Critic", "instructions": "Review edge cases"},
        ]
        res = orchestrate_group_chat(
            agents=agents,
            task="Design a resilient caching layer",
            strategy="round_robin",
            max_rounds=4,
            termination_keyword="APPROVED",
        )
        assert res["status"] == "ok"
        assert res["total_rounds"] >= 1
        assert len(res["chat_history"]) >= 1
        assert "final_output" in res

    def test_execute_kernel_process(self) -> None:
        steps = [
            {"step_id": "step_1", "action": "uppercase", "input_key": "raw_input", "output_key": "upper_text"},
            {"step_id": "step_2", "action": "validate", "input_key": "upper_text", "output_key": "validation_res"},
        ]
        initial_state = {"raw_input": "hello semantic kernel"}
        res = execute_kernel_process("text_pipeline", steps, initial_state)
        assert res["status"] == "ok"
        assert res["steps_executed"] == 2
        assert res["final_state"]["upper_text"] == "HELLO SEMANTIC KERNEL"
        assert res["final_state"]["validation_res"]["valid"] is True

    def test_render_semantic_prompt(self) -> None:
        template = "Hello {{user_name}}, welcome to {{project_name}}! {{#if is_admin}}Admin Mode Enabled.{{/if}}"
        variables = {"user_name": "Spectre", "project_name": "Brain Harness", "is_admin": True}
        res = render_semantic_prompt(template, variables)
        assert res["status"] == "ok"
        assert "Spectre" in res["rendered_prompt"]
        assert "Brain Harness" in res["rendered_prompt"]
        assert "Admin Mode Enabled." in res["rendered_prompt"]

    def test_search_semantic_memory(self) -> None:
        documents = [
            {"id": "doc1", "text": "Micro-kernel plugin architecture with dependency injection."},
            {"id": "doc2", "text": "Database indexing and relational query optimization."},
            {"id": "doc3", "text": "Frontend UI components and CSS glassmorphism styles."},
        ]
        res = search_semantic_memory(
            query="micro-kernel plugins and architecture",
            documents=documents,
            limit=2,
            min_relevance=0.2,
        )
        assert res["status"] == "ok"
        assert len(res["results"]) > 0
        assert res["top_match"]["id"] == "doc1"

    def test_execute_openapi_plugin(self) -> None:
        spec = {
            "openapi": "3.0.0",
            "servers": [{"url": "https://api.harness.local/v1"}],
            "paths": {
                "/users/{userId}": {
                    "get": {
                        "operationId": "getUserById",
                        "summary": "Retrieve user profile by ID",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True},
                            {"name": "include_roles", "in": "query", "required": False},
                        ],
                    }
                }
            },
        }
        res = execute_openapi_plugin(
            openapi_spec=spec,
            operation_id="getUserById",
            arguments={"userId": "usr_42", "include_roles": "true"},
        )
        assert res["status"] == "ok"
        assert res["method"] == "GET"
        assert "https://api.harness.local/v1/users/usr_42" in res["endpoint"]
        assert res["response"]["status_code"] == 200
