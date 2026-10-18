"""Reconstruction Obligation Ledger Plugin for Brain Harness.

Registers the ReconstructionObligationService into the micro-kernel IoC container,
enabling evidence-backed software reconstruction tracking, 8-state disposition FSMs,
and cryptographic closure verification.
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.reconstruction_obligation import (
    CanonicalEvidence,
    FacetAvailability,
    ObligationItem,
    RECONSTRUCTION_OBLIGATION_SERVICE_KEY,
    ReconstructionObligationService,
    ReconstructionProof,
    StandardReconstructionObligationService,
)

logger = structlog.get_logger(__name__)


class ReconstructionObligationLedgerPlugin(HarnessPlugin, ReconstructionObligationService):
    """Plugin providing authoritative reconstruction obligation ledger capabilities."""

    def __init__(self) -> None:
        self._service = StandardReconstructionObligationService()

    @property
    def name(self) -> str:
        return "plugin.reconstruction_obligation_ledger"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [RECONSTRUCTION_OBLIGATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(RECONSTRUCTION_OBLIGATION_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # ReconstructionObligationService Protocol Implementation
    # -------------------------------------------------------------------------

    def ingest_evidence(
        self,
        provider_id: str,
        subject_format: str,
        normalized_result: dict[str, Any] | str,
        raw_result: str | None = None,
        facet_availability: dict[str, FacetAvailability] | None = None,
        timestamp: str | None = None,
    ) -> CanonicalEvidence:
        return self._service.ingest_evidence(
            provider_id=provider_id,
            subject_format=subject_format,
            normalized_result=normalized_result,
            raw_result=raw_result,
            facet_availability=facet_availability,
            timestamp=timestamp,
        )

    def add_obligation(
        self,
        obligation_id: str,
        layer: str,
        case_kind: str,
        description: str,
        disposition: str = "unowned",
        evidence_ids: list[str] | None = None,
        owner_path: str | None = None,
        owner_sha256: str | None = None,
    ) -> ObligationItem:
        return self._service.add_obligation(
            obligation_id=obligation_id,
            layer=layer,
            case_kind=case_kind,
            description=description,
            disposition=disposition,
            evidence_ids=evidence_ids,
            owner_path=owner_path,
            owner_sha256=owner_sha256,
        )

    def transition_disposition(
        self,
        obligation_id: str,
        new_disposition: str,
        evidence_ids: list[str] | None = None,
        owner_path: str | None = None,
        owner_sha256: str | None = None,
    ) -> ObligationItem:
        return self._service.transition_disposition(
            obligation_id=obligation_id,
            new_disposition=new_disposition,
            evidence_ids=evidence_ids,
            owner_path=owner_path,
            owner_sha256=owner_sha256,
        )

    def verify_ledger(self, strict: bool = False) -> ReconstructionProof:
        return self._service.verify_ledger(strict=strict)

    def export_certificate(self) -> dict[str, Any]:
        return self._service.export_certificate()


plugin = ReconstructionObligationLedgerPlugin()
