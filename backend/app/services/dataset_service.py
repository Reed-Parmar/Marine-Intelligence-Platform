"""
Dataset Service for listing, fetching, updating, and analyzing datasets.
Uses SQLAlchemy database layer with named parameter dictionaries.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.database import execute_query, execute_single, execute_write
from backend.app.db.queries import (
    GET_DATASETS_BASE,
    GET_DATASET_BY_ID,
    INSERT_DATASET,
    UPDATE_DATASET_METADATA,
    DELETE_DATASET
)
from backend.app.schemas.dataset import (
    DatasetCreateRequest,
    DatasetPreviewResponse,
    DatasetProvenanceResponse,
    DatasetQualityResponse,
    DatasetResponse,
    DatasetUpdateRequest
)


class DatasetService:

    @staticmethod
    def _nullable_uuid(value: Any) -> Optional[str]:
        """Return clean UUID string or None if blank/invalid."""
        if value is None:
            return None
        val_str = str(value).strip()
        if not val_str:
            return None
        try:
            return str(uuid.UUID(val_str))
        except (ValueError, TypeError, AttributeError):
            return None

    @staticmethod
    def normalize_domain_type(domain_type: Optional[str]) -> str:
        """Normalizes diverse domain aliases to canonical database domain values."""
        if not domain_type:
            return "oceanography"
        d = str(domain_type).strip().lower()
        if d in ["molecular_edna", "edna", "dna", "metabarcoding", "molecular"]:
            return "molecular_edna"
        if d in ["biodiversity", "bio", "species", "occurrence"]:
            return "biodiversity"
        if d in ["oceanography", "ocean", "ctd", "hydrography"]:
            return "oceanography"
        if d in ["fisheries", "fish", "catch", "commercial"]:
            return "fisheries"
        if d in ["otolith"]:
            return "otolith"
        if d in ["cross_domain", "cross"]:
            return "cross_domain"
        return d

    @staticmethod
    def list_datasets(
        domain_type: Optional[str] = None,
        status: Optional[str] = None,
        quality_status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DatasetResponse], int]:
        """Lists datasets with optional filtering and pagination."""
        conditions = []
        params: Dict[str, Any] = {}

        if domain_type:
            norm_domain = DatasetService.normalize_domain_type(domain_type)
            if norm_domain in ("molecular_edna", "edna"):
                conditions.append("(d.domain_type = 'molecular_edna'::public.dataset_domain OR d.domain_type = 'edna'::public.dataset_domain)")
            else:
                conditions.append("d.domain_type = :domain_type::public.dataset_domain")
                params["domain_type"] = norm_domain
        if status:
            conditions.append("d.status = :status::public.processing_status")
            params["status"] = status
        if quality_status:
            conditions.append("d.quality_status = :quality_status::public.quality_flag")
            params["quality_status"] = quality_status
        if search:
            conditions.append("d.name ILIKE :search_pattern")
            params["search_pattern"] = f"%{search}%"

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Count query
        count_query = f"SELECT COUNT(*) as total FROM public.datasets d {where_clause};"
        count_res = execute_single(count_query, params)
        total = count_res["total"] if count_res else 0

        # Data query
        offset = (page - 1) * page_size
        params["limit"] = page_size
        params["offset"] = offset
        data_query = GET_DATASETS_BASE + where_clause + " ORDER BY d.created_at DESC LIMIT :limit OFFSET :offset;"
        rows = execute_query(data_query, params)

        datasets = [
            DatasetResponse(
                id=str(r["id"]),
                project_id=str(r["project_id"]) if r.get("project_id") else None,
                data_source_id=str(r["data_source_id"]) if r.get("data_source_id") else None,
                name=r["name"],
                domain_type=r["domain_type"],
                storage_file_path=r.get("storage_file_path"),
                file_type=r.get("file_type"),
                file_size_bytes=r.get("file_size_bytes"),
                row_count=r.get("row_count"),
                uploaded_by=str(r["uploaded_by"]) if r.get("uploaded_by") else None,
                status=r.get("status", "uploaded"),
                quality_status=r.get("quality_status", "pending"),
                quality_score=float(r["quality_score"]) if r.get("quality_score") is not None else None,
                validation_notes=r.get("validation_notes"),
                provenance_metadata=r.get("provenance_metadata"),
                project_name=r.get("project_name"),
                source_name=r.get("source_name"),
                created_at=str(r["created_at"]) if r.get("created_at") else None,
                updated_at=str(r["updated_at"]) if r.get("updated_at") else None
            )
            for r in rows
        ]
        return datasets, total

    @staticmethod
    def get_dataset_by_id(dataset_id: str) -> Optional[DatasetResponse]:
        """Retrieves a single dataset by ID."""
        r = execute_single(GET_DATASET_BY_ID, {"dataset_id": dataset_id})
        if not r:
            return None
        return DatasetResponse(
            id=str(r["id"]),
            project_id=str(r["project_id"]) if r.get("project_id") else None,
            data_source_id=str(r["data_source_id"]) if r.get("data_source_id") else None,
            name=r["name"],
            domain_type=r["domain_type"],
            storage_file_path=r.get("storage_file_path"),
            file_type=r.get("file_type"),
            file_size_bytes=r.get("file_size_bytes"),
            row_count=r.get("row_count"),
            uploaded_by=str(r["uploaded_by"]) if r.get("uploaded_by") else None,
            status=r.get("status", "uploaded"),
            quality_status=r.get("quality_status", "pending"),
            quality_score=float(r["quality_score"]) if r.get("quality_score") is not None else None,
            validation_notes=r.get("validation_notes"),
            provenance_metadata=r.get("provenance_metadata"),
            project_name=r.get("project_name"),
            source_name=r.get("source_name"),
            created_at=str(r["created_at"]) if r.get("created_at") else None,
            updated_at=str(r["updated_at"]) if r.get("updated_at") else None
        )

    @staticmethod
    def create_dataset(req: DatasetCreateRequest, user_id: Optional[str] = None) -> Optional[DatasetResponse]:
        """Registers a new dataset."""
        dataset_id = str(uuid.uuid4())
        norm_domain = DatasetService.normalize_domain_type(req.domain_type)
        params = {
            "id": dataset_id,
            "project_id": DatasetService._nullable_uuid(req.project_id),
            "data_source_id": DatasetService._nullable_uuid(req.data_source_id),
            "name": req.name,
            "domain_type": norm_domain,
            "storage_file_path": req.storage_file_path,
            "file_type": req.file_type,
            "file_size_bytes": req.file_size_bytes,
            "row_count": req.row_count,
            "uploaded_by": DatasetService._nullable_uuid(user_id),
            "status": "uploaded",
            "quality_status": "pending",
            "quality_score": None,
            "validation_notes": None,
            "provenance_metadata": json.dumps(req.provenance_metadata or {})
        }
        r = execute_write(INSERT_DATASET, params)
        if not r:
            return None
        return DatasetService.get_dataset_by_id(dataset_id)

    @staticmethod
    def update_dataset(dataset_id: str, req: DatasetUpdateRequest) -> Optional[DatasetResponse]:
        """Updates editable dataset metadata."""
        norm_domain = DatasetService.normalize_domain_type(req.domain_type) if req.domain_type else None
        params = {
            "name": req.name,
            "domain_type": norm_domain,
            "quality_status": req.quality_status,
            "quality_score": req.quality_score,
            "validation_notes": req.validation_notes,
            "provenance_metadata": json.dumps(req.provenance_metadata) if req.provenance_metadata is not None else None,
            "status": req.status,
            "dataset_id": dataset_id
        }
        r = execute_write(UPDATE_DATASET_METADATA, params)
        if not r:
            return None
        return DatasetService.get_dataset_by_id(dataset_id)

    @staticmethod
    def delete_dataset(dataset_id: str) -> bool:
        """Deletes a dataset."""
        r = execute_write(DELETE_DATASET, {"dataset_id": dataset_id})
        return r is not None

    @staticmethod
    def get_dataset_quality(dataset_id: str) -> Optional[DatasetQualityResponse]:
        """Returns quality score and validation details."""
        ds = DatasetService.get_dataset_by_id(dataset_id)
        if not ds:
            return None
        
        provenance = ds.provenance_metadata or {}
        qc_summary = provenance.get("quality_summary", {})
        
        return DatasetQualityResponse(
            dataset_id=ds.id,
            quality_score=ds.quality_score,
            quality_status=ds.quality_status,
            validation_notes=ds.validation_notes,
            issues_summary=qc_summary.get("issues_by_severity"),
            deductions=qc_summary.get("deductions")
        )

    @staticmethod
    def get_dataset_provenance(dataset_id: str) -> Optional[DatasetProvenanceResponse]:
        """Returns provenance audit records."""
        ds = DatasetService.get_dataset_by_id(dataset_id)
        if not ds:
            return None
        return DatasetProvenanceResponse(
            dataset_id=ds.id,
            provenance_metadata=ds.provenance_metadata,
            storage_file_path=ds.storage_file_path,
            uploaded_by=ds.uploaded_by,
            created_at=ds.created_at
        )

    @staticmethod
    def get_dataset_preview(dataset_id: str) -> Optional[DatasetPreviewResponse]:
        """Returns tabular preview for a dataset, resolving file artifact or table observations."""
        from pathlib import Path
        from data_pipeline.ingestion.format_detector import detect_format_and_preview

        ds = DatasetService.get_dataset_by_id(dataset_id)
        if not ds:
            return None

        # 1. Try finding matching file artifact in dataset/ directory or local storage path
        candidate_paths = []
        if ds.storage_file_path:
            candidate_paths.append(Path(ds.storage_file_path))
            candidate_paths.append(Path("dataset") / Path(ds.storage_file_path).name)
        if ds.name:
            candidate_paths.append(Path("dataset") / ds.name)
            candidate_paths.append(Path("dataset") / f"{ds.name}.txt")
            candidate_paths.append(Path("dataset") / f"{ds.name}.csv")

        for p in candidate_paths:
            if p.exists() and p.is_file():
                try:
                    prev_info = detect_format_and_preview(str(p))
                    cols = [{"name": c, "type": "string"} for c in prev_info.get("columns", [])]
                    rows = prev_info.get("sample_rows", [])
                    return DatasetPreviewResponse(
                        dataset_id=dataset_id,
                        datasetId=dataset_id,
                        columns=cols,
                        rows=rows,
                        total_preview_rows=len(rows),
                        totalPreviewRows=len(rows)
                    )
                except Exception:
                    pass

        # 2. Fallback: Query observations from domain table
        domain = (ds.domain_type or "").lower()
        rows = []
        try:
            if "ocean" in domain:
                obs = execute_query("SELECT * FROM public.oceanographic_observations WHERE dataset_id = :did LIMIT 20;", {"did": dataset_id})
                rows = [dict(r) for r in obs]
            elif "fish" in domain:
                obs = execute_query("SELECT * FROM public.fisheries_records WHERE dataset_id = :did LIMIT 20;", {"did": dataset_id})
                rows = [dict(r) for r in obs]
            elif "bio" in domain:
                obs = execute_query("SELECT * FROM public.species_occurrences WHERE dataset_id = :did LIMIT 20;", {"did": dataset_id})
                rows = [dict(r) for r in obs]
            elif "edna" in domain:
                obs = execute_query("SELECT * FROM public.edna_samples WHERE dataset_id = :did LIMIT 20;", {"did": dataset_id})
                rows = [dict(r) for r in obs]
        except Exception:
            rows = []

        if not rows:
            # Default preview based on dataset metadata
            q_score = ds.quality_score if ds.quality_score is not None else 95.0
            rows = [
                {"id": f"{dataset_id}-01", "name": ds.name, "domain": ds.domain_type, "quality_score": q_score, "status": ds.status}
            ]

        col_keys = list(rows[0].keys()) if rows else ["id", "name", "domain", "status"]
        columns = [{"name": k, "type": "string"} for k in col_keys]

        return DatasetPreviewResponse(
            dataset_id=dataset_id,
            datasetId=dataset_id,
            columns=columns,
            rows=rows,
            total_preview_rows=len(rows),
            totalPreviewRows=len(rows)
        )
