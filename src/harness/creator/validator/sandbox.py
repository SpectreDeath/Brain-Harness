"""Runtime sandbox dry-run rule executing tool invocations via isolated executor."""

from __future__ import annotations

import asyncio

from harness.creator.validator.base import ValidationRule
from harness.creator.validator.models import RuleSeverity, ValidationContext
from harness.plugins.sandbox import SandboxExecutorFactory


class SandboxDryRunRule(ValidationRule):
    """Optionally boots the sandbox executor and tests tool invocation over JSON-RPC."""

    @property
    def name(self) -> str:
        return "Sandbox Dry-Run"

    @property
    def category(self) -> str:
        return "runtime"

    async def validate(self, ctx: ValidationContext) -> bool:
        if not ctx.dry_run or not ctx.report.valid or not ctx.manifest or not ctx.manifest.entrypoints:
            return True

        try:
            executor = SandboxExecutorFactory.create(ctx.manifest, ctx.path)
            if executor is None:
                ctx.add_warn(self.name, "Skipped (no executor available for dry-run)", category=self.category)
                return True

            await executor.start()
            try:
                first_ep = ctx.manifest.entrypoints[0]
                res = await executor.execute(first_ep.name, {"task": "validator-dry-run"}, timeout=ctx.timeout)
                if res.get("status") == "error":
                    ctx.add_fail(
                        self.name,
                        f"Sandbox execution failed for '{first_ep.name}': {res.get('error')}",
                        severity=RuleSeverity.ERROR,
                        details=res,
                        category=self.category,
                    )
                    return False
                ctx.add_pass(
                    self.name,
                    f"Successfully executed '{first_ep.name}' in sandbox",
                    details=res,
                    category=self.category,
                )
                return True
            finally:
                await executor.stop()
                await asyncio.sleep(0.01)
        except Exception as e:
            ctx.add_fail(self.name, f"Sandbox dry-run error: {e}", severity=RuleSeverity.ERROR, category=self.category)
            return False
