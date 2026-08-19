# CMLRE Marine Data Platform — Database Schema Reference

**Platform**: Supabase PostgreSQL 17.6 with PostGIS  
**Target Database**: `db.wmejplohqpdupugeluxx.supabase.co`  
**Status**: Applied & Verified  

---

## 1. Architecture Overview & Core Decisions

The database implements the authoritative architecture defined in `docs/context.md`:
* **Primary Structured Store**: Supabase PostgreSQL + PostGIS (no MongoDB / no secondary SQL stores).
* **Spatial Processing**: Native PostGIS `geography(Point, 4326)` with automated synchronization triggers and GIST spatial indexing.
* **Authentication**: Native Supabase Auth (`auth.users`) integrated with `public.profiles` via foreign keys and auto-creation triggers. No custom password tables.
* **File Storage Strategy**: Large binary and raw files (NetCDF, CTD raw, FASTA, otolith high-res images, PDF reports) are referenced by storage paths in Supabase Storage buckets.
* **Row-Level Security (RLS)**: Enforced across all 18 application tables with role-based policies.
* **Traceability & Quality**: Standardized QARTOD quality control flags, quality scores, and immutable `audit_logs`.

---

## 2. Table Summary & Logical Domains

| Domain | Table Name | Purpose | Key Relationships & Spatial Types |
| :--- | :--- | :--- | :--- |
| **1. Identity / Access** | `profiles` | User profiles, roles, and institutional affiliations | `auth.users(id)` (1:1 cascade) |
| **2. Projects & Sources** | `projects` | Research workspaces and collaborative projects | `profiles(id)` (lead researcher / creator) |
| | `data_sources` | Provenance registry for external agencies & cruises | INCOIS, CMFRI, CMLRE, OBIS, GBIF |
| | `datasets` | Dataset catalog, metadata, QC scores, storage paths | `projects(id)`, `data_sources(id)`, `profiles(id)` |
| **3. Spatial Entities** | `stations` | Fixed/recurring marine sampling stations | `projects(id)`, PostGIS `location` GIST index |
| | `samples` | Specific sample collection events & casts | `datasets(id)`, `stations(id)`, `projects(id)`, `location` |
| **4. Oceanography** | `oceanographic_observations` | CTD, sensors, water column physical/chemical records | `datasets(id)`, `stations(id)`, `samples(id)`, `location` |
| **5. Species & Taxonomy**| `taxonomy` | Hierarchical taxonomy (WoRMS AphiaID, NCBI TaxID) | Self-referencing ranks, authority, synonyms |
| | `species` | Master marine species catalog with conservation status | `taxonomy(id)` |
| | `species_occurrences` | Darwin Core biodiversity occurrence records | `datasets(id)`, `samples(id)`, `species(id)`, `location` |
| **6. Fisheries** | `fisheries_records` | Catch logs, gear types, vessel data, fishing effort | `datasets(id)`, `samples(id)`, `species(id)`, `location` |
| **7. eDNA / Molecular** | `edna_samples` | Environmental DNA sampling metadata & primer info | `datasets(id)`, `samples(id)`, `stations(id)`, `location` |
| | `edna_results` | ASV/OTU reads, BLAST alignments, abundance metrics | `edna_samples(id)`, `species(id)`, `taxonomy(id)` |
| **8. Otolith / Vision** | `otolith_samples` | Otolith specimen data, morphometrics, image paths | `datasets(id)`, `samples(id)`, `location` |
| | `otolith_results` | ML predicted species, age estimates, validation status | `otolith_samples(id)`, `species(id)`, `ml_models(id)` |
| **9. AI / ML Registry** | `ml_models` | Model versioning, architecture, metrics, ONNX paths | Task types: CNN, XGBoost, ONNX classifiers |
| | `predictions` | ML model inference logs, explainability metadata | `ml_models(id)`, `datasets(id)`, `samples(id)`, `location` |
| **10. Scientific Analysis**| `analysis_jobs` | Spatial, temporal, cross-domain analytical jobs | `projects(id)`, `profiles(id)` |
| | `analysis_results` | Summary statistics, correlation matrices, GeoJSON layers| `analysis_jobs(id)`, `projects(id)` |
| **11. Alerts** | `alerts` | Anomaly, hypoxia, biodiversity, and ecosystem alerts | `projects(id)`, `analysis_jobs(id)`, `predictions(id)`, `location` |
| **12. Auditability** | `audit_logs` | Immutable audit trail for system operations | `profiles(id)`, entity tracking |

---

## 3. PostGIS Spatial Capabilities & Indexes

Spatial columns use `extensions.geography(Point, 4326)` for WGS84 geodesic calculations.

### Automated Spatial Sync Trigger
Every spatial table includes a `trg_sync_location` trigger that executes `public.sync_location_point()`. When `latitude` and `longitude` are provided, the PostGIS `location` point is computed automatically:
```sql
NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
```

### Spatial GIST Indexes
* `idx_stations_location` on `stations(location)`
* `idx_samples_location` on `samples(location)`
* `idx_ocean_obs_location` on `oceanographic_observations(location)`
* `idx_fisheries_location` on `fisheries_records(location)`
* `idx_occurrences_location` on `species_occurrences(location)`
* `idx_edna_samples_location` on `edna_samples(location)`
* `idx_otolith_samples_location` on `otolith_samples(location)`
* `idx_predictions_location` on `predictions(location)`
* `idx_alerts_location` on `alerts(location)`

---

## 4. Row-Level Security (RLS) Configuration

All 18 tables in `public` have Row Level Security enabled:
* **Profiles**: Users can read all profiles; authenticated users can only update their own profile (`auth.uid() = id`).
* **Projects**: Viewable by authenticated and anonymous users; creations and modifications restricted to project leads, creators, and admins.
* **Datasets & Observations**: Viewable across the platform; write/update operations restricted to authenticated researchers and scientists.
* **Audit Logs**: Immutable insert permissions for system events; select permissions for authenticated users.

---

## 5. Automated Triggers

1. `on_auth_user_created` on `auth.users`: Creates a corresponding `public.profiles` row upon user signup.
2. `trg_update_updated_at` on all tables: Automatically updates the `updated_at` timestamp before row updates.
3. `trg_sync_location` on all spatial tables: Automatically computes PostGIS geography point from coordinates.
