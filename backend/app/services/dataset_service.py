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
    DatasetProvenanceResponse,
    DatasetQualityResponse,
    DatasetResponse,
    DatasetUpdateRequest
)


class DatasetService:

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
            conditions.append("d.domain_type = :domain_type")
            params["domain_type"] = domain_type
        if status:
            conditions.append("d.status = :status")
            params["status"] = status
        if quality_status:
            conditions.append("d.quality_status = :quality_status")
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
        params = {
            "id": dataset_id,
            "project_id": req.project_id,
            "data_source_id": req.data_source_id,
            "name": req.name,
            "domain_type": req.domain_type,
            "storage_file_path": req.storage_file_path,
            "file_type": req.file_type,
            "file_size_bytes": req.file_size_bytes,
            "row_count": req.row_count,
            "uploaded_by": user_id,
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
        params = {
            "name": req.name,
            "domain_type": req.domain_type,
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
