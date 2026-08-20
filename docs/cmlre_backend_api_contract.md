# CMLRE Marine Intelligence Platform — Backend API Contract

## Purpose

This document is the implementation blueprint for the FastAPI backend of the CMLRE Marine Intelligence Platform.

This is a hackathon implementation. The priority is:

1. The complete demo flow should work.
2. APIs should be simple and easy for the frontend to consume.
3. The backend should integrate cleanly with Supabase/PostgreSQL/PostGIS.
4. Avoid unnecessary infrastructure and abstractions.
5. Do not implement future scientific functionality until it is actually needed.

The backend must be ready to connect to the Phase 3 ingestion/data work being implemented by another team member.

---

# 1. Backend Structure

Use a simple FastAPI structure:

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── uploads.py
│   │       ├── datasets.py
│   │       ├── marine.py
│   │       ├── ocean.py
│   │       ├── fisheries.py
│   │       ├── species.py
│   │       ├── edna.py
│   │       ├── otolith.py
│   │       ├── analysis.py
│   │       ├── ml.py
│   │       └── alerts.py
│   │
│   ├── services/
│   │   ├── dataset_service.py
│   │   ├── upload_service.py
│   │   ├── marine_service.py
│   │   ├── ocean_service.py
│   │   ├── fisheries_service.py
│   │   ├── species_service.py
│   │   └── analysis_service.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── dataset.py
│   │   ├── upload.py
│   │   ├── marine.py
│   │   ├── ocean.py
│   │   ├── fisheries.py
│   │   ├── species.py
│   │   └── analysis.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── queries.py
│   │
│   └── auth/
│       └── supabase_auth.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_datasets.py
│   ├── test_uploads.py
│   ├── test_marine.py
│   └── test_health.py
│
├── requirements.txt
├── .env.example
└── README.md
```

Keep this structure practical. Do not add extra layers such as repositories, dependency-injection frameworks, background-job systems, microservices, Redis, Kafka, Celery, or similar infrastructure unless an actual requirement appears.

---

# 2. API Base

All application endpoints use:

```text
/api/v1
```

The API should also expose:

```text
GET /health
```

One-line explanation: Check that the backend is running and able to respond.

---

# 3. Authentication

Supabase Auth remains the authentication provider.

FastAPI must validate the Supabase JWT for protected endpoints.

### POST /api/v1/auth/login

Authenticate a user through the application's Supabase authentication flow.

### GET /api/v1/auth/me

Return the currently authenticated user's profile and role.

### POST /api/v1/auth/logout

Log out the current user/session where applicable; do not create a separate authentication system.

---

# 4. Users

### GET /api/v1/users/me

Return the current user's profile, role and basic account information.

### GET /api/v1/users

Admin-only endpoint to list platform users.

### PATCH /api/v1/users/{user_id}/role

Admin-only endpoint to change a user's application role.

Do not build a large user-management system.

---

# 5. Uploads

These endpoints must be compatible with the Phase 3 ingestion implementation.

### POST /api/v1/uploads

Accept a dataset file/upload request and create an upload record.

### GET /api/v1/uploads/{upload_id}

Return upload status, detected format and processing status.

### GET /api/v1/uploads/{upload_id}/preview

Return a small preview of the parsed dataset for frontend display.

### POST /api/v1/uploads/{upload_id}/process

Start/continue processing of the uploaded dataset through the available ingestion and quality pipeline.

### DELETE /api/v1/uploads/{upload_id}

Remove/cancel an upload that has not been finalized as a dataset.

The backend must not assume the exact internal implementation of Phase 3. Provide a clean interface so the Phase 3 module can be connected when it is merged.

---

# 6. Datasets

### GET /api/v1/datasets

List datasets accessible to the authenticated user, with simple filters such as domain, status and quality status.

### GET /api/v1/datasets/{dataset_id}

Return complete metadata for one dataset.

### POST /api/v1/datasets

Register a dataset and its metadata.

### PATCH /api/v1/datasets/{dataset_id}

Update editable dataset metadata.

### DELETE /api/v1/datasets/{dataset_id}

Delete/archive a dataset according to the existing database/storage rules.

### GET /api/v1/datasets/{dataset_id}/quality

Return quality score, quality status and validation issues for a dataset.

### GET /api/v1/datasets/{dataset_id}/provenance

Return dataset provenance and important processing/transformation information.

Reuse the existing Supabase `datasets` structure and Phase 4 quality/provenance fields wherever possible.

---

# 7. Unified Marine APIs

This is the important cross-domain part of the backend.

### GET /api/v1/marine/observations

Return unified marine observations across relevant domains using filters such as time, location, depth, species, variable and dataset.

### GET /api/v1/marine/summary

Return a compact cross-domain summary for a selected spatial/temporal region.

### POST /api/v1/marine/query

Accept a structured spatial/temporal query and return matching information across oceanography, fisheries and biodiversity data.

Example query dimensions:

```text
date_from
date_to
latitude/longitude or bounding box
depth_min
depth_max
species
domain
dataset_id
variable
```

The `/marine` service should combine available domain data rather than simply exposing one database table.

---

# 8. Oceanography APIs

### GET /api/v1/ocean/observations

Return oceanographic observations with filters for location, time, depth, variable and dataset.

### GET /api/v1/ocean/observations/{observation_id}

Return one oceanographic observation.

### GET /api/v1/ocean/trends

Return aggregated temporal trends for supported ocean variables such as temperature, salinity and dissolved oxygen.

### GET /api/v1/ocean/summary

Return an aggregated oceanographic summary for a selected region/time period.

Do not put scientific calculations directly inside route functions.

---

# 9. Fisheries APIs

### GET /api/v1/fisheries/observations

Return fisheries/catch observations with simple filters.

### GET /api/v1/fisheries/observations/{observation_id}

Return one fisheries observation.

### GET /api/v1/fisheries/trends

Return aggregated fisheries/species trends over time.

### GET /api/v1/fisheries/summary

Return an aggregated fisheries summary for a selected region/time period.

---

# 10. Species and Biodiversity APIs

### GET /api/v1/species

Search/list species from the taxonomy/species data.

### GET /api/v1/species/{species_id}

Return taxonomy and basic species information.

### GET /api/v1/species/{species_id}/occurrences

Return spatial/temporal occurrences for a species.

### GET /api/v1/species/{species_id}/distribution

Return distribution information suitable for map visualisation.

---

# 11. eDNA APIs

Implement only the basic API layer needed to expose existing eDNA data.

### GET /api/v1/edna/samples

List/search eDNA samples.

### GET /api/v1/edna/samples/{sample_id}

Return eDNA sample metadata and associated detections.

### GET /api/v1/edna/detections

Return eDNA species detections with location, time and confidence where available.

### GET /api/v1/edna/species/{species_id}

Return eDNA detections associated with a species.

Do not implement a complex sequence-processing pipeline in the FastAPI backend.

---

# 12. Otolith APIs

### GET /api/v1/otolith/samples

List/search otolith samples and associated images/metadata.

### GET /api/v1/otolith/samples/{sample_id}

Return an otolith sample and its metadata.

### POST /api/v1/otolith/analyse

Accept an otolith image/reference and start an analysis using an available otolith processing module.

### GET /api/v1/otolith/analyses/{analysis_id}

Return an otolith analysis result.

If the scientific otolith module is not ready yet, keep this endpoint as a clean integration point rather than inventing analysis functionality.

---

# 13. Analysis APIs

### GET /api/v1/analysis

List available/completed analyses.

### POST /api/v1/analysis

Create/run a supported analysis.

### GET /api/v1/analysis/{analysis_id}

Return analysis status and metadata.

### GET /api/v1/analysis/{analysis_id}/results

Return analysis results.

### POST /api/v1/analysis/correlation

Run a supported cross-domain correlation analysis, such as ocean parameters versus species/fisheries observations.

### GET /api/v1/analysis/trends

Return standardized trend results.

The analysis endpoints should call service/scientific modules rather than containing scientific algorithms directly.

---

# 14. ML APIs

Create the API contract, but keep implementation minimal until actual models are available.

### GET /api/v1/ml/models

List available models.

### GET /api/v1/ml/models/{model_id}

Return model metadata.

### POST /api/v1/ml/predict

Run a prediction using an available model.

### GET /api/v1/ml/predictions/{prediction_id}

Return a prediction result.

Do not build placeholder ML models merely to populate endpoints.

---

# 15. Alert APIs

These can remain minimal and can be implemented when alert generation exists.

### GET /api/v1/alerts

List alerts.

### GET /api/v1/alerts/{alert_id}

Return alert details.

### PATCH /api/v1/alerts/{alert_id}

Acknowledge/update an alert.

### GET /api/v1/alerts/summary

Return alert counts by type/severity.

---

# 16. RAG API

Do not make RAG a dependency of the rest of the backend.

### POST /api/v1/rag/query

Accept a scientific question and return an answer with supporting evidence when the RAG module is available.

### GET /api/v1/rag/sources/{query_id}

Return the sources/evidence associated with a RAG response.

This should be implemented later when the RAG/scientific assistant module is ready.

---

# 17. Response Format

Use a simple consistent response format.

Successful object response:

```json
{
  "data": {},
  "meta": {}
}
```

Successful list response:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 50,
    "total": 0
  }
}
```

Error response:

```json
{
  "error": {
    "code": "DATASET_NOT_FOUND",
    "message": "Dataset not found."
  }
}
```

Do not make the response wrapper unnecessarily complicated.

---

# 18. Common API Filters

Where relevant, support simple query parameters for:

```text
dataset_id
domain
species_id
variable
date_from
date_to
depth_min
depth_max
latitude
longitude
bbox
quality_status
page
page_size
```

Do not implement every filter on every endpoint. Only use filters that make sense for the endpoint.

---

# 19. Important Backend Rules

1. FastAPI handles HTTP/API concerns.
2. Services handle application logic.
3. Scientific/data-processing modules remain separate.
4. Supabase/PostgreSQL/PostGIS remains the main database.
5. Supabase Auth remains the authentication provider.
6. Do not duplicate Phase 3 ingestion logic.
7. Do not duplicate Phase 4 quality/standardisation logic.
8. Preserve the Phase 3 → Phase 4 → database flow.
9. Do not expose raw database implementation details unnecessarily.
10. Keep the implementation simple enough to debug quickly.

---

# 20. Implementation Priority

Do not spend equal effort on every endpoint.

Implement and test in this order:

## Priority 1 — Must work for the demo

```text
GET  /health

GET  /api/v1/auth/me

GET  /api/v1/datasets
GET  /api/v1/datasets/{dataset_id}
GET  /api/v1/datasets/{dataset_id}/quality
GET  /api/v1/datasets/{dataset_id}/provenance

POST /api/v1/uploads
GET  /api/v1/uploads/{upload_id}
GET  /api/v1/uploads/{upload_id}/preview

GET /api/v1/marine/observations
GET /api/v1/marine/summary

GET /api/v1/ocean/observations
GET /api/v1/fisheries/observations
GET /api/v1/species
GET /api/v1/species/{species_id}
GET /api/v1/species/{species_id}/occurrences
```

## Priority 2 — Implement when corresponding data/modules are ready

```text
POST /api/v1/uploads/{upload_id}/process
POST /api/v1/datasets
PATCH /api/v1/datasets/{dataset_id}

GET /api/v1/ocean/trends
GET /api/v1/ocean/summary

GET /api/v1/fisheries/trends
GET /api/v1/fisheries/summary

POST /api/v1/marine/query

GET /api/v1/edna/...
GET /api/v1/otolith/...
GET /api/v1/analysis/...
```

## Priority 3 — Later

```text
ML
Alerts
RAG
```

The backend must not contain fake functionality simply because an endpoint is documented.

---

# 21. Phase 3 Integration Requirement

Phase 3 is currently being implemented separately.

The backend must therefore be designed so that the following future flow works without redesign:

```text
Frontend
   ↓
POST /uploads
   ↓
Phase 3 ingestion
   ↓
Phase 4 quality + standardisation
   ↓
Dataset registration
   ↓
PostgreSQL/Supabase
   ↓
GET /datasets
GET /marine/observations
GET /ocean/observations
...
```

Do not block backend development waiting for Phase 3 to finish.

Use clear service interfaces/mocks where necessary, then replace the temporary integration point when Phase 3 is merged.

---

# 22. Explicit Non-Goals

Do NOT add:

- microservices
- Kafka
- Redis
- Celery
- Airflow
- Spark
- Kubernetes
- GraphQL
- separate authentication service
- separate database
- unnecessary caching
- complex repository patterns
- complex event systems

This is a hackathon project. Reliability and a working demo are more important than architectural sophistication.
