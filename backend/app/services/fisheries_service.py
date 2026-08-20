"""
Fisheries Service for catch records, gear/effort tracking, trends, and summary statistics.
Uses SQLAlchemy parameterized queries.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.database import execute_query, execute_single
from backend.app.db.queries import (
    GET_FISHERIES_OBSERVATIONS,
    GET_FISHERIES_OBSERVATION_BY_ID,
    GET_FISHERIES_SUMMARY,
    GET_FISHERIES_TRENDS
)
from backend.app.schemas.fisheries import (
    FisheriesObservationResponse,
    FisheriesSummaryResponse,
    FisheriesTrendItem,
    FisheriesTrendResponse
)


class FisheriesService:

    @staticmethod
    def list_observations(
        dataset_id: Optional[str] = None,
        species_id: Optional[str] = None,
        fishing_zone: Optional[str] = None,
        gear_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[FisheriesObservationResponse], int]:
        """Lists fisheries observations with filters and pagination."""
        conditions = []
        params: Dict[str, Any] = {}

        if dataset_id:
            conditions.append("f.dataset_id = :dataset_id")
            params["dataset_id"] = dataset_id
        if species_id:
            conditions.append("f.species_id = :species_id")
            params["species_id"] = species_id
        if fishing_zone:
            conditions.append("f.fishing_zone = :fishing_zone")
            params["fishing_zone"] = fishing_zone
        if gear_type:
            conditions.append("f.gear_type = :gear_type")
            params["gear_type"] = gear_type
        if date_from:
            conditions.append("f.recorded_at >= :date_from::timestamptz")
            params["date_from"] = date_from
        if date_to:
            conditions.append("f.recorded_at <= :date_to::timestamptz")
            params["date_to"] = date_to

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        count_query = f"SELECT COUNT(*) as total FROM public.fisheries_records f {where_clause};"
        count_res = execute_single(count_query, params)
        total = count_res["total"] if count_res else 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        data_query = GET_FISHERIES_OBSERVATIONS + where_clause + " ORDER BY f.recorded_at DESC LIMIT :limit OFFSET :offset;"
        rows = execute_query(data_query, params)

        observations = [
            FisheriesObservationResponse(
                id=str(r["id"]),
                dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
                species_id=str(r["species_id"]) if r.get("species_id") else None,
                scientific_name=r.get("scientific_name"),
                common_name=r.get("common_name"),
                latitude=float(r["latitude"]),
                longitude=float(r["longitude"]),
                recorded_at=str(r["recorded_at"]) if r.get("recorded_at") else None,
                catch_weight_kg=float(r["catch_weight_kg"]) if r.get("catch_weight_kg") is not None else None,
                effort_hours=float(r["effort_hours"]) if r.get("effort_hours") is not None else None,
                gear_type=r.get("gear_type"),
                fishing_zone=r.get("fishing_zone"),
                vessel_name=r.get("vessel_name"),
                metadata=r.get("metadata")
            )
            for r in rows
        ]
        return observations, total

    @staticmethod
    def get_observation_by_id(observation_id: str) -> Optional[FisheriesObservationResponse]:
        """Retrieves a single fisheries observation by ID."""
        r = execute_single(GET_FISHERIES_OBSERVATION_BY_ID, {"observation_id": observation_id})
        if not r:
            return None
        return FisheriesObservationResponse(
            id=str(r["id"]),
            dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
            species_id=str(r["species_id"]) if r.get("species_id") else None,
            scientific_name=r.get("scientific_name"),
            common_name=r.get("common_name"),
            latitude=float(r["latitude"]),
            longitude=float(r["longitude"]),
            recorded_at=str(r["recorded_at"]) if r.get("recorded_at") else None,
            catch_weight_kg=float(r["catch_weight_kg"]) if r.get("catch_weight_kg") is not None else None,
            effort_hours=float(r["effort_hours"]) if r.get("effort_hours") is not None else None,
            gear_type=r.get("gear_type"),
            fishing_zone=r.get("fishing_zone"),
            vessel_name=r.get("vessel_name"),
            metadata=r.get("metadata")
        )

    @staticmethod
    def get_fisheries_summary(date_from: Optional[str] = None, date_to: Optional[str] = None) -> FisheriesSummaryResponse:
        """Calculates aggregate fisheries catch and effort statistics."""
        params = {"date_from": date_from, "date_to": date_to}
        r = execute_single(GET_FISHERIES_SUMMARY, params)
        if not r:
            return FisheriesSummaryResponse(total_records=0)
        return FisheriesSummaryResponse(
            total_records=r.get("total_records", 0),
            total_catch_kg=float(r["total_catch_kg"]) if r.get("total_catch_kg") is not None else None,
            avg_catch_kg=round(float(r["avg_catch_kg"]), 2) if r.get("avg_catch_kg") is not None else None,
            total_effort_hours=float(r["total_effort_hours"]) if r.get("total_effort_hours") is not None else None,
            distinct_species_count=r.get("distinct_species_count", 0),
            distinct_zones_count=r.get("distinct_zones_count", 0)
        )

    @staticmethod
    def get_fisheries_trends(
        interval: str = "month",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> FisheriesTrendResponse:
        """Retrieves aggregated time-series trends for fisheries catch."""
        valid_intervals = {"day", "week", "month", "year"}
        bucket_interval = interval if interval in valid_intervals else "month"
        params = {
            "interval": bucket_interval,
            "date_from": date_from,
            "date_to": date_to
        }
        rows = execute_query(GET_FISHERIES_TRENDS, params)
        trends = [
            FisheriesTrendItem(
                time_bucket=str(r["time_bucket"]),
                record_count=r.get("record_count", 0),
                total_catch_kg=round(float(r["total_catch_kg"]), 2) if r.get("total_catch_kg") is not None else None,
                avg_catch_kg=round(float(r["avg_catch_kg"]), 2) if r.get("avg_catch_kg") is not None else None,
                total_effort_hours=round(float(r["total_effort_hours"]), 2) if r.get("total_effort_hours") is not None else None
            )
            for r in rows
        ]
        return FisheriesTrendResponse(trends=trends)
