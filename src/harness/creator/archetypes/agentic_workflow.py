"""Autonomous agent workflow plugin archetype with multi-step plan/act/eval loops."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from harness.creator.archetypes.base import PluginArchetype
from harness.plugins.manifest import (
    EntrypointSpec,
    ParameterSpec,
    PluginManifest,
)

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldOptions


class AgenticWorkflowArchetype(PluginArchetype):
    """Autonomous agent workflow with multi-step plan, act, and evaluate loops."""

    @property
    def name(self) -> str:
        return "agentic_workflow"

    @property
    def description(self) -> str:
        return "Autonomous agent workflow loop with multi-step planning and evaluation hooks"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        desc = options.description or f"Agentic workflow engine for {options.name}"

        entrypoints = [
            EntrypointSpec(
                name="plan",
                description="Formulate an execution plan for a goal",
                parameters=[
                    ParameterSpec(name="goal", type="string", description="High-level goal or task", required=True),
                ],
                returns="dict",
            ),
            EntrypointSpec(
                name="execute_step",
                description="Execute an individual planned action step",
                parameters=[
                    ParameterSpec(name="step", type="string", description="Step action to execute", required=True),
                    ParameterSpec(name="context", type="object", description="Context data", required=False, default={}),
                ],
                returns="dict",
            ),
            EntrypointSpec(
                name="evaluate",
                description="Evaluate outcome against expected termination criteria",
                parameters=[
                    ParameterSpec(name="result", type="object", description="Execution result payload", required=True),
                ],
                returns="dict",
            ),
        ]

        cat = options.category if options.category and options.category != "general" else "agent"
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=desc,
            language=options.language,
            entrypoint=entrypoint,
            isolation=options.isolation,
            author=options.author,
            category=cat,
            tags=["agent", "workflow", "autonomous", "planning"],
            provides=[f"workflow.{options.name}"],
            requires=list(options.requires),
            entrypoints=entrypoints,
            dependencies=list(options.dependencies),
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        if lang == "python":
            return (
                f'"""Agentic Workflow engine for {options.name}.\n\n'
                f'{options.description or f"Implements autonomous agent workflow logic for {options.name}."}\n'
                f'"""\n\n'
                f'from __future__ import annotations\n'
                f'from typing import Any\n\n\n'
                f'def plan(goal: str = "", **kwargs: Any) -> dict[str, Any]:\n'
                f'    """Formulate multi-step action plan for goal."""\n'
                f'    steps = [\n'
                f'        f"1. Analyze requirements for: {{goal}}",\n'
                f'        f"2. Execute core operations",\n'
                f'        f"3. Verify and synthesize results",\n'
                f'    ]\n'
                f'    return {{"status": "ok", "action": "plan", "goal": goal, "steps": steps, "extra": kwargs}}\n\n\n'
                f'def execute_step(step: str = "", context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:\n'
                f'    """Execute an individual step action."""\n'
                f'    ctx = context or {{}}\n'
                f'    return {{"status": "ok", "action": "execute_step", "step": step, "output": f"Completed: {{step}}", "context": ctx}}\n\n\n'
                f'def evaluate(result: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:\n'
                f'    """Evaluate results against completion criteria."""\n'
                f'    res = result or {{}}\n'
                f'    is_success = res.get("status") == "ok"\n'
                f'    return {{"status": "ok", "action": "evaluate", "passed": is_success, "score": 1.0 if is_success else 0.0}}\n\n\n'
                f'if __name__ == "__main__":\n'
                f'    import json\n'
                f'    p = plan("Sample Agent Task")\n'
                f'    print(json.dumps(p, indent=2))\n'
            )

        return (
            f"/**\n"
            f" * Agentic Workflow engine for {options.name}\n"
            f" */\n\n"
            f"export async function plan(goal = '', kwargs = {{}}) {{\n"
            f"  const steps = [\n"
            f"    `1. Analyze requirements for: ${{goal}}`,\n"
            f"    `2. Execute core operations`,\n"
            f"    `3. Verify and synthesize results`,\n"
            f"  ];\n"
            f"  return {{ status: 'ok', action: 'plan', goal, steps, extra: kwargs }};\n"
            f"}}\n\n"
            f"export async function execute_step(step = '', context = {{}}, kwargs = {{}}) {{\n"
            f"  return {{ status: 'ok', action: 'execute_step', step, output: `Completed: ${{step}}`, context, extra: kwargs }};\n"
            f"}}\n\n"
            f"export async function evaluate(result = {{}}, kwargs = {{}}) {{\n"
            f"  const passed = result.status === 'ok';\n"
            f"  return {{ status: 'ok', action: 'evaluate', passed, score: passed ? 1.0 : 0.0, extra: kwargs }};\n"
            f"}}\n"
        )

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        if lang == "python":
            return (
                f'"""Unit tests for {options.name} agentic workflow."""\n\n'
                f'from main import plan, execute_step, evaluate\n\n\n'
                f'def test_workflow_lifecycle():\n'
                f'    plan_res = plan("Test Goal")\n'
                f'    assert plan_res["status"] == "ok"\n'
                f'    assert len(plan_res["steps"]) == 3\n\n'
                f'    step_res = execute_step(plan_res["steps"][0])\n'
                f'    assert step_res["status"] == "ok"\n'
                f'    assert "Completed:" in step_res["output"]\n\n'
                f'    eval_res = evaluate(step_res)\n'
                f'    assert eval_res["status"] == "ok"\n'
                f'    assert eval_res["passed"] is True\n'
            )

        return (
            f'// Unit tests for {options.name}\n'
            f'import {{ plan, execute_step, evaluate }} from "./index.js";\n\n'
            f'test("workflow lifecycle", async () => {{\n'
            f'  const planRes = await plan("Test Goal");\n'
            f'  expect(planRes.status).toBe("ok");\n'
            f'  expect(planRes.steps.length).toBe(3);\n\n'
            f'  const stepRes = await execute_step(planRes.steps[0]);\n'
            f'  expect(stepRes.status).toBe("ok");\n\n'
            f'  const evalRes = await evaluate(stepRes);\n'
            f'  expect(evalRes.status).toBe("ok");\n'
            f'  expect(evalRes.passed).toBe(true);\n'
            f'}});\n'
        )

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        lang = options.language.lower()
        if lang == "python":
            return "requirements.txt", "# Agent workflow dependencies\n"
        pkg = {
            "name": options.name,
            "version": options.version,
            "description": options.description,
            "main": "index.ts" if lang == "typescript" else "index.js",
            "type": "module",
            "dependencies": {dep: "*" for dep in options.dependencies},
        }
        return "package.json", json.dumps(pkg, indent=2)

    def generate_extra_files(self, options: ScaffoldOptions) -> dict[str, str]:
        readme = (
            f"# {options.name}\n\n"
            f"{options.description or 'Autonomous Agent Workflow Plugin'}\n\n"
            f"## Workflow Stages\n"
            f"- `plan(goal)`: Generates actionable steps\n"
            f"- `execute_step(step, context)`: Dispatches step execution\n"
            f"- `evaluate(result)`: Analyzes step outputs and completion\n"
        )
        return {
            "README.md": readme,
            ".gitignore": "__pycache__/\n*.pyc\n.pytest_cache/\nnode_modules/\n",
        }


__all__ = [
    "AgenticWorkflowArchetype",
]
