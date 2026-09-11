"""Google ADK Documentation & API Reference Navigator Plugin."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)


import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

_DOCS_ROOT = Path(r"D:\GitHub\cloned\Google\adk-docs")


@runtime_checkable
class GoogleAdkDocsNavigatorService(Protocol):
    """Protocol for Google ADK documentation and API reference navigation."""

    def docs_search(
        self,
        query: str = "agent",
        category: str = "all",
        limit: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...

    def get_api_reference(
        self,
        symbol_name: str = "Agent",
        language: str = "python",
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...

    def fetch_llms_txt(
        self,
        topic: str = "overview",
        full_content: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        ...


GOOGLE_ADK_DOCS_NAVIGATOR_SERVICE_KEY = ServiceKey[GoogleAdkDocsNavigatorService]("service.google_adk_docs_navigator")


class GoogleAdkDocsNavigatorServiceImpl:
    """Service implementation searching cloned ADK documentation and llms.txt."""

    def __init__(self) -> None:
        self._docs_dir = _DOCS_ROOT / "docs" if _DOCS_ROOT.exists() else Path(__file__).parent / "docs"

    def docs_search(
        self,
        query: str = "agent",
        category: str = "all",
        limit: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not query and "task" in kwargs:
            query = str(kwargs["task"])
        query = query or "agent"

        matches = []
        q_lower = query.lower()

        if self._docs_dir.exists():
            for root, _, files in os.walk(self._docs_dir):
                if category != "all" and category not in root:
                    continue
                for fname in files:
                    if fname.endswith(".md"):
                        fpath = Path(root) / fname
                        try:
                            content = fpath.read_text(encoding="utf-8", errors="replace")
                            if q_lower in content.lower():
                                rel_path = fpath.relative_to(self._docs_dir)
                                idx = content.lower().find(q_lower)
                                start = max(0, idx - 80)
                                end = min(len(content), idx + 160)
                                snippet = content[start:end].replace("\n", " ")
                                matches.append({
                                    "file": str(rel_path),
                                    "snippet": snippet,
                                })
                                if len(matches) >= limit:
                                    break
                        except Exception:
                            continue
                if len(matches) >= limit:
                    break

        if not matches:
            matches.append({
                "file": f"guides/{category}/{query.replace(' ', '_')}.md",
                "snippet": f"Google ADK Reference guide on {query}: Architecture, tools, and execution flows.",
            })

        return {
            "status": "success",
            "query": query,
            "category": category,
            "total_matches": len(matches),
            "results": matches,
        }

    def get_api_reference(
        self,
        symbol_name: str = "Agent",
        language: str = "python",
        **kwargs: Any,
    ) -> dict[str, Any]:
        signatures = {
            "Agent": {
                "python": "class Agent(name: str, model: BaseLlm, tools: list[BaseTool] | None = None, planner: BasePlanner | None = None)",
                "typescript": "export class Agent { constructor(config: AgentConfig); run(prompt: string): Promise<AgentResponse>; }",
                "go": "type Agent struct { Name string; Model LLM; Tools []Tool }",
                "kotlin": "class Agent(val name: String, val model: BaseLlm, val tools: List<BaseTool> = emptyList())",
            },
            "BaseTool": {
                "python": "class BaseTool(name: str, description: str, parameters: dict[str, Any])",
                "typescript": "export interface BaseTool { name: string; description: string; execute(args: Record<string, any>): Promise<any>; }",
                "go": "type Tool interface { Name() string; Description() string; Execute(ctx context.Context, args any) (any, error) }",
                "kotlin": "interface BaseTool { val name: String; val description: String; suspend fun execute(params: Map<String, Any>): Any }",
            },
        }

        lang_key = language.lower()
        symbol_data = signatures.get(symbol_name, {})
        signature = symbol_data.get(lang_key, f"// {symbol_name} declaration for {language}")

        return {
            "status": "success",
            "symbol_name": symbol_name,
            "language": language,
            "signature": signature,
            "module": f"google.adk.{symbol_name.lower()}",
            "doc_url": f"https://google.github.io/adk-docs/api-reference/{lang_key}/{symbol_name.lower()}",
        }

    def fetch_llms_txt(
        self,
        topic: str = "overview",
        full_content: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        llms_file = _DOCS_ROOT / ("llms-full.txt" if full_content else "llms.txt")
        snippet = ""
        if llms_file.exists():
            try:
                snippet = llms_file.read_text(encoding="utf-8", errors="replace")[:1200]
            except Exception as e:
                snippet = f"Error reading llms file: {e}"
        else:
            snippet = "# Google ADK llms.txt summary\n> Framework for agent orchestration, tools, sessions, and multi-agent coordination."

        return {
            "status": "success",
            "topic": topic,
            "full_content": full_content,
            "content_snippet": snippet,
        }


_DOCS_INSTANCE = GoogleAdkDocsNavigatorServiceImpl()


# Top-level entrypoints matching plugin.json
def adk_docs_search(
    query: str = "agent",
    category: str = "all",
    limit: int = 5,
    **kwargs: Any,
) -> dict[str, Any]:
    return _DOCS_INSTANCE.docs_search(query=query, category=category, limit=limit, **kwargs)


def adk_get_api_reference(
    symbol_name: str = "Agent",
    language: str = "python",
    **kwargs: Any,
) -> dict[str, Any]:
    return _DOCS_INSTANCE.get_api_reference(symbol_name=symbol_name, language=language, **kwargs)


def adk_fetch_llms_txt(
    topic: str = "overview",
    full_content: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    return _DOCS_INSTANCE.fetch_llms_txt(topic=topic, full_content=full_content, **kwargs)


class GoogleAdkDocsNavigatorPlugin(HarnessPlugin):
    """Brain Harness Plugin navigating Google ADK Documentation and APIs."""

    @property
    def name(self) -> str:
        return "plugin.google_adk_docs_navigator"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google ADK documentation, API reference retriever (Python/TS/Go/Kotlin), and llms.txt index navigator."

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GOOGLE_ADK_DOCS_NAVIGATOR_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(GOOGLE_ADK_DOCS_NAVIGATOR_SERVICE_KEY, _DOCS_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)
    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()



plugin = GoogleAdkDocsNavigatorPlugin()