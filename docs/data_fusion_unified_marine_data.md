# Phase 5 — Data Fusion & Unified Marine Data Layer

## 1. Executive Summary

Phase 5 implements the **Unified Marine Data & Cross-Domain Fusion Layer** for the CMLRE Marine Intelligence Platform. It provides a common query representation and cross-domain linking engine across heterogeneous marine domains:
- **Oceanography** (`oceanographic_observations`: CTD physical/chemical measurements)
- **Fisheries** (`fisheries_records`: catch logs, fishing gear, zones, effort)
- **Biodiversity & Taxonomy** (`species_occurrences`: Darwin Core occurrence records)
- **Molecular / eDNA** (`edna_samples` / `edna_results`: environmental DNA detections)

```text
┌─────────────────────────┐  ┌───────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────┐
│ Oceanographic Obs (CTD) │  │   Fisheries Records   │  │   Species Occurrences   │  │   eDNA Detections     │
└────────────┬────────────┘  └───────────┬───────────┘  └────────────┬────────────┘  └───────────┬───────────┘
             │                           │                           │                           │
             └───────────────────────────┼───────────────────────────┴───────────────────────────┘
                                         ▼
                 ┌────────────────────────────────────────────────────────┐
                 │       Phase 5: Common Marine Observation Model         │
                 │                 (MarineObservation)                    │
                 ├────────────────────────────────────────────────────────┤
                 │ • Spatial Alignment: Geodesic Haversine Distance (km)  │
                 │ • Temporal Alignment: Windowing (hours) & UTC bounds   │
                 │ • Depth Alignment: Water column tolerance (meters)     │
                 │ • Multi-criteria Unified Query & Bounding-Box filtering│
                 │ • Cross-Domain Co-occurrence Association Engine        │
                 │ • Strict Provenance & Source Table Lineage Retention   │
                 └────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                         Phase 6 Scientific Analysis /
                         FastAPI Backend / React Dashboard
```

---

## 2. Common Marine Observation Model

The common representation (`MarineObservation`) standardizes heterogeneous observations into a unified schema for multi-criteria querying while strictly preserving original table lineage and database structures:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `TEXT` / `UUID` | Unique observation identifier (e.g. `{rec_id}_{variable}`) |
| `dataset_id` | `UUID` | Foreign key referencing `public.datasets(id)` |
| `domain` | `TEXT` | `oceanography`, `fisheries`, `biodiversity`, or `edna` |
| `observation_id` | `UUID` / `TEXT` | Primary key in the source domain table |
| `station_id` | `UUID` / `TEXT` | Sampling station reference (where available) |
| `sample_id` | `UUID` / `TEXT` | Sample collection event reference |
| `species_id` | `UUID` / `TEXT` | Master species identifier (where applicable) |
| `species_name` | `TEXT` | Scientific name or vernacular name |
| `latitude` | `FLOAT` | Decimal degrees [-90.0, 90.0] |
| `longitude` | `FLOAT` | Decimal degrees [-180.0, 180.0] |
| `observation_time`| `TEXT` (ISO-8601) | Normalized ISO timestamp |
| `depth` | `FLOAT` | Canonical water depth in meters ($z \ge 0$) |
| `variable` | `TEXT` | Measured parameter (e.g. `temperature`, `salinity`, `catch_weight`, `individual_count`) |
| `value` | `FLOAT` | Numerical measurement value |
| `unit` | `TEXT` | Standard SI / marine unit (e.g. `°C`, `PSU`, `mg/L`, `kg`, `count`) |
| `source_table` | `TEXT` | Originating database table name |
| `quality_status` | `TEXT` | QC validation flag (`passed`, `flagged`, `failed`) |

---

## 3. Spatial, Temporal, and Depth Alignment

### Spatial Alignment
- **Mathematical Rigor**: Geodesic great-circle distance is computed via the spherical **Haversine formula** using the IUGG standard Earth radius ($R = 6371.0088\text{ km}$). It strictly rejects simplistic degree subtraction ($\Delta\text{deg} \times 111$) which distorts distances away from the equator.
- **Bounding Box Queries**: Supports envelope filtering `[west_lon, south_lat, east_lon, north_lat]` with antimeridian crossing support.
- **Proximity Queries**: Point-radius filtering `(center_lat, center_lon, radius_km)`.

### Temporal Alignment
- **Timezone Awareness**: Timezone-aware timestamps (`...Z`, `+05:30`) are converted to standard UTC for distance calculations.
- **Naive Timestamps**: Naive/local timestamps are preserved without fabricating timezone offsets (preserving Phase 4 integrity).
- **Missing Timestamps**: Missing timestamps are never hallucinated.

### Depth Alignment
- **Canonical Unit**: All depths are strictly evaluated in meters (`depth_meters`).
- **Vertical Tolerance**: Vertical water column matching `|depth_1 - depth_2| <= tolerance_meters`.
- **Stratification Semantics**: Missing depth on unstratified records (e.g. surface trawls) is handled explicitly and transparently.

---

## 4. Cross-Domain Association & Scientific Trust

### Association Method
Given an anchor observation (e.g. a fish occurrence or biodiversity detection), the cross-domain engine queries candidate observations across other domains that satisfy joint 3D spatial, temporal, and depth windows:
$$\text{Distance}(\text{anchor}, \text{candidate}) \le \text{radius\_km}$$
$$\Delta \text{Time}(\text{anchor}, \text{candidate}) \le \text{window\_hours}$$
$$|\text{Depth}_{\text{anchor}} - \text{Depth}_{\text{candidate}}| \le \text{tolerance\_meters}$$

### Scientific Trust & Ethics Disclaimer
> **CRITICAL SCIENTIFIC PRINCIPLE**:
> Spatial and temporal co-occurrence **DOES NOT imply biological causation**.
> Fused outputs are explicitly designated as **"associated observations / environmental context"** and never as "proof that oceanographic variable X caused species presence Y".

---

## 5. Verified Database Schema (Supabase PostgreSQL)

The live Supabase database tables and their exact columns verified in Phase 5:

### `oceanographic_observations`
- `id`, `dataset_id`, `station_id`, `sample_id`, `latitude`, `longitude`, `location`, `timestamp`, `depth_meters`, `temperature_celsius`, `salinity_psu`, `dissolved_oxygen_mgl`, `chlorophyll_mg_m3`, `ph`, `pressure_dbar`, `turbidity_ntu`, `quality_score`, `quality_status`, `created_at`, `updated_at`

### `fisheries_records`
- `id`, `dataset_id`, `sample_id`, `species_id`, `latitude`, `longitude`, `location`, `timestamp`, `depth_meters`, `catch_weight_kg`, `gear_type`, `fishing_zone`, `vessel_name`, `provenance_metadata`, `quality_score`, `quality_status`, `created_at`, `updated_at`

### `species_occurrences`
- `id`, `dataset_id`, `sample_id`, `species_id`, `scientific_name`, `common_name`, `latitude`, `longitude`, `location`, `timestamp`, `depth_meters`, `individual_count`, `basis_of_record`, `occurrence_status`, `quality_status`, `created_at`, `updated_at`

### `edna_samples`
- `id`, `dataset_id`, `sample_id`, `station_id`, `latitude`, `longitude`, `location`, `depth_meters`, `target_gene`, `quality_status`, `created_at`, `updated_at`

### Optional Common SQL View (`unified_marine_observations`)
```sql
CREATE OR REPLACE VIEW public.unified_marine_observations AS
-- Oceanography Temperature
SELECT 
    id || '_temp' AS id, dataset_id, 'oceanography' AS domain, id AS observation_id,
    station_id, sample_id, NULL::uuid AS species_id, NULL::text AS species_name,
    latitude, longitude, timestamp AS observation_time, depth_meters AS depth,
    'temperature' AS variable, temperature_celsius AS value, '°C' AS unit,
    'oceanographic_observations' AS source_table, quality_status
FROM public.oceanographic_observations WHERE temperature_celsius IS NOT NULL
UNION ALL
-- Oceanography Salinity
SELECT 
    id || '_sal' AS id, dataset_id, 'oceanography' AS domain, id AS observation_id,
    station_id, sample_id, NULL::uuid AS species_id, NULL::text AS species_name,
    latitude, longitude, timestamp AS observation_time, depth_meters AS depth,
    'salinity' AS variable, salinity_psu AS value, 'PSU' AS unit,
    'oceanographic_observations' AS source_table, quality_status
FROM public.oceanographic_observations WHERE salinity_psu IS NOT NULL
UNION ALL
-- Fisheries Catch
SELECT 
    id::text AS id, dataset_id, 'fisheries' AS domain, id AS observation_id,
    NULL::uuid AS station_id, sample_id, species_id, NULL::text AS species_name,
    latitude, longitude, timestamp AS observation_time, depth_meters AS depth,
    'catch_weight' AS variable, catch_weight_kg AS value, 'kg' AS unit,
    'fisheries_records' AS source_table, quality_status
FROM public.fisheries_records WHERE catch_weight_kg IS NOT NULL
UNION ALL
-- Species Occurrences
SELECT 
    id::text AS id, dataset_id, 'biodiversity' AS domain, id AS observation_id,
    NULL::uuid AS station_id, sample_id, species_id, scientific_name AS species_name,
    latitude, longitude, timestamp AS observation_time, depth_meters AS depth,
    'individual_count' AS variable, COALESCE(individual_count, 1)::double precision AS value, 'count' AS unit,
    'species_occurrences' AS source_table, quality_status
FROM public.species_occurrences;
```

---

## 6. Phase 5 → Phase 6 & FastAPI Interface

Phase 6 Scientific Analysis and the FastAPI backend consume Phase 5 through the clean service interface in `data_pipeline.fusion`:

```python
from data_pipeline.fusion import (
    MarineObservation,
    UnifiedQueryParams,
    query_unified_observations,
    get_domain_observations,
    get_unified_summary,
    get_cross_domain_context,
)

# 1. Multi-criteria unified query across all domains
params = UnifiedQueryParams(
    latitude=9.93,
    longitude=76.27,
    radius_km=50.0,
    depth_min=0.0,
    depth_max=100.0,
    date_from="2026-03-01T00:00:00Z",
    date_to="2026-03-31T23:59:59Z"
)
observations = query_unified_observations(params)

# 2. Cross-domain environmental context for a species observation
context = get_cross_domain_context(
    anchor=observations[0],
    spatial_radius_km=25.0,
    temporal_window_hours=48.0,
    depth_tolerance_m=20.0
)

# 3. Research Dashboard summary statistics
summary = get_unified_summary()
```
