"""TypeScript Agent Harness Constructor & Validation Engine.

Slotted and frozen domain architecture implementing the 6-stage construction progression,
atomic batch budget invariants, workspace confinement validation, context windowing,
and deterministic PRNG testing derived from Gabor Koos (freeCodeCamp, 2026).
"""

from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ErrorBifurcationMode(str, Enum):
    """Bifurcated error handling modes."""

    TOOL_RECOVERABLE = "tool_recoverable"
    MODEL_TERMINAL = "model_terminal"


class BudgetVerdictStatus(str, Enum):
    """Outcome status of atomic tool batch budget verification."""

    ADMITTED = "admitted"
    TOOL_LIMIT = "tool_limit"


# ---------------------------------------------------------------------------
# 1. Slotted & Frozen Dataclass Domain Models (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class HarnessBudgetConfig:
    """Mathematical operational budgets and execution thresholds."""

    max_steps: int = 25
    max_tool_calls: int = 75
    max_context_chars: int = 80000
    command_timeout_ms: int = 10000
    max_command_output_bytes: int = 65536

    def __post_init__(self) -> None:
        assert self.max_steps > 0, "max_steps must be a positive integer"
        assert self.max_tool_calls > 0, "max_tool_calls must be a positive integer"
        assert self.max_context_chars > 0, "max_context_chars must be a positive integer"
        assert self.command_timeout_ms > 0, "command_timeout_ms must be a positive integer"
        assert self.max_command_output_bytes > 0, "max_command_output_bytes must be a positive integer"


@dataclass(slots=True, frozen=True)
class ToolContractDefinition:
    """Immutable contract specification for an agent tool."""

    name: str
    schema: dict[str, Any]
    description: str = ""
    error_mode: ErrorBifurcationMode = ErrorBifurcationMode.TOOL_RECOVERABLE

    def __post_init__(self) -> None:
        assert re.match(
            r"^[a-zA-Z][a-zA-Z0-9_-]*$", self.name
        ), f"Invalid tool name '{self.name}': must match ^[a-zA-Z][a-zA-Z0-9_-]*$"
        assert isinstance(self.schema, dict), "schema must be a dictionary"

    def validate_args(self, args: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate input arguments against declared schema subset."""
        if not isinstance(args, dict):
            return False, f"Expected arguments object, received {type(args).__name__}"

        properties = self.schema.get("properties") or {}
        required = self.schema.get("required") or []
        additional = self.schema.get("additionalProperties", True)

        # Check required fields
        for req in required:
            if req not in args:
                return False, f"Missing required property: $.{req}"

        # Check unknown properties
        if additional is False:
            for key in args:
                if key not in properties:
                    return False, f"Unexpected additional property: $.{key}"

        # Check types and enums
        for key, val in args.items():
            prop_spec = properties.get(key)
            if not prop_spec:
                continue

            expected_type = prop_spec.get("type")
            if expected_type == "string" and not isinstance(val, str):
                return False, f"Property $.{key} must be a string, got {type(val).__name__}"
            elif expected_type == "integer" and (not isinstance(val, int) or isinstance(val, bool)):
                return False, f"Property $.{key} must be an integer, got {type(val).__name__}"
            elif expected_type == "number" and not isinstance(val, (int, float)):
                return False, f"Property $.{key} must be a number, got {type(val).__name__}"
            elif expected_type == "boolean" and not isinstance(val, bool):
                return False, f"Property $.{key} must be a boolean, got {type(val).__name__}"
            elif expected_type == "array" and not isinstance(val, list):
                return False, f"Property $.{key} must be an array, got {type(val).__name__}"

            if "enum" in prop_spec and val not in prop_spec["enum"]:
                return False, f"Property $.{key} value '{val}' not in allowed enum {prop_spec['enum']}"

        return True, None


@dataclass(slots=True, frozen=True)
class CommandPresetDefinition:
    """Hardened non-shell command preset."""

    name: str
    executable: str
    args: tuple[str, ...] = field(default_factory=tuple)
    timeout_ms: int = 10000
    shell: bool = False

    def __post_init__(self) -> None:
        assert self.shell is False, "Hardened command presets must strictly specify shell=False"
        assert self.name.strip(), "Command preset name cannot be empty"
        assert self.executable.strip(), "Command preset executable cannot be empty"
        assert self.timeout_ms > 0, "timeout_ms must be positive"


@dataclass(slots=True, frozen=True)
class WorkspaceSandboxPolicy:
    """Path confinement and intermediate symlink rejection policy."""

    root: Path
    allow_ancestor_symlinks: bool = False
    enforce_o_nofollow: bool = True

    def __post_init__(self) -> None:
        assert isinstance(self.root, Path), "root must be a Path object"

    def validate_path(self, target: str | Path) -> tuple[bool, str | None]:
        """Validate path confinement and assert zero ancestor symlinks."""
        try:
            canonical_root = self.root.resolve()
            resolved_target = (canonical_root / target).resolve()

            # 1. Lexical boundary containment
            rel = os.path.relpath(resolved_target, canonical_root)
            if rel == ".." or rel.startswith(".." + os.sep) or resolved_target == canonical_root:
                return False, f"Path traversal escape detected: '{target}' resolves outside workspace"

            # 2. Ancestor symlink check
            if not self.allow_ancestor_symlinks:
                curr = resolved_target.parent
                while curr != canonical_root and curr != curr.parent:
                    if curr.is_symlink():
                        return False, f"Ancestor directory is a symbolic link: '{curr}'"
                    curr = curr.parent

            return True, None
        except Exception as exc:
            return False, f"Path resolution error: {exc}"


@dataclass(slots=True, frozen=True)
class BatchBudgetVerdict:
    """Verdict of an atomic tool batch budget verification."""

    batch_size: int
    remaining_budget: int
    admitted: bool
    unanswered_calls_count: int = 0
    status: BudgetVerdictStatus = BudgetVerdictStatus.ADMITTED

    def __post_init__(self) -> None:
        assert self.batch_size >= 0, "batch_size cannot be negative"
        assert self.remaining_budget >= 0, "remaining_budget cannot be negative"


@dataclass(slots=True, frozen=True)
class ContextTurnGroup:
    """Atomic turn group preserving assistant tool calls and corresponding results."""

    turn_type: str
    messages: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    total_chars: int = 0

    def __post_init__(self) -> None:
        assert self.turn_type in ("prompt", "turn", "answer"), f"Invalid turn_type: {self.turn_type}"


@dataclass(slots=True, frozen=True)
class ContextWindowPlan:
    """Result of context window sliding allocation."""

    budget_chars: int
    retained_groups: tuple[ContextTurnGroup, ...] = field(default_factory=tuple)
    total_retained_chars: int = 0
    dropped_groups_count: int = 0

    def __post_init__(self) -> None:
        assert self.budget_chars > 0, "budget_chars must be positive"


@dataclass(slots=True, frozen=True)
class ObserverDispatchResult:
    """Isolated telemetry event dispatch outcome."""

    event_name: str
    dispatched: bool
    listener_exception: str | None = None
    is_suppressed: bool = True


@dataclass(slots=True, frozen=True)
class DiagnosticAuditReport:
    """Comprehensive compliance evaluation against the 9 diagnostic seam gates."""

    target_path: str
    passed_count: int
    total_count: int
    is_compliant: bool
    checks: tuple[dict[str, Any], ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# 2. Domain Engines & Simulators
# ---------------------------------------------------------------------------


class AtomicBudgetEvaluator:
    """Evaluates multi-call tool batches atomically before transcript mutation."""

    @staticmethod
    def evaluate_batch(
        batch_size: int,
        cumulative_calls: int,
        max_tool_calls: int,
    ) -> BatchBudgetVerdict:
        """Verify that the entire tool batch fits within remaining budget."""
        remaining = max(0, max_tool_calls - cumulative_calls)
        if batch_size <= remaining:
            return BatchBudgetVerdict(
                batch_size=batch_size,
                remaining_budget=remaining - batch_size,
                admitted=True,
                unanswered_calls_count=0,
                status=BudgetVerdictStatus.ADMITTED,
            )
        # Rejected atomically: 0 calls executed, 0 unanswered calls in transcript
        return BatchBudgetVerdict(
            batch_size=batch_size,
            remaining_budget=remaining,
            admitted=False,
            unanswered_calls_count=0,
            status=BudgetVerdictStatus.TOOL_LIMIT,
        )


class ContextWindowManager:
    """Manages sliding context windowing preserving turn atomicity."""

    @staticmethod
    def calculate_message_chars(msg: dict[str, Any]) -> int:
        """Calculate character footprint of a message."""
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []
        return len(str(content)) + len(json.dumps(tool_calls))

    @classmethod
    def group_messages(cls, messages: list[dict[str, Any]]) -> list[ContextTurnGroup]:
        """Group messages into atomic units: prompt, turn (assistant+results), or answer."""
        if not messages:
            return []

        groups: list[ContextTurnGroup] = []
        i = 0

        # Group 1: Initial user prompt
        if messages[0].get("role") == "user":
            prompt_msg = messages[0]
            groups.append(
                ContextTurnGroup(
                    turn_type="prompt",
                    messages=(prompt_msg,),
                    total_chars=cls.calculate_message_chars(prompt_msg),
                )
            )
            i = 1

        while i < len(messages):
            msg = messages[i]
            role = msg.get("role")

            if role == "assistant":
                tool_calls = msg.get("tool_calls") or []
                if not tool_calls:
                    # Final assistant answer
                    chars = cls.calculate_message_chars(msg)
                    groups.append(
                        ContextTurnGroup(
                            turn_type="answer",
                            messages=(msg,),
                            total_chars=chars,
                        )
                    )
                    i += 1
                else:
                    # Compound turn: assistant call + subsequent tool results
                    turn_msgs = [msg]
                    call_ids = {c.get("id") for c in tool_calls if c.get("id")}
                    i += 1

                    while i < len(messages) and messages[i].get("role") == "tool":
                        tool_msg = messages[i]
                        tool_call_id = tool_msg.get("tool_call_id")
                        if tool_call_id not in call_ids:
                            raise ValueError(
                                f"Mismatched tool result call ID: {tool_call_id}"
                            )
                        turn_msgs.append(tool_msg)
                        i += 1

                    total_chars = sum(cls.calculate_message_chars(m) for m in turn_msgs)
                    groups.append(
                        ContextTurnGroup(
                            turn_type="turn",
                            messages=tuple(turn_msgs),
                            total_chars=total_chars,
                        )
                    )
            elif role == "tool":
                # Standalone tool result with no preceding assistant turn
                raise ValueError(
                    f"Orphaned tool result detected without preceding assistant call: {msg.get('tool_call_id')}"
                )
            else:
                # Interleaved user message
                chars = cls.calculate_message_chars(msg)
                groups.append(
                    ContextTurnGroup(
                        turn_type="turn",
                        messages=(msg,),
                        total_chars=chars,
                    )
                )
                i += 1

        return groups

    @classmethod
    def select_context(
        cls, messages: list[dict[str, Any]], max_chars: int
    ) -> ContextWindowPlan:
        """Select context respecting character ceiling and atomic turn groups."""
        if max_chars <= 0:
            raise ValueError(f"max_chars budget must be positive, got {max_chars}")

        groups = cls.group_messages(messages)
        if not groups:
            return ContextWindowPlan(budget_chars=max_chars)

        # Always preserve initial user prompt
        prompt_group = groups[0] if groups[0].turn_type == "prompt" else None
        allocated_groups = []
        accumulated_chars = prompt_group.total_chars if prompt_group else 0

        if accumulated_chars > max_chars:
            raise ValueError("Initial user prompt exceeds total max_chars budget")

        subsequent_groups = groups[1:] if prompt_group else groups
        retained_subsequent = []
        dropped_count = 0

        # Walk backward from most recent group
        for grp in reversed(subsequent_groups):
            if accumulated_chars + grp.total_chars <= max_chars:
                retained_subsequent.append(grp)
                accumulated_chars += grp.total_chars
            else:
                dropped_count += 1

        retained_subsequent.reverse()
        if prompt_group:
            allocated_groups.append(prompt_group)
        allocated_groups.extend(retained_subsequent)

        return ContextWindowPlan(
            budget_chars=max_chars,
            retained_groups=tuple(allocated_groups),
            total_retained_chars=accumulated_chars,
            dropped_groups_count=dropped_count,
        )


class PRNGBatchSimulator:
    """Seeded pseudo-random scenario generator validating the atomic batch invariant."""

    @staticmethod
    def run_simulation(
        seed: int = 0x12345678, iterations: int = 150
    ) -> dict[str, Any]:
        """Execute property-based verification over randomized limits and batch sizes."""
        rng = random.Random(seed)
        admitted_runs = 0
        rejected_runs = 0
        zero_orphan_asserted = True

        for _ in range(iterations):
            limit = rng.randint(0, 8)
            batch = rng.randint(0, 12)
            cumulative = rng.randint(0, max(0, limit))

            verdict = AtomicBudgetEvaluator.evaluate_batch(
                batch_size=batch,
                cumulative_calls=cumulative,
                max_tool_calls=limit,
            )

            remaining = max(0, limit - cumulative)
            if batch <= remaining:
                assert verdict.admitted is True
                assert verdict.status == BudgetVerdictStatus.ADMITTED
                admitted_runs += 1
            else:
                assert verdict.admitted is False
                assert verdict.status == BudgetVerdictStatus.TOOL_LIMIT
                rejected_runs += 1

            # Invariant: orphaned/unanswered calls must always be 0
            if verdict.unanswered_calls_count != 0:
                zero_orphan_asserted = False

        return {
            "seed": hex(seed),
            "iterations": iterations,
            "admitted_runs": admitted_runs,
            "rejected_runs": rejected_runs,
            "zero_orphan_asserted": zero_orphan_asserted,
            "success": zero_orphan_asserted,
        }


class TypeScriptHarnessScaffolder:
    """Scaffolds zero-dependency TypeScript agent harness implementation files."""

    @staticmethod
    def scaffold_all(output_dir: Path) -> dict[str, Path]:
        """Scaffold all 7 production-grade TypeScript harness modules."""
        output_dir.mkdir(parents=True, exist_ok=True)
        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        files = {}

        # 1. src/model.ts
        model_ts = """export interface Message {
  role: 'user' | 'assistant' | 'tool';
  content?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  isError?: boolean;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
}

export interface ModelResponse {
  answer?: string;
  tool_calls?: ToolCall[];
  usage?: {
    inputTokens: number;
    outputTokens: number;
  };
}

export interface Model {
  generate(params: {
    messages: Message[];
    tools?: any[];
    signal?: AbortSignal;
  }): Promise<ModelResponse>;
}

export function scriptedModel(responses: ModelResponse[]): Model {
  let index = 0;
  return {
    async generate({ signal }) {
      if (signal?.aborted) throw new Error('Operation aborted');
      if (index >= responses.length) {
        throw new Error('Scripted model exhausted');
      }
      return responses[index++];
    }
  };
}
"""
        files["model.ts"] = src_dir / "model.ts"
        files["model.ts"].write_text(model_ts, encoding="utf-8")

        # 2. src/tools.ts
        tools_ts = """import { Message, ToolCall } from './model';

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, any>;
  execute(args: Record<string, any>, signal?: AbortSignal): Promise<any>;
}

export class ToolRegistry {
  private tools = new Map<string, ToolDefinition>();

  register(tool: ToolDefinition): void {
    if (!/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(tool.name)) {
      throw new Error(`Invalid tool name: ${tool.name}`);
    }
    if (this.tools.has(tool.name)) {
      throw new Error(`Duplicate tool registered: ${tool.name}`);
    }
    this.tools.set(tool.name, tool);
  }

  get(name: string): ToolDefinition | undefined {
    return this.tools.get(name);
  }

  validateArgs(schema: Record<string, any>, args: Record<string, any>): string | null {
    const required = schema.required || [];
    for (const req of required) {
      if (!(req in args)) return `Missing required property: $.${req}`;
    }
    return null;
  }

  async dispatch(call: ToolCall, signal?: AbortSignal): Promise<Message> {
    const tool = this.get(call.name);
    if (!tool) {
      return {
        role: 'tool',
        tool_call_id: call.id,
        content: `Unknown tool: '${call.name}'`,
        isError: true,
      };
    }

    const err = this.validateArgs(tool.parameters, call.arguments);
    if (err) {
      return {
        role: 'tool',
        tool_call_id: call.id,
        content: err,
        isError: true,
      };
    }

    try {
      const output = await tool.execute(call.arguments, signal);
      return {
        role: 'tool',
        tool_call_id: call.id,
        content: typeof output === 'string' ? output : JSON.stringify(output),
        isError: false,
      };
    } catch (e: any) {
      return {
        role: 'tool',
        tool_call_id: call.id,
        content: e.message || String(e),
        isError: true,
      };
    }
  }
}
"""
        files["tools.ts"] = src_dir / "tools.ts"
        files["tools.ts"].write_text(tools_ts, encoding="utf-8")

        # 3. src/workspace.ts
        workspace_ts = """import * as fs from 'fs/promises';
import * as path from 'path';

export interface CommandPreset {
  name: string;
  executable: string;
  args: string[];
  timeoutMs: number;
}

export class Workspace {
  private constructor(public readonly root: string) {}

  static async open(root: string): Promise<Workspace> {
    const canonical = await fs.realpath(root);
    return new Workspace(canonical);
  }

  async resolveSafe(filePath: string): Promise<string> {
    const resolved = path.resolve(this.root, filePath);
    const rel = path.relative(this.root, resolved);
    if (rel === '..' || rel.startsWith(`..${path.sep}`) || resolved === this.root) {
      throw new Error(`Path escape rejected: '${filePath}'`);
    }

    // Walk ancestor directories checking for symlinks
    let curr = path.dirname(resolved);
    while (curr !== this.root && curr !== path.dirname(curr)) {
      const stat = await fs.lstat(curr);
      if (stat.isSymbolicLink()) {
        throw new Error(`Ancestor symlink detected: '${curr}'`);
      }
      curr = path.dirname(curr);
    }

    return resolved;
  }
}
"""
        files["workspace.ts"] = src_dir / "workspace.ts"
        files["workspace.ts"].write_text(workspace_ts, encoding="utf-8")

        # 4. src/budget.ts
        budget_ts = """export interface BudgetConfig {
  maxSteps: number;
  maxToolCalls: number;
}

export class BudgetTracker {
  steps = 0;
  toolCalls = 0;

  constructor(private config: BudgetConfig) {}

  checkSteps(): boolean {
    return this.steps < this.config.maxSteps;
  }

  checkBatch(batchSize: number): boolean {
    return this.toolCalls + batchSize <= this.config.maxToolCalls;
  }

  recordBatch(batchSize: number): void {
    this.toolCalls += batchSize;
  }

  incrementStep(): void {
    this.steps++;
  }
}
"""
        files["budget.ts"] = src_dir / "budget.ts"
        files["budget.ts"].write_text(budget_ts, encoding="utf-8")

        # 5. src/context.ts
        context_ts = """import { Message } from './model';

export function selectContext(messages: Message[], maxChars: number): Message[] {
  if (maxChars <= 0) throw new RangeError('maxChars must be positive');
  if (messages.length === 0) return [];

  const prompt = messages[0];
  let accumulated = JSON.stringify(prompt).length;
  if (accumulated > maxChars) {
    throw new Error('Initial user prompt exceeds maxChars budget');
  }

  const result: Message[] = [prompt];
  const subsequent = messages.slice(1);
  const groups: Message[][] = [];

  let i = 0;
  while (i < subsequent.length) {
    const m = subsequent[i];
    if (m.role === 'assistant' && m.tool_calls && m.tool_calls.length > 0) {
      const turnGroup: Message[] = [m];
      const callIds = new Set(m.tool_calls.map(c => c.id));
      i++;
      while (i < subsequent.length && subsequent[i].role === 'tool') {
        const tm = subsequent[i];
        if (!callIds.has(tm.tool_call_id!)) {
          throw new Error(`Mismatched tool result call ID: ${tm.tool_call_id}`);
        }
        turnGroup.push(tm);
        i++;
      }
      groups.push(turnGroup);
    } else {
      groups.push([m]);
      i++;
    }
  }

  const retainedGroups: Message[][] = [];
  for (let g = groups.length - 1; g >= 0; g--) {
    const grp = groups[g];
    const grpLen = grp.reduce((acc, msg) => acc + JSON.stringify(msg).length, 0);
    if (accumulated + grpLen <= maxChars) {
      retainedGroups.unshift(grp);
      accumulated += grpLen;
    }
  }

  for (const grp of retainedGroups) {
    result.push(...grp);
  }

  return result;
}
"""
        files["context.ts"] = src_dir / "context.ts"
        files["context.ts"].write_text(context_ts, encoding="utf-8")

        # 6. src/telemetry.ts
        telemetry_ts = """export interface TelemetryEvent {
  type: string;
  timestamp: string;
  payload: Record<string, any>;
}

export type ObserverCallback = (event: TelemetryEvent) => void;

export class TelemetryEmitter {
  constructor(
    private onEvent?: ObserverCallback,
    private onObserverError?: (err: any) => void
  ) {}

  emit(type: string, payload: Record<string, any> = {}): void {
    if (!this.onEvent) return;
    try {
      this.onEvent({
        type,
        timestamp: new Date().toISOString(),
        payload,
      });
    } catch (err) {
      if (this.onObserverError) {
        try {
          this.onObserverError(err);
        } catch {
          // Suppress secondary observer failure
        }
      }
    }
  }
}
"""
        files["telemetry.ts"] = src_dir / "telemetry.ts"
        files["telemetry.ts"].write_text(telemetry_ts, encoding="utf-8")

        # 7. src/runAgent.ts
        run_agent_ts = """import { Message, Model } from './model';
import { ToolRegistry } from './tools';
import { BudgetTracker } from './budget';
import { TelemetryEmitter, ObserverCallback } from './telemetry';

export interface RunAgentParams {
  prompt: string;
  model: Model;
  tools: ToolRegistry;
  maxSteps?: number;
  maxToolCalls?: number;
  signal?: AbortSignal;
  onEvent?: ObserverCallback;
}

export interface RunResult {
  status: 'completed' | 'step_limit' | 'tool_limit' | 'aborted' | 'model_error';
  answer?: string;
  messages: Message[];
  steps: number;
}

export async function runAgent(params: RunAgentParams): Promise<RunResult> {
  const {
    prompt,
    model,
    tools,
    maxSteps = 25,
    maxToolCalls = 75,
    signal,
    onEvent,
  } = params;

  const telemetry = new TelemetryEmitter(onEvent);
  const tracker = new BudgetTracker({ maxSteps, maxToolCalls });
  const messages: Message[] = [{ role: 'user', content: prompt }];

  while (tracker.checkSteps()) {
    if (signal?.aborted) {
      return { status: 'aborted', messages, steps: tracker.steps };
    }

    telemetry.emit('model_start', { step: tracker.steps });
    let response;
    try {
      response = await model.generate({ messages, signal });
    } catch (err: any) {
      telemetry.emit('model_error', { error: err.message });
      return { status: 'model_error', messages, steps: tracker.steps };
    }
    telemetry.emit('model_end', { step: tracker.steps });
    tracker.incrementStep();

    if (!response.tool_calls || response.tool_calls.length === 0) {
      messages.push({ role: 'assistant', content: response.answer });
      return {
        status: 'completed',
        answer: response.answer,
        messages,
        steps: tracker.steps,
      };
    }

    // Atomic batch budget verification before transcript mutation
    if (!tracker.checkBatch(response.tool_calls.length)) {
      return { status: 'tool_limit', messages, steps: tracker.steps };
    }

    // Admitted: append assistant call and execute
    messages.push({ role: 'assistant', tool_calls: response.tool_calls });
    tracker.recordBatch(response.tool_calls.length);

    for (const call of response.tool_calls) {
      telemetry.emit('tool_start', { tool: call.name });
      const resultMsg = await tools.dispatch(call, signal);
      messages.push(resultMsg);
      telemetry.emit('tool_end', { tool: call.name, isError: resultMsg.isError });
    }
  }

  return { status: 'step_limit', messages, steps: tracker.steps };
}
"""
        files["runAgent.ts"] = src_dir / "runAgent.ts"
        files["runAgent.ts"].write_text(run_agent_ts, encoding="utf-8")

        return files
