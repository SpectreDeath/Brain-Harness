"""Ontology-Spider Plugin for Brain Harness.

Provides formal logic reasoning, multi-hop dependency traversal, and schema validation
over Brain Harness vaults through the Ontology-Spider ModelSource seam.
"""

from __future__ import annotations

from .adapter import HarnessVaultModelSource
from .main import OntologySpiderPlugin, plugin
from .service import OntologySpiderService

__all__ = [
    "HarnessVaultModelSource",
    "OntologySpiderPlugin",
    "OntologySpiderService",
    "plugin",
]
