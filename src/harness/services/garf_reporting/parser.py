"""Garf SQL query parser, macro expansion, and virtual column extraction."""

from __future__ import annotations

import datetime
import re
from typing import Any

from .models import GarfQuerySpec, VirtualColumnSpec


def expand_macros(
    query_text: str, macros: dict[str, Any] | None = None
) -> tuple[str, tuple[tuple[str, str], ...]]:
    """Expand dynamic date macros and user-provided macro variables."""
    expanded = query_text
    macro_records: list[tuple[str, str]] = []
    today = datetime.datetime.now(datetime.timezone.utc).date()

    # Dynamic date macro pattern: :YYYYMMDD-N or :YYYYMMDD+N
    date_pattern = re.compile(r":YYYYMMDD([+-]\d+)?")

    def _replace_date(match: re.Match[str]) -> str:
        delta_str = match.group(1)
        target_date = today
        if delta_str:
            days = int(delta_str)
            target_date = today + datetime.timedelta(days=days)
        res = target_date.strftime("%Y-%m-%d")
        macro_records.append((match.group(0), res))
        return f"'{res}'"

    expanded = date_pattern.sub(_replace_date, expanded)

    # :TODAY macro
    if ":TODAY" in expanded:
        today_str = f"'{today.strftime('%Y-%m-%d')}'"
        expanded = expanded.replace(":TODAY", today_str)
        macro_records.append((":TODAY", today_str))

    # Explicit user-supplied macros
    if macros:
        for k, v in macros.items():
            macro_key = f":{k}" if not k.startswith(":") else k
            val_str = str(v)
            if macro_key in expanded:
                expanded = expanded.replace(macro_key, val_str)
                macro_records.append((macro_key, val_str))

    return expanded, tuple(macro_records)


def parse_query(
    query_text: str, macros: dict[str, Any] | None = None
) -> GarfQuerySpec:
    """Parse SQL query into structured fields, aliases, filters, sorts, and limits."""
    cleaned_text = query_text.strip()
    expanded_text, dynamic_macros = expand_macros(cleaned_text, macros)

    # Extract title from leading comment if present (e.g. /* title: campaign_perf */ or -- title: campaign_perf)
    title = None
    title_match = re.search(
        r"(?:/\*|--)\s*title:\s*([\w\-]+)", cleaned_text, re.IGNORECASE
    )
    if title_match:
        title = title_match.group(1).strip()

    # Normalize whitespace for SQL token extraction
    sql = re.sub(r"\s+", " ", expanded_text).strip()

    # Regular expression for SELECT ... FROM ... [WHERE ...] [ORDER BY ...] [LIMIT ...]
    select_match = re.search(
        r"SELECT\s+(.*?)\s+FROM\s+([a-zA-Z0-9_\.]+)(?:\s+WHERE\s+(.*?))?(?:\s+ORDER\s+BY\s+(.*?))?(?:\s+LIMIT\s+(\d+))?$",
        sql,
        re.IGNORECASE,
    )

    if not select_match:
        raise ValueError(f"Could not parse valid SQL from query: {cleaned_text}")

    raw_fields = select_match.group(1).strip()
    resource_name = select_match.group(2).strip()
    raw_where = select_match.group(3)
    raw_order = select_match.group(4)
    raw_limit = select_match.group(5)

    # Parse fields, aliases, and virtual columns
    field_tokens = [f.strip() for f in raw_fields.split(",") if f.strip()]
    fields: list[str] = []
    column_names: list[str] = []
    virtual_columns: list[VirtualColumnSpec] = []

    for token in field_tokens:
        alias_match = re.search(r"^(.*?)\s+(?:AS|as)\s+([a-zA-Z0-9_]+)$", token)
        if alias_match:
            expr = alias_match.group(1).strip()
            alias = alias_match.group(2).strip()
            fields.append(expr)
            column_names.append(alias)
            if re.search(r"[\/\*\+\-\(\)\'\"]", expr) or re.search(r"\d+", expr):
                src_candidates = re.findall(r"[a-zA-Z_][a-zA-Z0-9_\.]*", expr)
                src_fields = [
                    c
                    for c in src_candidates
                    if c.upper()
                    not in (
                        "AS",
                        "NULL",
                        "TRUE",
                        "FALSE",
                        "CASE",
                        "WHEN",
                        "THEN",
                        "ELSE",
                        "END",
                    )
                ]
                virtual_columns.append(
                    VirtualColumnSpec(
                        name=alias,
                        expression=expr,
                        source_fields=tuple(dict.fromkeys(src_fields)),
                    )
                )
        else:
            fields.append(token)
            col_name = token.split(".")[-1]
            column_names.append(col_name)

    # Parse filters
    filters: list[str] = []
    if raw_where:
        filters = [
            f.strip()
            for f in re.split(r"\s+AND\s+", raw_where, flags=re.IGNORECASE)
            if f.strip()
        ]

    # Parse sorts
    sorts: list[str] = []
    if raw_order:
        sorts = [s.strip() for s in raw_order.split(",") if s.strip()]

    limit = int(raw_limit) if raw_limit else None

    return GarfQuerySpec(
        text=cleaned_text,
        title=title or resource_name,
        resource_name=resource_name,
        fields=tuple(fields),
        filters=tuple(filters),
        sorts=tuple(sorts),
        limit=limit,
        column_names=tuple(column_names),
        dynamic_macros=dynamic_macros,
        virtual_columns=tuple(virtual_columns),
    )
