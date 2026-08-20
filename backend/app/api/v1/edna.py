"""
eDNA Router: Environmental DNA sample metadata and species detections.
Uses real public.edna_samples and public.edna_results tables via SQLAlchemy.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.db.database import execute_query, execute_single
from backend.app.schemas.common import ApiListResponse, ApiMeta, ApiResponse
from backend.app.schemas.edna import EDNADetectionResponse, EDNASampleResponse

router = APIRouter()


@router.get("/samples", response_model=ApiListResponse[EDNASampleResponse])
async def list_edna_samples(
    dataset_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lists eDNA sampling events and sequence metadata from database.
    """
    conditions = []
    params: Dict[str, Any] = {}
    if dataset_id:
        conditions.append("dataset_id = :dataset_id")
        params["dataset_id"] = dataset_id
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    count_res = execute_single(f"SELECT COUNT(*) as total FROM public.edna_samples {where_clause};", params)
    total = count_res["total"] if count_res else 0

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    rows = execute_query(
        f"SELECT * FROM public.edna_samples {where_clause} ORDER BY collected_at DESC LIMIT :limit OFFSET :offset;",
        params
    )
    samples = [
        EDNASampleResponse(
            id=str(r["id"]),
            dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
            sample_code=r.get("sample_code", "EDNA-SAMPLE"),
            latitude=float(r["latitude"]),
            longitude=float(r["longitude"]),
            depth=float(r["depth"]) if r.get("depth") is not None else None,
            collected_at=str(r["collected_at"]) if r.get("collected_at") else None,
            sequencing_platform=r.get("sequencing_platform"),
            metadata=r.get("metadata")
        )
        for r in rows
    ]
    return ApiListResponse(
        data=samples,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )


@router.get("/detections", response_model=ApiListResponse[EDNADetectionResponse])
async def list_edna_detections(
    sample_id: Optional[str] = Query(None),
    species_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Returns eDNA detections and taxonomic matches from database.
    """
    conditions = []
    params: Dict[str, Any] = {}
    if sample_id:
        conditions.append("d.sample_id = :sample_id")
        params["sample_id"] = sample_id
    if species_id:
        conditions.append("d.species_id = :species_id")
        params["species_id"] = species_id
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    count_res = execute_single(f"SELECT COUNT(*) as total FROM public.edna_results d {where_clause};", params)
    total = count_res["total"] if count_res else 0

    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset
    query = f"""
    SELECT d.*, s.scientific_name 
    FROM public.edna_results d
    LEFT JOIN public.species s ON d.species_id = s.id
    {where_clause}
    LIMIT :limit OFFSET :offset;
    """
    rows = execute_query(query, params)
    detections = [
        EDNADetectionResponse(
            id=str(r["id"]),
            sample_id=str(r["sample_id"]),
            species_id=str(r["species_id"]) if r.get("species_id") else None,
            scientific_name=r.get("scientific_name"),
            read_count=r.get("read_count"),
            confidence_score=float(r["confidence_score"]) if r.get("confidence_score") is not None else None,
            metadata=r.get("metadata")
        )
        for r in rows
    ]
    return ApiListResponse(
        data=detections,
        meta=ApiMeta(page=page, page_size=page_size, total=total)
    )
