"""
Parameterized SQL queries for Supabase PostgreSQL + PostGIS tables using SQLAlchemy syntax (:param).
"""

# ==========================================
# 1. AUTH & USERS QUERIES
# ==========================================

GET_PROFILE_BY_ID = """
SELECT id, full_name, email, role, institution, department, designation, created_at, updated_at
FROM public.profiles
WHERE id = :user_id;
"""

GET_ALL_PROFILES = """
SELECT id, full_name, email, role, institution, department, designation, created_at, updated_at
FROM public.profiles
ORDER BY created_at DESC
LIMIT :limit OFFSET :offset;
"""

COUNT_ALL_PROFILES = """
SELECT COUNT(*) as total FROM public.profiles;
"""

UPDATE_USER_ROLE = """
UPDATE public.profiles
SET role = :role, updated_at = NOW()
WHERE id = :user_id
RETURNING id, full_name, email, role, institution, department, designation, updated_at;
"""


# ==========================================
# 2. DATASETS QUERIES
# ==========================================

GET_DATASETS_BASE = """
SELECT 
    d.id, d.project_id, d.data_source_id, d.name, d.domain_type,
    d.storage_file_path, d.file_type, d.file_size_bytes, d.row_count,
    d.uploaded_by, d.status, d.quality_status, d.quality_score,
    d.validation_notes, d.provenance_metadata, d.created_at, d.updated_at,
    p.name as project_name,
    s.name as source_name
FROM public.datasets d
LEFT JOIN public.projects p ON d.project_id = p.id
LEFT JOIN public.data_sources s ON d.data_source_id = s.id
"""

GET_DATASET_BY_ID = GET_DATASETS_BASE + """
WHERE d.id = :dataset_id;
"""

INSERT_DATASET = """
INSERT INTO public.datasets (
    id, project_id, data_source_id, name, domain_type,
    storage_file_path, file_type, file_size_bytes, row_count,
    uploaded_by, status, quality_status, quality_score,
    validation_notes, provenance_metadata
) VALUES (
    :id, :project_id, :data_source_id, :name, :domain_type,
    :storage_file_path, :file_type, :file_size_bytes, :row_count,
    :uploaded_by, :status, :quality_status, :quality_score,
    :validation_notes, :provenance_metadata
)
RETURNING *;
"""

UPDATE_DATASET_METADATA = """
UPDATE public.datasets
SET 
    name = COALESCE(:name, name),
    domain_type = COALESCE(:domain_type, domain_type),
    quality_status = COALESCE(:quality_status, quality_status),
    quality_score = COALESCE(:quality_score, quality_score),
    validation_notes = COALESCE(:validation_notes, validation_notes),
    provenance_metadata = COALESCE(:provenance_metadata, provenance_metadata),
    status = COALESCE(:status, status),
    updated_at = NOW()
WHERE id = :dataset_id
RETURNING *;
"""

DELETE_DATASET = """
DELETE FROM public.datasets
WHERE id = :dataset_id
RETURNING id;
"""


# ==========================================
# 3. OCEANOGRAPHY QUERIES
# ==========================================

GET_OCEAN_OBSERVATIONS = """
SELECT 
    o.id, o.dataset_id, o.station_id, o.sample_id,
    o.latitude, o.longitude, o.depth_meters as depth, o.timestamp as observed_at,
    o.temperature_celsius as temperature, o.salinity_psu as salinity, 
    o.dissolved_oxygen_mgl as dissolved_oxygen, o.chlorophyll_mg_m3 as chlorophyll,
    o.ph, o.pressure_dbar as pressure, o.turbidity_ntu as turbidity, o.conductivity_sm as conductivity,
    o.quality_status::text as quality_flag, o.extra_parameters as metadata, o.created_at
FROM public.oceanographic_observations o
"""

GET_OCEAN_OBSERVATION_BY_ID = GET_OCEAN_OBSERVATIONS + """
WHERE o.id = :observation_id;
"""

GET_OCEAN_SUMMARY = """
SELECT 
    COUNT(*) as total_observations,
    MIN(temperature_celsius) as min_temperature,
    MAX(temperature_celsius) as max_temperature,
    AVG(temperature_celsius) as avg_temperature,
    MIN(salinity_psu) as min_salinity,
    MAX(salinity_psu) as max_salinity,
    AVG(salinity_psu) as avg_salinity,
    MIN(dissolved_oxygen_mgl) as min_dissolved_oxygen,
    MAX(dissolved_oxygen_mgl) as max_dissolved_oxygen,
    AVG(dissolved_oxygen_mgl) as avg_dissolved_oxygen,
    MIN(depth_meters) as min_depth,
    MAX(depth_meters) as max_depth
FROM public.oceanographic_observations
WHERE (:date_from IS NULL OR timestamp >= CAST(:date_from AS timestamptz))
  AND (:date_to IS NULL OR timestamp <= CAST(:date_to AS timestamptz));
"""

GET_OCEAN_TRENDS = """
SELECT 
    DATE_TRUNC(:interval, timestamp) as time_bucket,
    COUNT(*) as observation_count,
    AVG(temperature_celsius) as avg_temperature,
    AVG(salinity_psu) as avg_salinity,
    AVG(dissolved_oxygen_mgl) as avg_dissolved_oxygen,
    AVG(chlorophyll_mg_m3) as avg_chlorophyll
FROM public.oceanographic_observations
WHERE (:date_from IS NULL OR timestamp >= CAST(:date_from AS timestamptz))
  AND (:date_to IS NULL OR timestamp <= CAST(:date_to AS timestamptz))
GROUP BY time_bucket
ORDER BY time_bucket ASC;
"""


# ==========================================
# 4. FISHERIES QUERIES
# ==========================================

GET_FISHERIES_OBSERVATIONS = """
SELECT 
    f.id, f.dataset_id, f.species_id, f.latitude, f.longitude,
    f.timestamp as recorded_at, f.catch_weight_kg, f.fishing_effort_hours as effort_hours, f.gear_type,
    f.fishing_zone, f.vessel_name, f.extra_parameters as metadata, f.created_at,
    s.scientific_name, s.common_name
FROM public.fisheries_records f
LEFT JOIN public.species s ON f.species_id = s.id
"""

GET_FISHERIES_OBSERVATION_BY_ID = GET_FISHERIES_OBSERVATIONS + """
WHERE f.id = :observation_id;
"""

GET_FISHERIES_SUMMARY = """
SELECT 
    COUNT(*) as total_records,
    SUM(catch_weight_kg) as total_catch_kg,
    AVG(catch_weight_kg) as avg_catch_kg,
    SUM(fishing_effort_hours) as total_effort_hours,
    COUNT(DISTINCT species_id) as distinct_species_count,
    COUNT(DISTINCT fishing_zone) as distinct_zones_count
FROM public.fisheries_records
WHERE (:date_from IS NULL OR timestamp >= CAST(:date_from AS timestamptz))
  AND (:date_to IS NULL OR timestamp <= CAST(:date_to AS timestamptz));
"""

GET_FISHERIES_TRENDS = """
SELECT 
    DATE_TRUNC(:interval, timestamp) as time_bucket,
    COUNT(*) as record_count,
    SUM(catch_weight_kg) as total_catch_kg,
    AVG(catch_weight_kg) as avg_catch_kg,
    SUM(fishing_effort_hours) as total_effort_hours
FROM public.fisheries_records
WHERE (:date_from IS NULL OR timestamp >= CAST(:date_from AS timestamptz))
  AND (:date_to IS NULL OR timestamp <= CAST(:date_to AS timestamptz))
GROUP BY time_bucket
ORDER BY time_bucket ASC;
"""


# ==========================================
# 5. SPECIES & TAXONOMY QUERIES
# ==========================================

SEARCH_SPECIES = """
SELECT 
    s.id, s.taxonomy_id, s.scientific_name, s.common_name,
    s.iucn_conservation_status as iucn_red_list_status, s.commercial_importance,
    s.habitat_type, s.created_at,
    t.kingdom, t.phylum, t.class, t.order_name as "order", t.family, t.genus
FROM public.species s
LEFT JOIN public.taxonomy t ON s.taxonomy_id = t.id
WHERE (:search IS NULL OR s.scientific_name ILIKE :search_like OR s.common_name ILIKE :search_like)
ORDER BY s.scientific_name ASC
LIMIT :limit OFFSET :offset;
"""

COUNT_SEARCH_SPECIES = """
SELECT COUNT(*) as total
FROM public.species s
WHERE (:search IS NULL OR s.scientific_name ILIKE :search_like OR s.common_name ILIKE :search_like);
"""

GET_SPECIES_BY_ID = """
SELECT 
    s.id, s.taxonomy_id, s.scientific_name, s.common_name,
    s.iucn_conservation_status as iucn_red_list_status, s.commercial_importance,
    s.habitat_type, s.metadata, s.created_at,
    t.kingdom, t.phylum, t.class, t.order_name as "order", t.family, t.genus
FROM public.species s
LEFT JOIN public.taxonomy t ON s.taxonomy_id = t.id
WHERE s.id = :species_id;
"""

GET_SPECIES_OCCURRENCES = """
SELECT 
    o.id, o.dataset_id, o.species_id, o.latitude, o.longitude,
    o.depth_meters as depth, o.timestamp as observed_at, o.individual_count, o.basis_of_record,
    o.darwin_core_fields->>'recordedBy' as recorded_by, o.darwin_core_fields as metadata, o.created_at,
    s.scientific_name, s.common_name
FROM public.species_occurrences o
JOIN public.species s ON o.species_id = s.id
WHERE o.species_id = :species_id
ORDER BY o.timestamp DESC
LIMIT :limit OFFSET :offset;
"""

COUNT_SPECIES_OCCURRENCES = """
SELECT COUNT(*) as total
FROM public.species_occurrences
WHERE species_id = :species_id;
"""

GET_SPECIES_DISTRIBUTION = """
SELECT 
    species_id,
    COUNT(*) as occurrence_count,
    MIN(latitude) as min_latitude,
    MAX(latitude) as max_latitude,
    MIN(longitude) as min_longitude,
    MAX(longitude) as max_longitude,
    MIN(depth_meters) as min_depth,
    MAX(depth_meters) as max_depth
FROM public.species_occurrences
WHERE species_id = :species_id
GROUP BY species_id;
"""


# ==========================================
# 6. UNIFIED CROSS-DOMAIN MARINE QUERIES
# ==========================================

GET_UNIFIED_MARINE_OBSERVATIONS = """
(
    SELECT 
        'oceanography' as domain,
        o.id::text as id,
        o.dataset_id::text as dataset_id,
        o.latitude,
        o.longitude,
        o.depth_meters as depth,
        o.timestamp as time,
        NULL::text as species_id,
        NULL::text as species_name,
        jsonb_build_object(
            'temperature', o.temperature_celsius,
            'salinity', o.salinity_psu,
            'dissolved_oxygen', o.dissolved_oxygen_mgl,
            'chlorophyll', o.chlorophyll_mg_m3
        ) as measurements
    FROM public.oceanographic_observations o
    WHERE (:date_from IS NULL OR o.timestamp >= CAST(:date_from AS timestamptz))
      AND (:date_to IS NULL OR o.timestamp <= CAST(:date_to AS timestamptz))
      AND (:dataset_id IS NULL OR o.dataset_id = :dataset_id)
      AND (:depth_min IS NULL OR o.depth_meters >= :depth_min)
      AND (:depth_max IS NULL OR o.depth_meters <= :depth_max)
)
UNION ALL
(
    SELECT 
        'fisheries' as domain,
        f.id::text as id,
        f.dataset_id::text as dataset_id,
        f.latitude,
        f.longitude,
        f.depth_meters as depth,
        f.timestamp as time,
        f.species_id::text as species_id,
        COALESCE(s.common_name, f.species_name_reported) as species_name,
        jsonb_build_object(
            'catch_weight_kg', f.catch_weight_kg,
            'effort_hours', f.fishing_effort_hours,
            'gear_type', f.gear_type,
            'fishing_zone', f.fishing_zone
        ) as measurements
    FROM public.fisheries_records f
    LEFT JOIN public.species s ON f.species_id = s.id
    WHERE (:date_from IS NULL OR f.timestamp >= CAST(:date_from AS timestamptz))
      AND (:date_to IS NULL OR f.timestamp <= CAST(:date_to AS timestamptz))
      AND (:dataset_id IS NULL OR f.dataset_id = :dataset_id)
      AND (:species_id IS NULL OR f.species_id = :species_id)
)
UNION ALL
(
    SELECT 
        'biodiversity' as domain,
        occ.id::text as id,
        occ.dataset_id::text as dataset_id,
        occ.latitude,
        occ.longitude,
        occ.depth_meters as depth,
        occ.timestamp as time,
        occ.species_id::text as species_id,
        COALESCE(sp.scientific_name, occ.scientific_name) as species_name,
        jsonb_build_object(
            'individual_count', occ.individual_count,
            'basis_of_record', occ.basis_of_record,
            'scientific_name', occ.scientific_name
        ) as measurements
    FROM public.species_occurrences occ
    LEFT JOIN public.species sp ON occ.species_id = sp.id
    WHERE (:date_from IS NULL OR occ.timestamp >= CAST(:date_from AS timestamptz))
      AND (:date_to IS NULL OR occ.timestamp <= CAST(:date_to AS timestamptz))
      AND (:dataset_id IS NULL OR occ.dataset_id = :dataset_id)
      AND (:species_id IS NULL OR occ.species_id = :species_id)
      AND (:depth_min IS NULL OR occ.depth_meters >= :depth_min)
      AND (:depth_max IS NULL OR occ.depth_meters <= :depth_max)
)
ORDER BY time DESC NULLS LAST, id ASC
LIMIT :limit OFFSET :offset;
"""

COUNT_UNIFIED_MARINE_OBSERVATIONS = """
SELECT (
    (
        SELECT COUNT(*)
        FROM public.oceanographic_observations o
        WHERE (:date_from IS NULL OR o.timestamp >= CAST(:date_from AS timestamptz))
          AND (:date_to IS NULL OR o.timestamp <= CAST(:date_to AS timestamptz))
          AND (:dataset_id IS NULL OR o.dataset_id = :dataset_id)
          AND (:depth_min IS NULL OR o.depth_meters >= :depth_min)
          AND (:depth_max IS NULL OR o.depth_meters <= :depth_max)
    ) +
    (
        SELECT COUNT(*)
        FROM public.fisheries_records f
        WHERE (:date_from IS NULL OR f.timestamp >= CAST(:date_from AS timestamptz))
          AND (:date_to IS NULL OR f.timestamp <= CAST(:date_to AS timestamptz))
          AND (:dataset_id IS NULL OR f.dataset_id = :dataset_id)
          AND (:species_id IS NULL OR f.species_id = :species_id)
    ) +
    (
        SELECT COUNT(*)
        FROM public.species_occurrences occ
        WHERE (:date_from IS NULL OR occ.timestamp >= CAST(:date_from AS timestamptz))
          AND (:date_to IS NULL OR occ.timestamp <= CAST(:date_to AS timestamptz))
          AND (:dataset_id IS NULL OR occ.dataset_id = :dataset_id)
          AND (:species_id IS NULL OR occ.species_id = :species_id)
          AND (:depth_min IS NULL OR occ.depth_meters >= :depth_min)
          AND (:depth_max IS NULL OR occ.depth_meters <= :depth_max)
    )
) as total;
"""

GET_MARINE_SUMMARY = """
SELECT 
    (SELECT COUNT(*) FROM public.oceanographic_observations) as oceanography_count,
    (SELECT COUNT(*) FROM public.fisheries_records) as fisheries_count,
    (SELECT COUNT(*) FROM public.species_occurrences) as biodiversity_count,
    (SELECT COUNT(*) FROM public.edna_results) as edna_count,
    (SELECT COUNT(*) FROM public.datasets) as total_datasets,
    (SELECT COUNT(*) FROM public.species) as total_species;
"""

