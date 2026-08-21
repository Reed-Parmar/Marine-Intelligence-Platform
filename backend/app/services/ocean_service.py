"""
Oceanography Service for ocean observations, trends, and summary statistics.
Uses SQLAlchemy parameterized queries.
"""

from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from backend.app.db.database import execute_query, execute_single
from backend.app.db.queries import (
    GET_OCEAN_OBSERVATIONS,
    GET_OCEAN_OBSERVATION_BY_ID,
    GET_OCEAN_SUMMARY,
    GET_OCEAN_TRENDS
)
from backend.app.schemas.ocean import (
    CTDProfilePointResponse,
    OceanObservationResponse,
    OceanSummaryResponse,
    OceanTrendItem,
    OceanTrendResponse
)


class OceanService:

    @staticmethod
    def list_observations(
        dataset_id: Optional[str] = None,
        station_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        depth_min: Optional[float] = None,
        depth_max: Optional[float] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[OceanObservationResponse], int]:
        """Lists oceanographic observations with deterministic secondary sort and pagination."""
        conditions = []
        params: Dict[str, Any] = {}

        if dataset_id:
            conditions.append("o.dataset_id = :dataset_id")
            params["dataset_id"] = dataset_id
        if station_id:
            conditions.append("o.station_id = :station_id")
            params["station_id"] = station_id
        if date_from:
            conditions.append("o.observed_at >= :date_from::timestamptz")
            params["date_from"] = date_from
        if date_to:
            conditions.append("o.observed_at <= :date_to::timestamptz")
            params["date_to"] = date_to
        if depth_min is not None:
            conditions.append("o.depth >= :depth_min")
            params["depth_min"] = depth_min
        if depth_max is not None:
            conditions.append("o.depth <= :depth_max")
            params["depth_max"] = depth_max

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        count_query = f"SELECT COUNT(*) as total FROM public.oceanographic_observations o {where_clause};"
        count_res = execute_single(count_query, params)
        total = count_res["total"] if count_res else 0

        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        data_query = GET_OCEAN_OBSERVATIONS + where_clause + " ORDER BY o.observed_at DESC NULLS LAST, o.id ASC LIMIT :limit OFFSET :offset;"
        rows = execute_query(data_query, params)

        observations = [
            OceanObservationResponse(
                id=str(r["id"]),
                dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
                station_id=r.get("station_id"),
                sample_id=r.get("sample_id"),
                latitude=float(r["latitude"]),
                longitude=float(r["longitude"]),
                depth=float(r["depth"]) if r.get("depth") is not None else None,
                observed_at=str(r["observed_at"]) if r.get("observed_at") else None,
                temperature=float(r["temperature"]) if r.get("temperature") is not None else None,
                salinity=float(r["salinity"]) if r.get("salinity") is not None else None,
                dissolved_oxygen=float(r["dissolved_oxygen"]) if r.get("dissolved_oxygen") is not None else None,
                chlorophyll=float(r["chlorophyll"]) if r.get("chlorophyll") is not None else None,
                ph=float(r["ph"]) if r.get("ph") is not None else None,
                pressure=float(r["pressure"]) if r.get("pressure") is not None else None,
                turbidity=float(r["turbidity"]) if r.get("turbidity") is not None else None,
                conductivity=float(r["conductivity"]) if r.get("conductivity") is not None else None,
                quality_flag=r.get("quality_flag"),
                metadata=r.get("metadata")
            )
            for r in rows
        ]
        return observations, total

    @staticmethod
    def get_observation_by_id(observation_id: str) -> Optional[OceanObservationResponse]:
        """Retrieves a single ocean observation by ID."""
        r = execute_single(GET_OCEAN_OBSERVATION_BY_ID, {"observation_id": observation_id})
        if not r:
            return None
        return OceanObservationResponse(
            id=str(r["id"]),
            dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
            station_id=r.get("station_id"),
            sample_id=r.get("sample_id"),
            latitude=float(r["latitude"]),
            longitude=float(r["longitude"]),
            depth=float(r["depth"]) if r.get("depth") is not None else None,
            observed_at=str(r["observed_at"]) if r.get("observed_at") else None,
            temperature=float(r["temperature"]) if r.get("temperature") is not None else None,
            salinity=float(r["salinity"]) if r.get("salinity") is not None else None,
            dissolved_oxygen=float(r["dissolved_oxygen"]) if r.get("dissolved_oxygen") is not None else None,
            chlorophyll=float(r["chlorophyll"]) if r.get("chlorophyll") is not None else None,
            ph=float(r["ph"]) if r.get("ph") is not None else None,
            pressure=float(r["pressure"]) if r.get("pressure") is not None else None,
            turbidity=float(r["turbidity"]) if r.get("turbidity") is not None else None,
            conductivity=float(r["conductivity"]) if r.get("conductivity") is not None else None,
            quality_flag=r.get("quality_flag"),
            metadata=r.get("metadata")
        )

    @staticmethod
    def get_ocean_summary(date_from: Optional[str] = None, date_to: Optional[str] = None) -> OceanSummaryResponse:
        """Calculates aggregate oceanographic summary statistics."""
        params = {"date_from": date_from, "date_to": date_to}
        r = execute_single(GET_OCEAN_SUMMARY, params)
        if not r:
            return OceanSummaryResponse(total_observations=0)
        return OceanSummaryResponse(
            total_observations=r.get("total_observations", 0),
            min_temperature=float(r["min_temperature"]) if r.get("min_temperature") is not None else None,
            max_temperature=float(r["max_temperature"]) if r.get("max_temperature") is not None else None,
            avg_temperature=round(float(r["avg_temperature"]), 2) if r.get("avg_temperature") is not None else None,
            min_salinity=float(r["min_salinity"]) if r.get("min_salinity") is not None else None,
            max_salinity=float(r["max_salinity"]) if r.get("max_salinity") is not None else None,
            avg_salinity=round(float(r["avg_salinity"]), 2) if r.get("avg_salinity") is not None else None,
            min_dissolved_oxygen=float(r["min_dissolved_oxygen"]) if r.get("min_dissolved_oxygen") is not None else None,
            max_dissolved_oxygen=float(r["max_dissolved_oxygen"]) if r.get("max_dissolved_oxygen") is not None else None,
            avg_dissolved_oxygen=round(float(r["avg_dissolved_oxygen"]), 2) if r.get("avg_dissolved_oxygen") is not None else None,
            min_depth=float(r["min_depth"]) if r.get("min_depth") is not None else None,
            max_depth=float(r["max_depth"]) if r.get("max_depth") is not None else None
        )

    @staticmethod
    def get_ocean_trends(
        variable: str = "temperature",
        interval: str = "month",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> OceanTrendResponse:
        """Retrieves aggregated time-series trends for oceanographic variables."""
        valid_variables = {"temperature", "salinity", "dissolved_oxygen", "chlorophyll"}
        if variable not in valid_variables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_VARIABLE", "message": f"Variable must be one of: {', '.join(sorted(valid_variables))}"}
            )

        valid_intervals = {"day", "week", "month", "year"}
        bucket_interval = interval if interval in valid_intervals else "month"
        params = {
            "interval": bucket_interval,
            "date_from": date_from,
            "date_to": date_to
        }
        rows = execute_query(GET_OCEAN_TRENDS, params)
        trends = [
            OceanTrendItem(
                time_bucket=str(r["time_bucket"]),
                observation_count=r.get("observation_count", 0),
                avg_temperature=round(float(r["avg_temperature"]), 2) if r.get("avg_temperature") is not None else None,
                avg_salinity=round(float(r["avg_salinity"]), 2) if r.get("avg_salinity") is not None else None,
                avg_dissolved_oxygen=round(float(r["avg_dissolved_oxygen"]), 2) if r.get("avg_dissolved_oxygen") is not None else None,
                avg_chlorophyll=round(float(r["avg_chlorophyll"]), 2) if r.get("avg_chlorophyll") is not None else None
            )
            for r in rows
        ]
        return OceanTrendResponse(variable=variable, trends=trends)

    @staticmethod
    def get_ctd_profile(
        station_id: Optional[str] = None,
        dataset_id: Optional[str] = None
    ) -> List[CTDProfilePointResponse]:
        """Retrieves depth-sorted CTD profile measurements."""
        conditions = ["o.depth IS NOT NULL"]
        params: Dict[str, Any] = {}
        if station_id:
            conditions.append("o.station_id = :station_id")
            params["station_id"] = station_id
        if dataset_id:
            conditions.append("o.dataset_id = :dataset_id")
            params["dataset_id"] = dataset_id

        where_clause = " WHERE " + " AND ".join(conditions)
        query = f"""
        SELECT o.depth, o.temperature, o.salinity, o.dissolved_oxygen, o.chlorophyll, o.station_id
        FROM public.oceanographic_observations o
        {where_clause}
        ORDER BY o.depth ASC
        LIMIT 50;
        """
        try:
            rows = execute_query(query, params)
        except Exception:
            rows = []

        if not rows:
            return []

        profile_points = []
        for r in rows:
            d = float(r["depth"])
            t = float(r["temperature"]) if r.get("temperature") is not None else None
            s = float(r["salinity"]) if r.get("salinity") is not None else None
            do_val = float(r["dissolved_oxygen"]) if r.get("dissolved_oxygen") is not None else None
            chl_val = float(r["chlorophyll"]) if r.get("chlorophyll") is not None else None
            sigma_t = None
            if s is not None and t is not None:
                sigma_t = round(22.0 + (s - 34.0) * 0.7 - (t - 25.0) * 0.25, 2)

            profile_points.append(
                CTDProfilePointResponse(
                    depth=d,
                    temperature=t,
                    salinity=s,
                    dissolvedOxygen=do_val,
                    dissolved_oxygen=do_val,
                    chlorophyllA=chl_val,
                    chlorophyll=chl_val,
                    densitySigmaT=sigma_t,
                    stationId=r.get("station_id") or station_id,
                    station_id=r.get("station_id") or station_id
                )
            )
        return profile_points
