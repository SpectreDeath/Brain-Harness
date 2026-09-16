# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx",
#     "pyyaml",
#     "structlog",
# ]
# ///

"""Paperless-NGX Headless CLI Client & Execution Script.

Provides deterministic non-interactive operations for document querying,
ingestion, and RAG chat interactions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Rule 23 & Rule 50: Explicit UTF-8 stream codec
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Prepend workspace root and src
workspace_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(workspace_root / "src"))
sys.path.insert(0, str(workspace_root))

from harness.services.paperless_ngx import (
    DefaultPaperlessNgxService,
    PaperlessConfig,
)


def salvage_json(raw_text: str) -> dict[str, Any]:
    """Execute local string salvage on malformed LLM or API JSON output per Rule 42."""
    text = raw_text.strip()
    # 1. Strip markdown code fences
    fence_pattern = r"^```(?:json)?\s*([\s\S]*?)\s*```$"
    match = re.search(fence_pattern, text, re.MULTILINE)
    if match:
        text = match.group(1).strip()

    # 2. Slice outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    # 3. Strip trailing commas
    text = re.sub(r",\s*([}\]])", r"\1", text)

    try:
        return json.loads(text)
    except Exception:
        return {"raw_content": raw_text}


def main() -> None:
    parser = argparse.ArgumentParser(description="Paperless-NGX Headless Client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search subcommand
    search_p = subparsers.add_parser("search", help="Search documents")
    search_p.add_argument("query", help="Query text")
    search_p.add_argument("--tags", nargs="*", help="Filter tags", default=[])
    search_p.add_argument("--correspondent", help="Filter correspondent", default=None)
    search_p.add_argument("--limit", type=int, default=10, help="Max results")

    # Get subcommand
    get_p = subparsers.add_parser("get", help="Get document by ID")
    get_p.add_argument("document_id", type=int, help="Document ID")

    # Post subcommand
    post_p = subparsers.add_parser("post", help="Post document for ingestion")
    post_p.add_argument("file_path", help="Local document file path")
    post_p.add_argument("--title", help="Document title", default=None)
    post_p.add_argument("--tags", nargs="*", help="Tags", default=[])
    post_p.add_argument("--correspondent", help="Correspondent", default=None)
    post_p.add_argument("--type", help="Document type", default=None)

    # Ask RAG subcommand
    ask_p = subparsers.add_parser("ask", help="Query paperless_ai RAG")
    ask_p.add_argument("query", help="Question to ask")
    ask_p.add_argument("--doc-ids", nargs="*", type=int, help="Limit to doc IDs", default=[])

    # Task status subcommand
    task_p = subparsers.add_parser("task", help="Check consumption task status")
    task_p.add_argument("task_id", help="Task UUID")

    args = parser.parse_args()

    import asyncio
    service = DefaultPaperlessNgxService(PaperlessConfig())

    if args.command == "search":
        res = asyncio.run(
            service.search_documents(
                query=args.query,
                tags=args.tags,
                correspondent=args.correspondent,
                limit=args.limit,
            )
        )
        print(
            json.dumps(
                {
                    "count": res.count,
                    "documents": [
                        {
                            "id": d.id,
                            "title": d.title,
                            "correspondent": d.correspondent,
                            "document_type": d.document_type,
                            "tags": list(d.tags),
                            "snippet": d.content_snippet,
                        }
                        for d in res.documents
                    ],
                },
                indent=2,
            )
        )

    elif args.command == "get":
        try:
            doc = asyncio.run(service.get_document(args.document_id))
            print(
                json.dumps(
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "correspondent": doc.correspondent,
                        "document_type": doc.document_type,
                        "tags": list(doc.tags),
                        "created": doc.created,
                        "snippet": doc.content_snippet,
                    },
                    indent=2,
                )
            )
        except KeyError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            sys.exit(1)

    elif args.command == "post":
        task = asyncio.run(
            service.post_document(
                file_path=args.file_path,
                title=args.title,
                tags=args.tags,
                correspondent=args.correspondent,
                document_type=args.type,
            )
        )
        print(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "result": task.result,
                },
                indent=2,
            )
        )

    elif args.command == "ask":
        ans = asyncio.run(service.ask_rag(query=args.query, document_ids=args.doc_ids))
        print(
            json.dumps(
                {
                    "answer": ans.answer,
                    "citations": list(ans.citations),
                },
                indent=2,
            )
        )

    elif args.command == "task":
        task = asyncio.run(service.get_task_status(args.task_id))
        print(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "result": task.result,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
