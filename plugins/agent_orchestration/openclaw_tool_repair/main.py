"""OpenClaw Tool Repair Plugin — In-flight plain-text tool-call recovery and streaming event normalizer."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any
import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.openclaw_bridge import (
    OPENCLAW_TOOL_REPAIR_KEY,
    OpenClawToolBlock,
    OpenClawToolRepairService,
)

logger = structlog.get_logger(__name__)

# Regex patterns for detecting plain-text tool invocations
JSON_CODEBLOCK_PATTERN = re.compile(
    r"```(?:json)?\s*(\{\s*[\"'](?:tool|tool_name|name|action|function)[\"']\s*:[\s\S]*?\})\s*```",
    re.IGNORECASE,
)
STANDALONE_JSON_TOOL_PATTERN = re.compile(
    r"\{\s*[\"'](?:tool|tool_name|name|action|function)[\"']\s*:\s*[\"'](?P<tool>[a-zA-Z0-9_\-\.]+)[\"']\s*,\s*[\"'](?:arguments|parameters|args|params)[\"']\s*:\s*(?P<args>\{[\s\S]*?\})\s*\}",
    re.IGNORECASE,
)
XML_TOOL_CALL_PATTERN = re.compile(
    r"<(?:tool_call|invoke|function_call)(?:\s+name=[\"'](?P<name>[a-zA-Z0-9_\-\.]+)[\"'])?\s*>(?P<body>[\s\S]*?)</(?:tool_call|invoke|function_call)>",
    re.IGNORECASE,
)


class OpenClawToolRepairServiceImpl(OpenClawToolRepairService):
    """AST regex parser and JSON repair engine implementing OpenClaw Tool Repair."""

    def _sanitize_and_parse_json(self, raw_json_str: str) -> tuple[dict[str, Any], bool, str]:
        """Attempts to parse JSON, auto-repairing common model syntax errors."""
        cleaned = raw_json_str.strip()
        # 1. Direct parse attempt
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed, False, ""
        except Exception:
            pass

        # 2. Repair trailing commas (e.g. `{"a": 1,}`)
        repaired = re.sub(r",\s*([\]}])", r"\1", cleaned)

        # 3. Repair unescaped single quotes to double quotes if valid JSON structure
        repaired = re.sub(r"(?<!\\)'", '"', repaired)

        # 4. Repair unclosed brackets or braces
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")
        if open_brackets > 0:
            repaired += "]" * open_brackets
        if open_braces > 0:
            repaired += "}" * open_braces

        try:
            parsed = json.loads(repaired)
            if isinstance(parsed, dict):
                return parsed, True, "Repaired unbalanced brackets or trailing commas"
        except Exception as err:
            logger.debug("json_repair_fallback_failed", error=str(err), raw=raw_json_str[:60])

        return {"raw_payload": raw_json_str}, True, "Fallback raw payload wrapping"

    def parse_plain_text_tool_blocks(self, text: str) -> list[OpenClawToolBlock]:
        """Parses model-emitted plain-text tool call blocks and code fences."""
        blocks: list[OpenClawToolBlock] = []

        # 1. Check for XML tool tags
        for match in XML_TOOL_CALL_PATTERN.finditer(text):
            tool_name = match.group("name") or "generic_tool"
            body = match.group("body").strip()
            parsed_args, repaired, reason = self._sanitize_and_parse_json(body)
            blocks.append(
                OpenClawToolBlock(
                    tool_name=tool_name,
                    arguments=parsed_args,
                    raw_block=match.group(0),
                    call_id=f"call_{uuid.uuid4().hex[:8]}",
                    is_repaired=repaired or True,
                    repair_reason=reason or "Extracted from XML tool tags",
                )
            )

        # 2. Check for JSON codeblocks
        for match in JSON_CODEBLOCK_PATTERN.finditer(text):
            raw_json = match.group(1)
            parsed, repaired, reason = self._sanitize_and_parse_json(raw_json)
            tool_name = parsed.get("tool") or parsed.get("tool_name") or parsed.get("name") or parsed.get("action") or "unknown_tool"
            args = parsed.get("arguments") or parsed.get("parameters") or parsed.get("args") or parsed.get("params") or parsed
            if not isinstance(args, dict):
                args = {"value": args}

            blocks.append(
                OpenClawToolBlock(
                    tool_name=str(tool_name),
                    arguments=args,
                    raw_block=match.group(0),
                    call_id=f"call_{uuid.uuid4().hex[:8]}",
                    is_repaired=repaired or True,
                    repair_reason=reason or "Extracted from JSON codeblock",
                )
            )

        # 3. Check for Standalone JSON tool calls
        if not blocks:
            for match in STANDALONE_JSON_TOOL_PATTERN.finditer(text):
                tool_name = match.group("tool")
                raw_args = match.group("args")
                args, repaired, reason = self._sanitize_and_parse_json(raw_args)
                blocks.append(
                    OpenClawToolBlock(
                        tool_name=tool_name,
                        arguments=args,
                        raw_block=match.group(0),
                        call_id=f"call_{uuid.uuid4().hex[:8]}",
                        is_repaired=repaired or True,
                        repair_reason=reason or "Extracted from standalone JSON pattern",
                    )
                )

        return blocks

    def repair_json_call(self, raw_call: str | dict[str, Any]) -> OpenClawToolBlock:
        """Repairs trailing commas, unbalanced brackets, and unescaped strings in JSON arguments."""
        if isinstance(raw_call, dict):
            tool_name = str(raw_call.get("name") or raw_call.get("tool") or "tool")
            args = raw_call.get("arguments") or raw_call.get("parameters") or raw_call
            if not isinstance(args, dict):
                args = {"value": args}
            return OpenClawToolBlock(
                tool_name=tool_name,
                arguments=args,
                raw_block=json.dumps(raw_call),
                call_id=f"call_{uuid.uuid4().hex[:8]}",
                is_repaired=False,
            )

        parsed, repaired, reason = self._sanitize_and_parse_json(raw_call)
        tool_name = parsed.get("tool") or parsed.get("name") or parsed.get("tool_name") or "repaired_tool"
        args = parsed.get("arguments") or parsed.get("parameters") or parsed.get("args") or parsed
        if not isinstance(args, dict):
            args = {"value": args}

        return OpenClawToolBlock(
            tool_name=str(tool_name),
            arguments=args,
            raw_block=raw_call,
            call_id=f"call_{uuid.uuid4().hex[:8]}",
            is_repaired=repaired,
            repair_reason=reason,
        )

    def normalize_stream_chunk(self, chunk: str) -> tuple[str, list[OpenClawToolBlock]]:
        """Filters stream chunks, stripping plain-text blocks and returning promoted tool events."""
        blocks = self.parse_plain_text_tool_blocks(chunk)
        if not blocks:
            return chunk, []

        stripped_chunk = chunk
        for b in blocks:
            stripped_chunk = stripped_chunk.replace(b.raw_block, "").strip()

        return stripped_chunk, blocks


class OpenClawToolRepairPlugin(HarnessPlugin):
    """Harness plugin registering OpenClaw Tool Repair service and tool entrypoints."""

    name = "plugin.openclaw_tool_repair"
    version = "1.0.0"
    description = "In-flight plain-text tool-call recovery and streaming event normalizer"

    def __init__(self) -> None:
        super().__init__()
        self.service = OpenClawToolRepairServiceImpl()

    def register_services(self, context: ServiceContext) -> None:
        """Register the typed OpenClawToolRepairService into the IoC container."""
        context.provide(OPENCLAW_TOOL_REPAIR_KEY, self.service)
        logger.info("openclaw_tool_repair_service_registered")

    async def openclaw_parse_tool_blocks(self, text: str) -> list[dict[str, Any]]:
        """Tool handler for openclaw_parse_tool_blocks."""
        blocks = self.service.parse_plain_text_tool_blocks(text)
        return [b.to_dict() for b in blocks]

    async def openclaw_repair_tool_call(
        self,
        raw_call: str,
        tool_name: str | None = None,
    ) -> dict[str, Any]:
        """Tool handler for openclaw_repair_tool_call."""
        block = self.service.repair_json_call(raw_call)
        if tool_name and block.tool_name in {"repaired_tool", "tool", "unknown_tool"}:
            block = OpenClawToolBlock(
                tool_name=tool_name,
                arguments=block.arguments,
                raw_block=block.raw_block,
                call_id=block.call_id,
                is_repaired=block.is_repaired,
                repair_reason=block.repair_reason,
            )
        return block.to_dict()

    async def openclaw_normalize_stream_chunk(self, chunk: str) -> dict[str, Any]:
        """Tool handler for openclaw_normalize_stream_chunk."""
        stripped, blocks = self.service.normalize_stream_chunk(chunk)
        return {
            "stripped_text": stripped,
            "promoted_blocks": [b.to_dict() for b in blocks],
            "count": len(blocks),
        }
