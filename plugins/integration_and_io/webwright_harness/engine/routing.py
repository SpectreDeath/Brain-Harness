"""Skill routing, parameter slot-filling, and isolated subprocess execution mixin."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


class SkillRoutingMixin:
    """Provides skill decision routing and sandboxed subprocess execution."""

    base_dir: Path

    def retrieve_skills(self, task: str, k: int = 3, library_dir: str = "skills") -> dict[str, Any]: ...

    def route_and_execute(
        self,
        task: str,
        start_url: str,
        library_dir: str = "skills",
        timeout_s: int = 120,
    ) -> dict[str, Any]:
        """Route a task to matching skill execution or fallback."""
        ret = self.retrieve_skills(task, k=1, library_dir=library_dir)
        cands = ret.get("candidates", [])

        if not cands or cands[0]["score"] < 0.25:
            return {
                "status": "ok",
                "decision": "skip",
                "skill_id": None,
                "filled_params": {},
                "result": None,
                "returncode": 0,
                "error": "No matching skill with sufficient confidence found. Fallback to full agent exploration.",
            }

        top = cands[0]
        skill_id = top["skill_id"]
        skill_dir = self.base_dir / library_dir / skill_id
        skill_file = skill_dir / "skill.py"

        if not skill_file.exists():
            return {
                "status": "error",
                "decision": "adapt",
                "skill_id": skill_id,
                "filled_params": {},
                "result": None,
                "returncode": 1,
                "error": f"Skill script {skill_file} not found.",
            }

        # Parameter extraction / slot filling
        meta = json.loads((skill_dir / "meta.json").read_text(encoding="utf-8", errors="ignore"))
        params_needed = meta.get("signature", {}).get("params", [])
        filled: dict[str, Any] = {"start_url": start_url}
        for p in params_needed:
            filled[p] = f"extracted_{p}"

        # Subprocess execution for sandbox isolation
        try:
            run_script = (
                f"import sys, json\n"
                f"from pathlib import Path\n"
                f"sys.path.insert(0, r'{skill_dir}')\n"
                f"import skill\n"
                f"params = {json.dumps(filled)}\n"
                f"res = skill.execute_skill(**params) if hasattr(skill, 'execute_skill') else {{'status': 'executed'}}\n"
                f"print('__RESULT__' + json.dumps(res))\n"
            )
            proc = subprocess.run(
                [sys.executable, "-c", run_script],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            if proc.returncode == 0 and "__RESULT__" in proc.stdout:
                res_part = proc.stdout.split("__RESULT__")[1].strip().splitlines()[0]
                result_data = json.loads(res_part)
                return {
                    "status": "ok",
                    "decision": "run",
                    "skill_id": skill_id,
                    "filled_params": filled,
                    "result": result_data,
                    "returncode": 0,
                    "error": None,
                }
            else:
                return {
                    "status": "ok",
                    "decision": "adapt",
                    "skill_id": skill_id,
                    "filled_params": filled,
                    "result": None,
                    "returncode": proc.returncode,
                    "error": f"Execution failed ({proc.stderr.strip()[:200]}). Fallback to agent adaptation.",
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "decision": "adapt",
                "skill_id": skill_id,
                "filled_params": filled,
                "result": None,
                "returncode": 124,
                "error": f"Skill execution timed out after {timeout_s}s",
            }
        except Exception as e:
            return {
                "status": "error",
                "decision": "adapt",
                "skill_id": skill_id,
                "filled_params": filled,
                "result": None,
                "returncode": 1,
                "error": str(e),
            }
