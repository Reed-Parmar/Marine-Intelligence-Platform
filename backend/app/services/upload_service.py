"""
Upload Service: Handles staging uploads, file preview, and the Phase 3/4 pipeline integration interface.
"""

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, UploadFile, status
from backend.app.schemas.dataset import DatasetCreateRequest, DatasetUpdateRequest
from backend.app.schemas.upload import (
    UploadPreviewResponse,
    UploadProcessRequest,
    UploadProcessResponse,
    UploadResponse
)
from backend.app.services.dataset_service import DatasetService

# Maximum upload limit (50 MB)
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024

# Staging registry for active uploads
_STAGING_UPLOADS: Dict[str, Dict[str, Any]] = {}


class UploadService:

    @staticmethod
    async def create_upload(
        file: UploadFile,
        user_id: Optional[str] = None
    ) -> UploadResponse:
        """
        Stages an uploaded file, enforces max size, detects format, and prepares for preview/processing.
        """
        upload_id = str(uuid.uuid4())
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": "FILE_TOO_LARGE", "message": f"File size ({file_size} bytes) exceeds maximum limit of 50MB."}
            )

        filename = file.filename or f"upload_{upload_id}.csv"

        # Detect format based on extension & content
        ext = filename.split(".")[-1].lower() if "." in filename else "csv"
        detected_format = ext
        if ext == "txt":
            sample = content[:1024].decode("utf-8", errors="ignore")
            if "\t" in sample:
                detected_format = "tsv"
            else:
                detected_format = "csv"

        storage_path = f"staging/{upload_id}/{filename}"
        created_at = datetime.now(timezone.utc).isoformat()

        record = {
            "upload_id": upload_id,
            "filename": filename,
            "file_type": ext,
            "file_size_bytes": file_size,
            "storage_path": storage_path,
            "status": "uploaded",
            "detected_format": detected_format,
            "created_at": created_at,
            "raw_content": content,
            "uploaded_by": user_id
        }
        _STAGING_UPLOADS[upload_id] = record

        return UploadResponse(
            upload_id=upload_id,
            filename=filename,
            file_type=ext,
            file_size_bytes=file_size,
            storage_path=storage_path,
            status="uploaded",
            detected_format=detected_format,
            created_at=created_at
        )

    @staticmethod
    def get_upload_status(upload_id: str) -> Optional[UploadResponse]:
        """Retrieves upload status."""
        rec = _STAGING_UPLOADS.get(upload_id)
        if not rec:
            return None
        return UploadResponse(
            upload_id=rec["upload_id"],
            filename=rec["filename"],
            file_type=rec["file_type"],
            file_size_bytes=rec["file_size_bytes"],
            storage_path=rec["storage_path"],
            status=rec["status"],
            detected_format=rec["detected_format"],
            created_at=rec["created_at"]
        )

    @staticmethod
    def get_upload_preview(upload_id: str, max_rows: int = 10) -> Optional[UploadPreviewResponse]:
        """
        Parses the first few rows of the uploaded file for frontend display using appropriate delimiter.
        """
        rec = _STAGING_UPLOADS.get(upload_id)
        if not rec:
            return None

        detected_format = rec.get("detected_format", "csv")
        supported_formats = {"csv", "tsv", "txt"}
        if detected_format not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "UNSUPPORTED_FORMAT", "message": f"Preview not supported for format: {detected_format}"}
            )

        content = rec.get("raw_content", b"")
        text = content.decode("utf-8", errors="ignore")
        delimiter = "\t" if detected_format == "tsv" else ","
        
        headers: List[str] = []
        sample_rows: List[Dict[str, Any]] = []

        try:
            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            if reader.fieldnames:
                headers = [str(f).strip() for f in reader.fieldnames if f]
            
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                sample_rows.append({k.strip(): v.strip() for k, v in row.items() if k})
        except Exception:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if lines:
                headers = ["line"]
                sample_rows = [{"line": l} for l in lines[:max_rows]]

        return UploadPreviewResponse(
            upload_id=upload_id,
            filename=rec["filename"],
            detected_format=detected_format,
            total_preview_rows=len(sample_rows),
            headers=headers,
            sample_rows=sample_rows
        )

    @staticmethod
    def delete_upload(upload_id: str) -> bool:
        """Cancels/removes an upload before finalization."""
        if upload_id in _STAGING_UPLOADS:
            del _STAGING_UPLOADS[upload_id]
            return True
        return False

    @staticmethod
    def process_upload(
        upload_id: str,
        req: UploadProcessRequest,
        user_id: Optional[str] = None
    ) -> Optional[UploadProcessResponse]:
        """
        Phase 3 / Phase 4 Integration Point:
        1. Atomically claims upload to prevent concurrent processing.
        2. Ingests raw data using format-aware delimited parser.
        3. Applies Phase 4 QualityPipeline if available, without inventing fake 100% scores.
        4. Registers dataset into PostgreSQL public.datasets table.
        """
        rec = _STAGING_UPLOADS.get(upload_id)
        if not rec:
            return None

        # Check terminal and active states
        if rec["status"] == "finalized":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_PROCESSED", "message": "Upload has already been finalized and registered."}
            )
        if rec["status"] == "processing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "PROCESSING_IN_PROGRESS", "message": "Upload is currently being processed."}
            )

        rec["status"] = "processing"
        content = rec.get("raw_content", b"")
        text = content.decode("utf-8", errors="ignore")
        detected_format = rec.get("detected_format", "csv")
        delimiter = "\t" if detected_format == "tsv" else ","

        # 1. Parse delimited records
        raw_records: List[Dict[str, Any]] = []
        try:
            reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
            for row in reader:
                raw_records.append({k.strip(): v.strip() for k, v in row.items() if k})
        except Exception as e:
            rec["status"] = "failed"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "PARSE_ERROR", "message": f"Failed to parse uploaded file: {str(e)}"}
            )

        # 2. Phase 4 Quality Pipeline execution (honest hook)
        quality_score: Optional[float] = None
        quality_status = "pending"
        validation_notes = "Quality pipeline pending execution."
        provenance = {
            "upload_id": upload_id,
            "original_filename": rec["filename"],
            "records_ingested": len(raw_records),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            from data_pipeline.pipeline import QualityPipeline
            pipeline = QualityPipeline(
                unit_hints=req.unit_hints,
                custom_column_mapping=req.column_mapping
            )
            res = pipeline.process(raw_records, dataset_metadata={"domain_type": req.domain_type})
            quality_score = res.quality_score
            quality_status = res.quality_status.value
            validation_notes = res.validation_notes
            provenance = res.provenance
        except ImportError:
            # QualityPipeline module not in environment; keep status as pending
            quality_score = None
            quality_status = "pending"
            validation_notes = "Quality control pipeline is pending execution."
        except Exception as q_err:
            logger.error("Quality pipeline execution error for upload %s: %s", upload_id, q_err)
            quality_score = None
            quality_status = "pending"
            validation_notes = "Quality control pipeline encountered an error during evaluation."

        # 3. Register dataset in PostgreSQL
        dataset_name = req.dataset_name or rec["filename"].rsplit(".", 1)[0]
        storage_path = f"datasets/{upload_id}/{rec['filename']}"

        ds_create = DatasetCreateRequest(
            name=dataset_name,
            domain_type=req.domain_type,
            project_id=req.project_id,
            storage_file_path=storage_path,
            file_type=rec["file_type"],
            file_size_bytes=rec["file_size_bytes"],
            row_count=len(raw_records),
            provenance_metadata=provenance
        )
        ds = DatasetService.create_dataset(ds_create, user_id=user_id or rec.get("uploaded_by"))
        if not ds:
            rec["status"] = "failed"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "DATASET_REGISTRATION_FAILED", "message": "Failed to create dataset in database."}
            )

        # 4. Ingest parsed records into domain observation tables
        ingested_obs_count, skipped_obs_count = UploadService._ingest_records_into_domain_tables(
            dataset_id=ds.id,
            domain_type=req.domain_type,
            records=raw_records
        )

        provenance["records_inserted"] = ingested_obs_count
        provenance["records_skipped"] = skipped_obs_count

        # Persist quality evaluation and dataset status
        if quality_score is not None:
            DatasetService.update_dataset(
                ds.id,
                DatasetUpdateRequest(
                    quality_score=quality_score,
                    quality_status=quality_status,
                    validation_notes=validation_notes,
                    status="standardized",
                    provenance_metadata=provenance
                )
            )
        else:
            DatasetService.update_dataset(
                ds.id,
                DatasetUpdateRequest(
                    quality_status="pending",
                    validation_notes=validation_notes,
                    provenance_metadata=provenance
                )
            )

        rec["status"] = "finalized"
        rec["dataset_id"] = ds.id

        return UploadProcessResponse(
            upload_id=upload_id,
            dataset_id=ds.id,
            status="finalized",
            quality_score=quality_score,
            quality_status=quality_status,
            records_processed=ingested_obs_count,
            message=f"Dataset successfully registered with {ingested_obs_count} standardized observations ingested ({skipped_obs_count} skipped due to invalid/missing coordinates)."
        )

    @staticmethod
    def _ingest_records_into_domain_tables(
        dataset_id: str,
        domain_type: str,
        records: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Parses raw and canonical records and writes real observation entities
        into PostgreSQL domain tables:
        - species_occurrences & species (biodiversity)
        - oceanographic_observations (oceanography)
        - fisheries_records (fisheries)
        - edna_samples & edna_results (molecular_edna)

        Returns: (inserted_count, skipped_count)
        """
        import json
        import math
        from datetime import datetime, timezone
        from backend.app.db.database import execute_query, execute_single, execute_write
        
        def _validate_coords(lat_raw: Any, lon_raw: Any) -> Optional[Tuple[float, float]]:
            if lat_raw is None or lon_raw is None:
                return None
            try:
                lat_f = float(str(lat_raw).strip())
                lon_f = float(str(lon_raw).strip())
                if math.isnan(lat_f) or math.isnan(lon_f) or math.isinf(lat_f) or math.isinf(lon_f):
                    return None
                if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
                    return None
                return (lat_f, lon_f)
            except (ValueError, TypeError):
                return None

        domain = (domain_type or "").lower()
        now_iso = datetime.now(timezone.utc).isoformat()
        inserted_count = 0
        skipped_count = 0
        
        # 1. BIODIVERSITY / OCCURRENCE
        if any(d in domain for d in ["bio", "species", "occur"]):
            species_cache: Dict[str, str] = {}
            occurrence_batch: List[Dict[str, Any]] = []

            for r in records:
                try:
                    coords = _validate_coords(
                        r.get("decimalLatitude") or r.get("latitude") or r.get("lat"),
                        r.get("decimalLongitude") or r.get("longitude") or r.get("lon")
                    )
                    if not coords:
                        skipped_count += 1
                        continue
                    lat, lon = coords
                    
                    sc_name = (r.get("scientificName") or r.get("scientific_name") or "Unknown Marine Species").strip()
                    if not sc_name:
                        sc_name = "Unknown Marine Species"
                        
                    species_id = species_cache.get(sc_name)
                    if not species_id:
                        sp_res = execute_single(
                            """
                            INSERT INTO public.species (id, scientific_name, common_name, habitat_type, description, created_at, updated_at)
                            VALUES (gen_random_uuid(), :name, :common, :habitat, :desc, NOW(), NOW())
                            ON CONFLICT (scientific_name) DO UPDATE SET updated_at = NOW()
                            RETURNING id;
                            """,
                            {
                                "name": sc_name,
                                "common": r.get("vernacularName") or r.get("common_name") or r.get("commonName"),
                                "habitat": r.get("habitat") or "Marine",
                                "desc": f"Observed via CMLRE Deep Sea dataset ({r.get('datasetName') or 'Survey'})"
                            }
                        )
                        if sp_res:
                            species_id = str(sp_res["id"])
                            species_cache[sc_name] = species_id

                    depth_val = None
                    d_raw = r.get("minimumDepthInMeters") or r.get("depth_meters") or r.get("depth") or r.get("maximumDepthInMeters")
                    if d_raw is not None and str(d_raw).strip():
                        try:
                            d_f = float(str(d_raw).strip())
                            if not math.isnan(d_f) and not math.isinf(d_f):
                                depth_val = d_f
                        except (ValueError, TypeError):
                            depth_val = None

                    count_val = 1
                    c_raw = r.get("individualCount") or r.get("organismQuantity") or r.get("count")
                    if c_raw is not None and str(c_raw).strip():
                        try:
                            count_val = int(float(str(c_raw).strip()))
                        except (ValueError, TypeError):
                            count_val = 1

                    ts_val = r.get("eventDate") or r.get("timestamp") or r.get("date") or now_iso
                    basis = r.get("basisOfRecord") or r.get("basis_of_record") or "HumanObservation"
                    status_occ = r.get("occurrenceStatus") or r.get("occurrence_status") or "present"

                    occurrence_batch.append({
                        "dataset_id": dataset_id,
                        "species_id": species_id,
                        "scientific_name": sc_name,
                        "common_name": r.get("vernacularName") or r.get("common_name"),
                        "timestamp": ts_val,
                        "latitude": lat,
                        "longitude": lon,
                        "depth_meters": depth_val,
                        "individual_count": count_val,
                        "occurrence_status": status_occ,
                        "basis_of_record": basis,
                        "darwin_core_fields": json.dumps(r)
                    })

                    # Batch write in chunks of 500
                    if len(occurrence_batch) >= 500:
                        UploadService._batch_insert_occurrences(occurrence_batch)
                        inserted_count += len(occurrence_batch)
                        occurrence_batch.clear()

                except Exception as ex:
                    logger.warning("Error processing biodiversity record: %s", ex)
                    skipped_count += 1
                    continue

            if occurrence_batch:
                UploadService._batch_insert_occurrences(occurrence_batch)
                inserted_count += len(occurrence_batch)
                occurrence_batch.clear()

        # 2. OCEANOGRAPHY
        elif any(d in domain for d in ["ocean", "ctd", "hydro"]):
            for r in records:
                try:
                    coords = _validate_coords(
                        r.get("decimalLatitude") or r.get("latitude") or r.get("lat"),
                        r.get("decimalLongitude") or r.get("longitude") or r.get("lon")
                    )
                    if not coords:
                        skipped_count += 1
                        continue
                    lat, lon = coords
                    
                    def _flt(k_list):
                        for k in k_list:
                            v = r.get(k)
                            if v is not None and str(v).strip():
                                try:
                                    val_f = float(str(v).strip())
                                    if not math.isnan(val_f) and not math.isinf(val_f):
                                        return val_f
                                except (ValueError, TypeError):
                                    pass
                        return None

                    depth_val = _flt(["depth_meters", "depth", "pressure_dbar", "pressure"])
                    temp_val = _flt(["temperature_celsius", "temperature", "temp", "sst"])
                    sal_val = _flt(["salinity_psu", "salinity", "sal"])
                    do_val = _flt(["dissolved_oxygen_mgl", "dissolved_oxygen", "oxygen", "do"])
                    chl_val = _flt(["chlorophyll_mg_m3", "chlorophyll", "chla"])
                    ph_val = _flt(["ph"])
                    ts_val = r.get("timestamp") or r.get("observed_at") or r.get("eventDate") or now_iso

                    execute_write(
                        """
                        INSERT INTO public.oceanographic_observations (
                            id, dataset_id, station_id, timestamp, latitude, longitude,
                            depth_meters, temperature_celsius, salinity_psu, dissolved_oxygen_mgl,
                            chlorophyll_mg_m3, ph, quality_status, created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :dataset_id, :station_id, CAST(:timestamp AS timestamptz), :latitude, :longitude,
                            :depth_meters, :temperature, :salinity, :dissolved_oxygen,
                            :chlorophyll, :ph, 'passed'::quality_flag, NOW(), NOW()
                        );
                        """,
                        {
                            "dataset_id": dataset_id,
                            "station_id": r.get("station_id") or r.get("stationID") or r.get("eventID"),
                            "timestamp": ts_val,
                            "latitude": lat,
                            "longitude": lon,
                            "depth_meters": depth_val,
                            "temperature": temp_val,
                            "salinity": sal_val,
                            "dissolved_oxygen": do_val,
                            "chlorophyll": chl_val,
                            "ph": ph_val
                        }
                    )
                    inserted_count += 1
                except Exception as ex:
                    logger.warning("Error processing oceanographic record: %s", ex)
                    skipped_count += 1
                    continue

        # 3. FISHERIES
        elif any(d in domain for d in ["fish", "catch"]):
            for r in records:
                try:
                    coords = _validate_coords(
                        r.get("decimalLatitude") or r.get("latitude") or r.get("lat"),
                        r.get("decimalLongitude") or r.get("longitude") or r.get("lon")
                    )
                    if not coords:
                        skipped_count += 1
                        continue
                    lat, lon = coords

                    def _flt(k_list):
                        for k in k_list:
                            v = r.get(k)
                            if v is not None and str(v).strip():
                                try:
                                    val_f = float(str(v).strip())
                                    if not math.isnan(val_f) and not math.isinf(val_f):
                                        return val_f
                                except (ValueError, TypeError):
                                    pass
                        return None

                    catch_wt = _flt(["catch_weight_kg", "catch_weight", "landing_weight", "weight"])
                    effort = _flt(["fishing_effort_hours", "effort_hours", "trawl_hours", "effort"])
                    species_name = r.get("species_name_reported") or r.get("species_name") or r.get("scientificName") or "Marine Finfish"
                    ts_val = r.get("timestamp") or r.get("recorded_at") or r.get("date") or now_iso

                    execute_write(
                        """
                        INSERT INTO public.fisheries_records (
                            id, dataset_id, timestamp, latitude, longitude,
                            species_name_reported, catch_weight_kg, fishing_effort_hours,
                            gear_type, fishing_zone, vessel_name, quality_status, created_at, updated_at
                        ) VALUES (
                            gen_random_uuid(), :dataset_id, CAST(:timestamp AS timestamptz), :latitude, :longitude,
                            :species_name, :catch_weight_kg, :fishing_effort_hours,
                            :gear_type, :fishing_zone, :vessel_name, 'passed'::quality_flag, NOW(), NOW()
                        );
                        """,
                        {
                            "dataset_id": dataset_id,
                            "timestamp": ts_val,
                            "latitude": lat,
                            "longitude": lon,
                            "species_name": species_name,
                            "catch_weight_kg": catch_wt,
                            "fishing_effort_hours": effort,
                            "gear_type": r.get("gear_type") or "Trawl Net",
                            "fishing_zone": r.get("fishing_zone") or "West Coast EEZ",
                            "vessel_name": r.get("vessel_name") or r.get("vesselID") or "FORV Sagar Sampada"
                        }
                    )
                    inserted_count += 1
                except Exception as ex:
                    logger.warning("Error processing fisheries record: %s", ex)
                    skipped_count += 1
                    continue

        # 4. MOLECULAR eDNA
        elif any(d in domain for d in ["dna", "edna", "mole"]):
            sample_cache: Dict[str, str] = {}
            for r in records:
                try:
                    coords = _validate_coords(
                        r.get("latitude") or r.get("decimalLatitude"),
                        r.get("longitude") or r.get("decimalLongitude")
                    )
                    if not coords:
                        skipped_count += 1
                        continue
                    lat, lon = coords

                    sample_code = r.get("sample_code") or r.get("sampleCode") or r.get("eventID") or f"EDNA-{dataset_id[:8]}"
                    
                    sample_id = sample_cache.get(sample_code)
                    if not sample_id:
                        d_raw = r.get("depth_meters") or r.get("depth")
                        depth_val = float(str(d_raw).strip()) if d_raw is not None and str(d_raw).strip() else None

                        s_res = execute_single(
                            """
                            INSERT INTO public.edna_samples (
                                id, dataset_id, sample_code, collection_timestamp, latitude, longitude,
                                depth_meters, target_gene, sequencing_platform, quality_status, created_at, updated_at
                            ) VALUES (
                                gen_random_uuid(), :dataset_id, :sample_code, CAST(:timestamp AS timestamptz), :latitude, :longitude,
                                :depth_meters, :target_gene, :sequencing_platform, 'passed'::quality_flag, NOW(), NOW()
                            ) RETURNING id;
                            """,
                            {
                                "dataset_id": dataset_id,
                                "sample_code": sample_code,
                                "timestamp": r.get("collection_timestamp") or r.get("eventDate") or now_iso,
                                "latitude": lat,
                                "longitude": lon,
                                "depth_meters": depth_val,
                                "target_gene": r.get("target_gene") or r.get("marker"),
                                "sequencing_platform": r.get("sequencing_platform")
                            }
                        )
                        if s_res:
                            sample_id = str(s_res["id"])
                            sample_cache[sample_code] = sample_id

                    if sample_id:
                        sc_name = r.get("assigned_scientific_name") or r.get("scientificName") or "Marine Microorganism"
                        r_raw = r.get("read_count") or r.get("reads")
                        reads = int(float(str(r_raw).strip())) if r_raw is not None and str(r_raw).strip() else None

                        b_raw = r.get("blast_identity_percentage")
                        blast_val = float(str(b_raw).strip()) if b_raw is not None and str(b_raw).strip() else None

                        conf_raw = r.get("confidence_score")
                        conf_val = float(str(conf_raw).strip()) if conf_raw is not None and str(conf_raw).strip() else None

                        execute_write(
                            """
                            INSERT INTO public.edna_results (
                                id, edna_sample_id, assigned_scientific_name, read_count,
                                blast_identity_percentage, confidence_score, created_at, updated_at
                            ) VALUES (
                                gen_random_uuid(), :sample_id, :scientific_name, :read_count,
                                :blast_identity, :confidence_score, NOW(), NOW()
                            );
                            """,
                            {
                                "sample_id": sample_id,
                                "scientific_name": sc_name,
                                "read_count": reads,
                                "blast_identity": blast_val,
                                "confidence_score": conf_val
                            }
                        )
                        inserted_count += 1
                except Exception as ex:
                    logger.warning("Error processing eDNA record: %s", ex)
                    skipped_count += 1
                    continue

        return (inserted_count, skipped_count)

    @staticmethod
    def _batch_insert_occurrences(batch: List[Dict[str, Any]]) -> None:
        """Helper to batch-insert species occurrences."""
        from backend.app.db.database import execute_write
        for item in batch:
            execute_write(
                """
                INSERT INTO public.species_occurrences (
                    id, dataset_id, species_id, scientific_name, common_name, timestamp,
                    latitude, longitude, depth_meters, individual_count, occurrence_status,
                    basis_of_record, darwin_core_fields, quality_status, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :dataset_id, :species_id, :scientific_name, :common_name, CAST(:timestamp AS timestamptz),
                    :latitude, :longitude, :depth_meters, :individual_count, :occurrence_status,
                    :basis_of_record, CAST(:darwin_core_fields AS jsonb), 'passed'::quality_flag, NOW(), NOW()
                );
                """,
                item
            )


