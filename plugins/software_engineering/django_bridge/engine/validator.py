"""Django template syntax, tag stack balance, partialdef, and filter diagnostics."""

from __future__ import annotations

import re

from harness.services.django_bridge import DjangoValidationResult


def validate_template_syntax(
    template_content: str,
    template_path: str | None = None,
    enable_partials: bool = True,
) -> DjangoValidationResult:
    """Validate syntax of Django templates, block tags, partials, and filters."""
    errors: list[str] = []
    warnings: list[str] = []
    partials: list[str] = []
    tags_found: set[str] = set()
    filters_found: set[str] = set()

    tag_pairs = {
        "if": "endif",
        "for": "endfor",
        "block": "endblock",
        "with": "endwith",
        "autoescape": "endautoescape",
        "comment": "endcomment",
        "filter": "endfilter",
        "spaceless": "endspaceless",
    }
    if enable_partials:
        tag_pairs["partialdef"] = "endpartialdef"

    tag_stack: list[tuple[str, int]] = []

    # Find tags {% ... %}
    for match in re.finditer(r"\{%\s*(\w+)(.*?)\s*%\}", template_content):
        tag_name = match.group(1)
        tag_args = match.group(2).strip()
        line_no = template_content[: match.start()].count("\n") + 1
        tags_found.add(tag_name)

        if tag_name == "partialdef":
            p_name = tag_args.split()[0] if tag_args else "unnamed"
            partials.append(p_name.strip("\"'"))

        if tag_name in tag_pairs:
            tag_stack.append((tag_name, line_no))
        elif tag_name.startswith("end"):
            if not tag_stack:
                errors.append(f"Line {line_no}: Unexpected closing tag '{{% {tag_name} %}}' with no matching open tag")
            else:
                open_tag, open_line = tag_stack[-1]
                expected_close = tag_pairs.get(open_tag)
                if tag_name == expected_close:
                    tag_stack.pop()
                else:
                    errors.append(
                        f"Line {line_no}: Mismatched closing tag '{{% {tag_name} %}}' (expected '{{% {expected_close} %}}' opened at line {open_line})"
                    )

    # Check unclosed tags
    for unclosed, line in tag_stack:
        errors.append(f"Line {line}: Unclosed tag '{{% {unclosed} %}}' (missing '{{% {tag_pairs[unclosed]} %}}')")

    # Find filters {{ val|filter:arg }}
    for match in re.finditer(r"\{\{(.*?)\}\}", template_content):
        var_expr = match.group(1)
        parts = var_expr.split("|")[1:]
        for p in parts:
            f_name = p.split(":")[0].strip()
            if f_name:
                filters_found.add(f_name)

    return DjangoValidationResult(
        valid=(len(errors) == 0),
        errors=tuple(errors),
        warnings=tuple(warnings),
        partials_found=tuple(sorted(partials)),
        tags_found=tuple(sorted(tags_found)),
        filters_found=tuple(sorted(filters_found)),
    )
