"""Project trust evaluator, path confinement, and sensitive asset auditing."""

from __future__ import annotations

import os
from pathlib import Path

from harness.services.tau_bridge.models import TrustScope


class ProjectTrustEvaluator:
    """Evaluates workspace boundaries, detects Git roots, and verifies path confinement."""

    DEFAULT_SENSITIVE_PATTERNS = (
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials.json",
        "service_account.json",
        "id_rsa",
        "id_ed25519",
        ".git/config",
    )

    SENSITIVE_DIRS = (
        ".secrets",
        ".aws",
        ".ssh",
    )

    @classmethod
    def is_path_confined(
        cls, target_path: str | Path, root_path: str | Path
    ) -> bool:
        """Verify target path does not escape root path via directory traversal."""
        try:
            r = Path(root_path).resolve()
            t = Path(target_path).resolve()
            return t == r or r in t.parents
        except Exception:
            return False

    @classmethod
    def evaluate(
        cls,
        project_path: str,
        trusted_roots: list[str] | None = None,
        custom_sensitive_patterns: tuple[str, ...] | None = None,
    ) -> TrustScope:
        """Evaluate project security posture, directory traversal, and sensitive assets."""
        try:
            p = Path(project_path).resolve()
        except Exception:
            p = Path(os.path.abspath(project_path))

        warnings: list[str] = []
        git_root: str | None = None

        # Search for .git root by traversing up
        curr = p
        while curr != curr.parent:
            if (curr / ".git").is_dir():
                git_root = str(curr)
                break
            curr = curr.parent

        if git_root is None:
            warnings.append(
                "Project is not contained inside a recognized Git repository."
            )

        patterns = custom_sensitive_patterns or cls.DEFAULT_SENSITIVE_PATTERNS
        detected_sensitive: list[str] = []

        if p.exists() and p.is_dir():
            # Depth 1 check
            for pat in patterns:
                target = p / pat
                if target.exists():
                    detected_sensitive.append(pat)

            # Depth 2 check for sensitive directories
            for sdir in cls.SENSITIVE_DIRS:
                target_dir = p / sdir
                if target_dir.exists() and target_dir.is_dir():
                    detected_sensitive.append(f"{sdir}/")

        # Trust evaluation
        is_trusted = False
        if trusted_roots:
            for tr in trusted_roots:
                if cls.is_path_confined(p, tr):
                    is_trusted = True
                    break
        else:
            # Default heuristic: Git root exists and no private keys
            has_private_keys = any(
                s in detected_sensitive for s in ("id_rsa", "id_ed25519")
            )
            is_trusted = (git_root is not None) and not has_private_keys

        if detected_sensitive:
            warnings.append(
                f"Detected sensitive assets in project: {', '.join(detected_sensitive)}"
            )

        permission_level = "TRUSTED" if is_trusted else "RESTRICTED"
        if any(s in detected_sensitive for s in ("id_rsa", "id_ed25519")):
            permission_level = "BLOCKED"
            warnings.append(
                "Sensitive SSH private keys detected. Workspace execution blocked."
            )

        return TrustScope(
            project_path=str(p),
            is_trusted=is_trusted and permission_level != "BLOCKED",
            git_root=git_root,
            protected_assets=tuple(detected_sensitive),
            warnings=tuple(warnings),
            permission_level=permission_level,
        )


__all__ = [
    "ProjectTrustEvaluator",
]
