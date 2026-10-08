"""Declarative Django Model class and fields source code generator."""

from __future__ import annotations

from typing import Any


def generate_model_source(
    model_name: str,
    fields: list[dict[str, Any]],
    app_label: str = "",
    docstring: str = "",
    meta_options: dict[str, Any] | None = None,
) -> str:
    """Generate Python source code for a declarative Django Model class."""
    lines: list[str] = [
        "from django.db import models",
        "from django.utils.translation import gettext_lazy as _",
        "",
        f"class {model_name}(models.Model):",
    ]
    if docstring:
        lines.append(f'    """{docstring.strip()}"""')
        lines.append("")

    for f in fields:
        fname = f.get("name", "field")
        ftype = f.get("type", "CharField")
        kwargs: list[str] = []

        if ftype == "CharField":
            max_len = f.get("max_length", 255)
            kwargs.append(f"max_length={max_len}")
        elif ftype == "DecimalField":
            max_digits = f.get("max_digits", 10)
            dec_places = f.get("decimal_places", 2)
            kwargs.append(f"max_digits={max_digits}")
            kwargs.append(f"decimal_places={dec_places}")
        elif ftype == "SlugField":
            max_len = f.get("max_length", 255)
            kwargs.append(f"max_length={max_len}")

        if ftype in ("ForeignKey", "OneToOneField"):
            rel_model = f.get("related_model", "auth.User")
            on_del = f.get("on_delete", "CASCADE")
            kwargs.insert(0, f"'{rel_model}'")
            kwargs.append(f"on_delete=models.{on_del}")
            if "related_name" in f:
                kwargs.append(f"related_name='{f['related_name']}'")
        elif ftype == "ManyToManyField":
            rel_model = f.get("related_model", "auth.User")
            kwargs.insert(0, f"'{rel_model}'")
            if "related_name" in f:
                kwargs.append(f"related_name='{f['related_name']}'")

        if f.get("null") is True:
            kwargs.append("null=True")
        if f.get("blank") is True:
            kwargs.append("blank=True")
        if f.get("unique") is True:
            kwargs.append("unique=True")
        if f.get("db_index") is True:
            kwargs.append("db_index=True")
        if "default" in f:
            d_val = f["default"]
            if isinstance(d_val, str) and not d_val.startswith("models."):
                kwargs.append(f"default='{d_val}'")
            else:
                kwargs.append(f"default={d_val}")

        kwargs_str = ", ".join(kwargs)
        lines.append(f"    {fname} = models.{ftype}({kwargs_str})")

    # Meta options
    lines.append("")
    lines.append("    class Meta:")
    if app_label:
        lines.append(f"        app_label = '{app_label}'")
    if meta_options:
        if "db_table" in meta_options:
            lines.append(f"        db_table = '{meta_options['db_table']}'")
        if "ordering" in meta_options:
            ord_list = [f"'{o}'" for o in meta_options["ordering"]]
            lines.append(f"        ordering = [{', '.join(ord_list)}]")
        if "verbose_name" in meta_options:
            lines.append(f"        verbose_name = _('{meta_options['verbose_name']}')")
        if "verbose_name_plural" in meta_options:
            lines.append(f"        verbose_name_plural = _('{meta_options['verbose_name_plural']}')")
        if "unique_together" in meta_options:
            lines.append(f"        unique_together = {meta_options['unique_together']}")
    else:
        lines.append("        ordering = ['-id']")

    # __str__ method
    primary_char = next(
        (f.get("name") for f in fields if f.get("type") in ("CharField", "SlugField", "EmailField")),
        "id",
    )
    lines.append("")
    lines.append("    def __str__(self) -> str:")
    lines.append(f"        return str(self.{primary_char})")
    lines.append("")

    return "\n".join(lines)
