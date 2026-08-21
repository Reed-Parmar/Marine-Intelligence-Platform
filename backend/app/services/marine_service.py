"""
Marine Service: Cross-domain unified marine observation aggregation and spatial querying.
Uses SQLAlchemy parameterized queries.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.database import execute_query, execute_single
from backend.app.db.queries import (
    COUNT_UNIFIED_MARINE_OBSERVATIONS,
    GET_MARINE_SUMMARY,
    GET_UNIFIED_MARINE_OBSERVATIONS
)
from backend.app.schemas.marine import (
    MarineObservationItem,
    MarineQueryRequest,
    MarineSummaryResponse
)


class MarineService:

    @staticmethod
    def get_unified_observations(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        dataset_id: Optional[str] = None,
        species_id: Optional[str] = None,
        depth_min: Optional[float] = None,
        depth_max: Optional[float] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[MarineObservationItem], int]:
        """
        Retrieves unified observations across oceanography, fisheries, and biodiversity domains.
        Executes a matching COUNT query to return the true total.
        """
        offset = (page - 1) * page_size
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "dataset_id": dataset_id,
            "species_id": species_id,
            "depth_min": depth_min,
            "depth_max": depth_max,
            "limit": page_size,
            "offset": offset
        }
        
        count_res = execute_single(COUNT_UNIFIED_MARINE_OBSERVATIONS, params)
        total = count_res["total"] if count_res else 0

        rows = execute_query(GET_UNIFIED_MARINE_OBSERVATIONS, params)
        
        items = [
            MarineObservationItem(
                id=str(r["id"]),
                domain=r["domain"],
                dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
                latitude=float(r["latitude"]),
                longitude=float(r["longitude"]),
                depth=float(r["depth"]) if r.get("depth") is not None else None,
                time=str(r["time"]) if r.get("time") else None,
                species_id=str(r["species_id"]) if r.get("species_id") else None,
                species_name=r.get("species_name"),
                measurements=r.get("measurements") or {}
            )
            for r in rows
        ]
        return items, total

    @staticmethod
    def get_marine_summary() -> MarineSummaryResponse:
        """Retrieves aggregate platform summary across all domains."""
        r = execute_single(GET_MARINE_SUMMARY)
        if not r:
            return MarineSummaryResponse(
                total_datasets=0,
                oceanography_count=0,
                fisheries_count=0,
                biodiversity_count=0,
                total_species=0
            )
        return MarineSummaryResponse(
            total_datasets=r.get("total_datasets", 0),
            oceanography_count=r.get("oceanography_count", 0),
            fisheries_count=r.get("fisheries_count", 0),
            biodiversity_count=r.get("biodiversity_count", 0),
            total_species=r.get("total_species", 0)
        )

    @staticmethod
    def query_marine(req: MarineQueryRequest) -> Tuple[List[MarineObservationItem], int]:
        """
        Executes structured multi-dimensional query across oceanography, fisheries, and occurrences.
        Applies date, dataset, species, and depth constraints.
        """
        return MarineService.get_unified_observations(
            date_from=req.date_from,
            date_to=req.date_to,
            dataset_id=req.dataset_id,
            species_id=req.species_id,
            depth_min=req.depth_min,
            depth_max=req.depth_max,
            page=req.page,
            page_size=req.page_size
        )
