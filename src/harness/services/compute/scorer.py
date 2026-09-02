"""Dimensional complexity scorer for evaluating task surface across 5 dimensions."""

from __future__ import annotations

from typing import Any

from harness.services.compute.types import (
    AssessmentTrace,
    ComplexityVector,
    ScoringProfile,
    ScoringProfileName,
)


class DimensionalScorer:
    """Evaluates task surface across 5 orthogonal complexity dimensions with configurable profiles."""

    HIGH_KEYWORDS: set[str] = {
        "refactor", "architect", "deepen", "concurrency", "race condition",
        "deadlock", "dag", "isnad", "security", "threat model", "migration",
        "multi-file", "ast", "inversion of control", "topological", "consensus",
        "distributed", "sandbox", "metaclass", "protocol", "kernel", "cryptography"
    }

    LOW_KEYWORDS: set[str] = {
        "format", "lint", "regex", "boilerplate", "docstring", "typo",
        "print", "rename", "capitalize", "json schema", "convert case",
        "comment", "whitespace", "markdown", "sort imports"
    }

    CONCURRENCY_KEYWORDS: set[str] = {
        "asyncio", "thread", "concurrency", "lock", "mutex", "deadlock",
        "race condition", "event loop", "parallel", "semaphore"
    }

    DEPTH_KEYWORDS: set[str] = {
        "ast", "parser", "type system", "topological", "compiler", "dag",
        "bytecode", "algorithm", "recursive", "optimization", "graph"
    }

    @classmethod
    def evaluate(
        cls,
        prompt: str,
        *,
        files_count: int = 1,
        is_architecture: bool = False,
        is_debugging: bool = False,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> tuple[ComplexityVector, AssessmentTrace]:
        """Compute dimensional scores, vector composite, and explainability trace."""
        active_profile: ScoringProfile
        if isinstance(profile, ScoringProfile):
            active_profile = profile
        elif profile:
            active_profile = ScoringProfile.get_preset(profile)
        else:
            active_profile = ScoringProfile.get_preset(ScoringProfileName.BALANCED)

        prompt_lower = prompt.lower()

        all_high_kw = cls.HIGH_KEYWORDS | active_profile.custom_high_keywords
        all_low_kw = cls.LOW_KEYWORDS | active_profile.custom_low_keywords

        detected_high = [kw for kw in all_high_kw if kw in prompt_lower]
        detected_low = [kw for kw in all_low_kw if kw in prompt_lower]
        detected_concurrency = [kw for kw in cls.CONCURRENCY_KEYWORDS if kw in prompt_lower]
        detected_depth = [kw for kw in cls.DEPTH_KEYWORDS if kw in prompt_lower]

        # 1. Ambiguity Score (0.0 to 1.0)
        ambiguity = 0.3
        if is_debugging:
            ambiguity += 0.4
        if "design" in prompt_lower or "architect" in prompt_lower or "explore" in prompt_lower:
            ambiguity += 0.3
        if detected_low and not detected_high:
            ambiguity = max(0.1, ambiguity - 0.2)
        ambiguity = min(1.0, max(0.0, ambiguity))

        # 2. Span Score (0.0 to 1.0) based on files and multi-module references
        span = 0.2
        if files_count > 3:
            span = 0.9
        elif files_count > 1:
            span = 0.6
        if "multi-file" in prompt_lower or "across" in prompt_lower or "subsystem" in prompt_lower:
            span = min(1.0, span + 0.3)

        # 3. Depth Score (0.0 to 1.0)
        depth = 0.3
        if detected_depth:
            depth += 0.4
        if is_architecture:
            depth += 0.3
        if "kernel" in prompt_lower or "core" in prompt_lower:
            depth += 0.2
        depth = min(1.0, max(0.0, depth))

        # 4. Rigor Score (0.0 to 1.0)
        rigor = 0.3
        if "migration" in prompt_lower or "persistent" in prompt_lower or "database" in prompt_lower:
            rigor += 0.4
        if "security" in prompt_lower or "audit" in prompt_lower or "isnad" in prompt_lower:
            rigor += 0.4
        if is_architecture:
            rigor += 0.2
        rigor = min(1.0, max(0.0, rigor))

        # 5. Concurrency Score (0.0 to 1.0)
        concurrency = 0.1
        if detected_concurrency:
            concurrency = min(1.0, 0.4 + (0.2 * len(detected_concurrency)))

        # Weighted Composite Score using active profile
        composite = (
            (ambiguity * active_profile.ambiguity_weight)
            + (span * active_profile.span_weight)
            + (depth * active_profile.depth_weight)
            + (rigor * active_profile.rigor_weight)
            + (concurrency * active_profile.concurrency_weight)
        )

        # Classify Level using profile thresholds
        if (
            is_architecture
            or files_count > 3
            or (detected_high and (is_debugging or files_count > 1))
            or composite >= active_profile.high_threshold
        ):
            level = "High"
        elif (
            detected_low
            and not detected_high
            and files_count <= 1
            and not is_architecture
            and not is_debugging
            and composite < active_profile.low_threshold
        ):
            level = "Low"
        else:
            level = "Medium"

        vector = ComplexityVector(
            ambiguity_score=ambiguity,
            span_score=span,
            depth_score=depth,
            rigor_score=rigor,
            concurrency_score=concurrency,
            composite_score=composite,
            level=level,
        )

        high_factors: list[str] = []
        if is_architecture:
            high_factors.append("Architectural refactoring flag enabled")
        if files_count > 3:
            high_factors.append(f"High multi-file footprint ({files_count} files)")
        if detected_high:
            high_factors.append(f"High-complexity keywords detected: {', '.join(detected_high)}")
        if is_debugging:
            high_factors.append("Debugging / diagnostic investigation flag enabled")

        low_factors: list[str] = []
        if detected_low:
            low_factors.append(f"Mechanical / low keywords detected: {', '.join(detected_low)}")
        if files_count <= 1 and not is_architecture and not is_debugging:
            low_factors.append("Confined single-file scope")

        trace = AssessmentTrace(
            high_factors=high_factors,
            low_factors=low_factors,
            detected_keywords=list(set(detected_high + detected_low)),
            files_evaluated=files_count,
            is_architectural=is_architecture,
            is_debugging=is_debugging,
            profile_used=active_profile.name,
            notes=f"Composite score {composite:.2f} classified into {level} complexity tier via '{active_profile.name}' profile.",
        )

        return vector, trace

    @classmethod
    def evaluate_conversation(
        cls,
        messages: list[Any],
        *,
        profile: ScoringProfile | ScoringProfileName | str | None = None,
    ) -> tuple[ComplexityVector, AssessmentTrace]:
        """Evaluate multi-turn conversation messages, detecting tool calls, context length, and algorithmic density."""
        combined_text_parts: list[str] = []
        tool_call_count = 0
        is_debugging = False
        is_architecture = False
        files_found: set[str] = set()

        for msg in messages:
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else str(msg))
            if isinstance(content, str):
                combined_text_parts.append(content)
                for word in content.split():
                    if "." in word and ("/" in word or "\\" in word or word.endswith((".py", ".ts", ".js", ".json", ".md", ".rs", ".go"))):
                        files_found.add(word)

            tc = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)
            if tc:
                tool_call_count += len(tc)
            elif (
                getattr(msg, "tool_call_id", None)
                or (isinstance(msg, dict) and msg.get("tool_call_id"))
                or getattr(msg, "role", None) == "tool"
                or (isinstance(msg, dict) and msg.get("role") == "tool")
            ):
                tool_call_count += 1

        full_text = " ".join(combined_text_parts)
        prompt_lower = full_text.lower()
        if any(err_kw in prompt_lower for err_kw in ("error", "traceback", "exception", "failed", "bug", "deadlock", "race condition")):
            is_debugging = True
        if any(arch_kw in prompt_lower for arch_kw in ("architect", "refactor", "seam", "migration", "deepen", "kernel", "topological")):
            is_architecture = True

        files_count = max(1, len(files_found))
        vector, trace = cls.evaluate(
            full_text,
            files_count=files_count,
            is_architecture=is_architecture,
            is_debugging=is_debugging,
            profile=profile,
        )

        if tool_call_count > 2:
            vector.depth_score = min(1.0, vector.depth_score + 0.15)
            vector.rigor_score = min(1.0, vector.rigor_score + 0.15)
            trace.high_factors.append(f"Active tool calling trajectory ({tool_call_count} tool calls)")

        trace.notes += f" Evaluated from {len(messages)} conversation messages with {tool_call_count} tool calls."
        return vector, trace
