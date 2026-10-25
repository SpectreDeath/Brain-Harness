"""Template interpolation and workspace instantiation engine for ICM (arXiv:2603.16021)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .models import IcmScaffoldResult, IcmTemplateInterpolateResult

CANONICAL_CLONED_REPO = Path(r"D:\GitHub\cloned\Interpretable-Context-Methodology")

CONDITIONAL_PATTERN = re.compile(r"\{\{\?([A-Za-z0-9_]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL)
PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")


class IcmTemplateEngine:
    """High-performance template interpolation and workspace instantiation engine."""

    @staticmethod
    def interpolate_text(
        text: str,
        variables: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, str], list[str]]:
        """Interpolate variables and resolve conditionals per _core/placeholder-syntax.md."""
        vars_dict = dict(variables or {})
        applied: dict[str, str] = {}

        # 1. Resolve conditional sections: {{?SECTION}}...{{/SECTION}}
        def _resolve_cond(m: re.Match[str]) -> str:
            sec_name = m.group(1)
            content = m.group(2)
            val = vars_dict.get(sec_name)
            if val is not None and str(val).lower() not in ("false", "0", "no", ""):
                applied[sec_name] = str(val)
                return content.lstrip("\n")
            return ""

        result_text = CONDITIONAL_PATTERN.sub(_resolve_cond, text)

        # 2. Substitute standard placeholders: {{VARIABLE_NAME}}
        def _resolve_var(m: re.Match[str]) -> str:
            var_name = m.group(1)
            if var_name in vars_dict:
                val_str = str(vars_dict[var_name])
                applied[var_name] = val_str
                return val_str
            return m.group(0)

        result_text = PLACEHOLDER_PATTERN.sub(_resolve_var, result_text)

        # 3. Detect unresolved placeholders
        unresolved: list[str] = []
        for m in PLACEHOLDER_PATTERN.finditer(result_text):
            var_name = m.group(1)
            if var_name not in unresolved:
                unresolved.append(var_name)

        return result_text, applied, unresolved

    def interpolate_file(
        self,
        template_path: str | Path,
        variables: dict[str, Any] | None = None,
        output_path: str | Path | None = None,
    ) -> IcmTemplateInterpolateResult:
        """Read template file, interpolate placeholders, and optionally write output."""
        t_path = Path(template_path).resolve()
        if not t_path.exists():
            return IcmTemplateInterpolateResult(
                output_path=str(output_path or t_path),
                status="error",
                error=f"Template file not found: {t_path}",
            )

        try:
            content = t_path.read_text(encoding="utf-8", errors="replace")
            interpolated, applied, unresolved = self.interpolate_text(content, variables)

            out_dest = Path(output_path).resolve() if output_path else t_path
            out_dest.parent.mkdir(parents=True, exist_ok=True)
            out_dest.write_text(interpolated, encoding="utf-8")

            return IcmTemplateInterpolateResult(
                output_path=str(out_dest),
                variables_applied=applied,
                unresolved_placeholders=unresolved,
                status="ok",
            )
        except Exception as err:
            return IcmTemplateInterpolateResult(
                output_path=str(output_path or t_path),
                status="error",
                error=str(err),
            )

    def instantiate_workspace(
        self,
        target_dir: str | Path,
        template_name: str = "workspace-builder",
        name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> IcmScaffoldResult:
        """Instantiate a production-grade workspace from canonical templates (arXiv:2603.16021)."""
        out_dir = Path(target_dir).resolve()
        ws_name = name or out_dir.name
        vars_dict = dict(variables or {})
        vars_dict.setdefault("WORKSPACE_NAME", ws_name)
        vars_dict.setdefault("PROJECT_NAME", ws_name)

        created_files: list[str] = []
        source_ws = CANONICAL_CLONED_REPO / "workspaces" / template_name

        try:
            out_dir.mkdir(parents=True, exist_ok=True)

            if source_ws.exists() and source_ws.is_dir():
                # Copy from canonical upstream repository
                for item in source_ws.rglob("*"):
                    if ".git" in item.parts or item.name == ".gitkeep":
                        continue
                    rel_p = item.relative_to(source_ws)
                    dest_p = out_dir / rel_p
                    if item.is_dir():
                        dest_p.mkdir(parents=True, exist_ok=True)
                    elif item.is_file():
                        dest_p.parent.mkdir(parents=True, exist_ok=True)
                        if item.suffix.lower() == ".md":
                            raw = item.read_text(encoding="utf-8", errors="replace")
                            interp, _, _ = self.interpolate_text(raw, vars_dict)
                            dest_p.write_text(interp, encoding="utf-8")
                        else:
                            shutil.copy2(item, dest_p)
                        created_files.append(rel_p.as_posix())
            else:
                # Standalone fallback: scaffold structured template pipeline
                created_files.extend(self._fallback_scaffold(out_dir, template_name, ws_name))

            return IcmScaffoldResult(
                target_dir=str(out_dir),
                form=template_name,
                created_files=created_files,
                status="ok",
            )
        except Exception as err:
            return IcmScaffoldResult(
                target_dir=str(out_dir),
                form=template_name,
                created_files=created_files,
                status="error",
                error=str(err),
            )

    def _fallback_scaffold(self, out_dir: Path, template: str, ws_name: str) -> list[str]:
        """Scaffold baseline structure when cloned repo is offline."""
        files = ["AGENTS.md", "CLAUDE.md", "CONTEXT.md"]
        (out_dir / "AGENTS.md").write_text(f"# {ws_name}\n\nRouting catalog.\n", encoding="utf-8")
        (out_dir / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
        (out_dir / "CONTEXT.md").write_text(f"# {template}: {ws_name}\n", encoding="utf-8")
        stages = ["01-discovery", "02-mapping", "03-scaffolding"]
        for s in stages:
            s_dir = out_dir / "stages" / s
            (s_dir / "output").mkdir(parents=True, exist_ok=True)
            (s_dir / "CONTEXT.md").write_text(f"# {s} Contract\n\n## Inputs\n## Process\n## Outputs\n## Check\n", encoding="utf-8")
            files.append(f"stages/{s}/CONTEXT.md")
        return files
