"""Django ORM query expression to SQL compiler and read-only safety guard."""

from __future__ import annotations

import re
from typing import Any

from harness.services.django_bridge import DjangoQueryResult


def simulate_orm_query(
    query_expr: str,
    model_name: str,
    project_path: str | None = None,
) -> DjangoQueryResult:
    """Safely translate and compile a Django ORM query expression to SQL."""
    clean_expr = query_expr.strip()
    table_name = f"{model_name.lower()}s" if not model_name.endswith("s") else model_name.lower()

    # Check read-only safety
    destructive_methods = (".delete(", ".update(", ".bulk_create(", ".create(", ".save(")
    is_safe = not any(m in clean_expr for m in destructive_methods)

    where_clauses: list[str] = []
    params: list[Any] = []
    tables_ref: list[str] = [table_name]
    limit_clause = ""
    order_clause = ""

    # Extract .filter(...)
    filter_matches = re.findall(r"\.filter\((.*?)\)", clean_expr)
    for match in filter_matches:
        args = [a.strip() for a in match.split(",") if "=" in a]
        for arg in args:
            k, v = arg.split("=", 1)
            k, v = k.strip(), v.strip()
            col = k
            op = "="
            if "__gte" in k:
                col = k.replace("__gte", "")
                op = ">="
            elif "__lte" in k:
                col = k.replace("__lte", "")
                op = "<="
            elif "__gt" in k:
                col = k.replace("__gt", "")
                op = ">"
            elif "__lt" in k:
                col = k.replace("__lt", "")
                op = "<"
            elif "__icontains" in k:
                col = k.replace("__icontains", "")
                op = "ILIKE"
                clean_val = v.strip("'\"")
                v = f"'%{clean_val}%'"
            elif "__contains" in k:
                col = k.replace("__contains", "")
                op = "LIKE"
                clean_val = v.strip("'\"")
                v = f"'%{clean_val}%'"
            elif "__in" in k:
                col = k.replace("__in", "")
                op = "IN"

            where_clauses.append(f'"{table_name}"."{col}" {op} {v}')
            params.append(v)

    # Extract .select_related(...)
    select_rel = re.findall(r"\.select_related\((.*?)\)", clean_expr)
    for rel in select_rel:
        rel_name = rel.strip("'\"")
        if rel_name:
            tables_ref.append(f"{rel_name}s")

    # Extract .order_by(...)
    order_match = re.search(r"\.order_by\((.*?)\)", clean_expr)
    if order_match:
        fields = [f.strip("'\" ") for f in order_match.group(1).split(",")]
        order_items: list[str] = []
        for of in fields:
            direction = "DESC" if of.startswith("-") else "ASC"
            clean_f = of.lstrip("-")
            order_items.append(f'"{table_name}"."{clean_f}" {direction}')
        if order_items:
            order_clause = f" ORDER BY {', '.join(order_items)}"

    # Extract slice [:N]
    slice_match = re.search(r"\[:?(\d+)\]", clean_expr)
    if slice_match:
        limit_clause = f" LIMIT {slice_match.group(1)}"

    # Construct SQL
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    generated_sql = f'SELECT "{table_name}".* FROM "{table_name}"{where_sql}{order_clause}{limit_clause};'

    explain_plan = f"SCAN TABLE {table_name}" + (
        f" USING INDEX ON ({', '.join(where_clauses)})" if where_clauses else ""
    )

    return DjangoQueryResult(
        query_expr=clean_expr,
        model_name=model_name,
        generated_sql=generated_sql,
        params=tuple(params),
        explain_plan=explain_plan,
        is_safe_read_only=is_safe,
        tables_referenced=tuple(tables_ref),
    )
