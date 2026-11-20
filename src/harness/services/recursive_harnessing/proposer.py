"""Live LLM-backed `HarnessProposer` implementation (Step 2, Rules 12, 19)."""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext
from harness.services.llm import LLM_SERVICE_KEY, LLMMessage, LLMService
from harness.services.recursive_harnessing import guards, surface as surface_ops
from harness.services.recursive_harnessing.errors import ProposerError
from harness.services.recursive_harnessing.models import BRAIN_SURFACE, ProposalReply, SurfaceSpec, Tree

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)
_SYSTEM_PROMPT = (
    "You are an autonomous harness editor. Edit only files on the declared editable surface. "
    'Return ONLY a JSON object: {"notes": "<short rationale>", '
    '"files": {"<relative/path>": "<full file text>"}, "delete": ["<relative/path>"]}.'
)


def _extract_json_payload(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ProposerError("LiveHarnessProposer received an empty model reply")
    if match := _FENCE_RE.search(text):
        text = match.group(1).strip()
    elif "{" in text and "}" in text:
        text = text[text.find("{") : text.rfind("}") + 1]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProposerError(f"LiveHarnessProposer could not parse JSON reply: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ProposerError("LiveHarnessProposer expected a JSON object reply")
    return parsed


def _run_coro_sync(coro: Awaitable[Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class LiveHarnessProposer:
    """Live LLM-backed `HarnessProposer` editing `<evidence_root>/harness` in place."""

    def __init__(
        self,
        llm: LLMService | None = None,
        *,
        context: ServiceContext | None = None,
        complete_fn: Callable[[list[LLMMessage]], Any] | None = None,
        surface: SurfaceSpec = BRAIN_SURFACE,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> None:
        self._llm = llm
        self._context = context
        self._complete_fn = complete_fn
        self._surface = surface
        self._model = model
        self._max_tokens = max_tokens

    def _resolve_completion(self, messages: list[LLMMessage]) -> tuple[str, float]:
        if self._complete_fn is not None:
            raw = self._complete_fn(messages)
            if inspect.isawaitable(raw):
                raw = _run_coro_sync(raw)
            content = getattr(raw, "content", raw)
            return str(content), 0.0
        llm = self._llm
        if llm is None and self._context is not None:
            llm = self._context.optional(LLM_SERVICE_KEY)
        if llm is None:
            raise ProposerError(
                "LiveHarnessProposer requires an LLMService, context with LLM_SERVICE_KEY, or complete_fn"
            )
        resp = _run_coro_sync(llm.complete(messages, model=self._model, max_tokens=self._max_tokens, temperature=0.2))
        usage = getattr(resp, "usage", None) or {}
        est_cost = float(usage.get("total_tokens", 0)) * 1e-6
        return str(getattr(resp, "content", "")), est_cost

    def propose(self, mission: str, evidence_root: Path, label: str) -> ProposalReply:
        """Edit `<evidence_root>/harness` in place from LLM output, enforcing surface & isolation guards."""
        root = Path(evidence_root)
        try:
            guards.assert_no_verdicts(root)
        except Exception as exc:
            raise ProposerError(f"Evidence isolation guard failed for '{label}': {exc}") from exc

        harness_dir = root / "harness"
        harness_dir.mkdir(parents=True, exist_ok=True)
        cur_tree = surface_ops.read_tree(self._surface, harness_dir)
        messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(
                role="user",
                content=(
                    f"Label: {label}\n"
                    f"Editable surface: always_on={self._surface.always_on}, "
                    f"skills={self._surface.skill_dir}/<name>/SKILL.md, "
                    f"subagents={self._surface.subagent_dir}/<name>/AGENT.md, "
                    f"scripts={self._surface.scripts_dir}/<name>.py\n\n"
                    f"Current tree files: {json.dumps(cur_tree, sort_keys=True)}\n\n"
                    f"Mission:\n{mission}"
                ),
            ),
        ]
        try:
            raw_text, cost_usd = self._resolve_completion(messages)
        except ProposerError:
            raise
        except Exception as exc:
            raise ProposerError(f"LiveHarnessProposer completion failed for '{label}': {exc}") from exc

        payload = _extract_json_payload(raw_text)
        files = payload.get("files") or {}
        deletes = payload.get("delete") or []
        if not isinstance(files, dict) or not isinstance(deletes, list):
            raise ProposerError("LiveHarnessProposer JSON 'files' must be an object and 'delete' a list")

        next_tree: Tree = dict(cur_tree)
        try:
            for rel in deletes:
                norm = surface_ops.normalize_rel(str(rel))
                if not surface_ops.is_allowed(self._surface, norm):
                    raise ProposerError(f"Proposer attempted off-surface deletion: {rel!r}")
                next_tree.pop(norm, None)
            for rel, body in files.items():
                norm = surface_ops.normalize_rel(str(rel))
                if not surface_ops.is_allowed(self._surface, norm):
                    raise ProposerError(f"Proposer attempted off-surface write: {rel!r}")
                if not isinstance(body, str):
                    raise ProposerError(f"Proposer file content for {norm!r} must be a string")
                next_tree[norm] = body
        except ValueError as exc:
            raise ProposerError(f"Proposer path validation failed: {exc}") from exc

        try:
            guards.assert_tree_clean(next_tree)
        except Exception as exc:
            raise ProposerError(f"Proposed tree failed leak guard: {exc}") from exc

        for rel in cur_tree:
            if rel not in next_tree and (harness_dir / rel).is_file():
                (harness_dir / rel).unlink()
        surface_ops.write_tree(self._surface, next_tree, harness_dir)
        notes = str(payload.get("notes") or f"updated {len(files)} file(s) via LiveHarnessProposer").strip()
        return ProposalReply(text=f"<notes>{notes}</notes>", workspace=harness_dir, cost_usd=cost_usd)

    def propose_tree_from_description(
        self,
        description: str,
        work_dir: Path | str,
        *,
        base_tree: Mapping[str, str] | None = None,
        label: str = "spawn_propose",
    ) -> tuple[Tree, ProposalReply]:
        """Generate and validate a child harness tree from a natural-language description."""
        root = Path(work_dir)
        harness_dir = root / "harness"
        seed = dict(base_tree) if base_tree is not None else {"AGENTS.md": f"# Child Harness\n\n{description}\n"}
        surface_ops.write_tree(self._surface, seed, harness_dir)
        reply = self.propose(description, root, label)
        proposed_tree = surface_ops.read_tree(self._surface, harness_dir)
        try:
            guards.assert_tree_clean(proposed_tree)
            surface_ops.validate(self._surface, proposed_tree)
        except Exception as exc:
            raise ProposerError(f"Proposed harness tree failed validation: {exc}") from exc
        return proposed_tree, reply


__all__ = ["LiveHarnessProposer"]
