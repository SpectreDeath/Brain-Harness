"""Multi-layer spatial analyst query pipeline and conversational session execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models import AnalystQueryResult
from ..query_pipeline import SpatialQueryPipeline

if TYPE_CHECKING:
    from .core import GodsEyeViewEngine


async def execute_analyst_query(
    engine: GodsEyeViewEngine,
    layer: str,
    filters: list[dict[str, Any]] | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = None,
    bbox: list[float] | None = None,
    polygon: list[tuple[float, float]] | None = None,
    follow_up_token: str | None = None,
    include_geojson: bool = True,
) -> AnalystQueryResult:
    """Execute multi-layer spatial query pipeline with session memory and GeoJSON export."""
    records: list[dict[str, Any]] = []

    # 1. Retrieve from follow-up session or fresh layer fetch
    if follow_up_token:
        cached_session = engine.session_store.get_session(follow_up_token)
        if cached_session is not None:
            records = cached_session
        else:
            return AnalystQueryResult(status="error", layer=layer, total_matched=0, items=[])
    else:
        layer_norm = layer.lower().strip()
        if layer_norm in ["flights", "flight"]:
            flist = await engine.fetch_flights(limit=500)
            records = [f.model_dump() for f in flist]
        elif layer_norm in ["military", "military-flights"]:
            flist = await engine.fetch_flights(military_only=True, limit=500)
            records = [f.model_dump() for f in flist]
        elif layer_norm in ["ais-live-vessels", "vessels", "ships"]:
            vlist = await engine.fetch_vessels(limit=500)
            records = [v.model_dump() for v in vlist]
        elif layer_norm in ["earthquakes", "seismic"]:
            qlist = await engine.fetch_earthquakes(limit=500)
            records = [q.model_dump() for q in qlist]
        elif layer_norm in ["local-firms", "firms", "fires"]:
            hlist = await engine.fetch_firms_hotspots(limit=500)
            records = [h.model_dump() for h in hlist]
        elif layer_norm in ["infrastructure", "cables", "datacenters", "dams", "installations"]:
            infras = engine.query_infrastructure(infra_type="all", limit=500)
            records = [inf.model_dump() for inf in infras]
        else:
            return AnalystQueryResult(status="error", layer=layer, total_matched=0, items=[])

    # 2. Execute SpatialQueryPipeline filtering
    filtered_records = SpatialQueryPipeline.filter_records(
        records=records,
        filters=filters,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        bbox=bbox,
        polygon=polygon,
    )

    # 3. Compute statistical aggregations
    aggregations = SpatialQueryPipeline.compute_aggregations(filtered_records)

    # 4. Generate RFC 7946 GeoJSON export if requested
    geojson_data = (
        SpatialQueryPipeline.to_geojson(filtered_records, layer_name=layer)
        if include_geojson
        else None
    )

    # 5. Store session for follow-up chaining
    session_token = engine.session_store.save_session(filtered_records)

    return AnalystQueryResult(
        status="ok",
        layer=layer,
        total_matched=len(filtered_records),
        items=filtered_records[:100],
        aggregations=aggregations,
        geojson=geojson_data,
        follow_up_token=session_token,
    )


__all__ = [
    "execute_analyst_query",
]
