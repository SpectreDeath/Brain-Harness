"""Trajectory skill learning and output schema deduction mixin."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


class SkillLearningMixin:
    """Provides execution trajectory analysis and parameterized skill code synthesis."""

    base_dir: Path

    def learn_skill(
        self,
        trajectory_dirs: list[str],
        template: str,
        library_dir: str = "skills",
    ) -> dict[str, Any]:
        """Synthesize a reusable Python web automation skill from execution trajectories."""
        if not trajectory_dirs:
            return {
                "status": "error",
                "error": "trajectory_dirs cannot be empty",
            }

        resolved_lib = self.base_dir / library_dir
        resolved_lib.mkdir(parents=True, exist_ok=True)

        extracted_params = re.findall(r"\{([a-zA-Z0-9_]+)\}", template)

        # Collect scripts and responses from trajectories
        scripts: list[str] = []
        answers: list[Any] = []

        for tdir in trajectory_dirs:
            p = Path(tdir)
            if not p.is_absolute():
                p = self.base_dir / p

            script_file = p / "final_script.py"
            resp_file = p / "agent_response.json"

            if script_file.exists():
                scripts.append(script_file.read_text(encoding="utf-8", errors="ignore"))
            if resp_file.exists():
                try:
                    data = json.loads(resp_file.read_text(encoding="utf-8", errors="ignore"))
                    answers.append(data.get("retrieved_data", data))
                except Exception:
                    pass

        # Synthesize skill ID
        content_hash = hashlib.sha256(f"{template}:{len(scripts)}".encode("utf-8")).hexdigest()[:8]
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", template.strip().lower())[:30].strip("_")
        skill_id = f"{slug}_{content_hash}"

        skill_dir = resolved_lib / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Build parameterized skill code
        primary_script = scripts[0] if scripts else (
            "def solve(params):\n"
            "    print(f'Executing skill for params: {params}')\n"
            "    return {'status': 'completed', 'params': params}\n"
        )

        skill_py_path = skill_dir / "skill.py"
        skill_code = (
            f"# Webwright Synthesized Skill: {skill_id}\n"
            f"# Template: {template}\n\n"
            f"from __future__ import annotations\n"
            f"from typing import Any\n\n"
            f"{primary_script}\n\n"
            f"def execute_skill(**kwargs: Any) -> Any:\n"
            f"    return solve(kwargs) if 'solve' in globals() else kwargs\n"
        )
        skill_py_path.write_text(skill_code, encoding="utf-8")

        output_schema = self._infer_output_schema(answers)
        signature = {
            "template": template,
            "params": extracted_params,
            "required": extracted_params,
        }

        meta = {
            "skill_id": skill_id,
            "template": template,
            "summary": f"Learned skill for '{template}' across {len(trajectory_dirs)} trajectories",
            "signature": signature,
            "output_schema": output_schema,
            "trajectories_count": len(trajectory_dirs),
        }
        (skill_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        (skill_dir / "signature.json").write_text(json.dumps(signature, indent=2), encoding="utf-8")

        return {
            "status": "ok",
            "skill_id": skill_id,
            "file_path": str(skill_py_path),
            "signature": signature,
            "output_schema": output_schema,
            "error": None,
        }

    def _infer_output_schema(self, answers: list[Any]) -> dict[str, Any]:
        """Mechanically deduce schema from answers."""
        if not answers:
            return {"type": "object"}
        sample = answers[0]
        if isinstance(sample, list):
            item = sample[0] if sample else ""
            t = (
                "number"
                if isinstance(item, (int, float)) and not isinstance(item, bool)
                else "object"
                if isinstance(item, dict)
                else "string"
            )
            return {"type": "array", "items": {"type": t}}
        if isinstance(sample, (int, float)) and not isinstance(sample, bool):
            return {"type": "number"}
        if isinstance(sample, dict):
            return {"type": "object", "properties": {k: {"type": type(v).__name__} for k, v in sample.items()}}
        return {"type": "string"}
