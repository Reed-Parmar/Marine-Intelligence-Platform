# CMLRE Marine Intelligence Platform — Backend API

FastAPI backend providing REST APIs for cross-domain marine intelligence, oceanography (CTD), fisheries catch, species taxonomy, and datasets quality control.

---

## 1. Quickstart

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- PostgreSQL + PostGIS (Supabase instance)

### Installation
```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and fill in the required variables (never commit real secrets):
```env
# Server
PORT=8000
DEBUG=True
ENVIRONMENT=development

# Supabase Auth & Storage
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_JWT_SECRET=<your-jwt-secret>

# Database Connection (PostgreSQL + PostGIS)
DATABASE_URL=postgresql://postgres:<password>@db.<your-project>.supabase.co:5432/postgres

# CORS Origins
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 2. Running Locally

Start the development server with automatic reloading:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

- **API Base URL**: `http://localhost:8000/api/v1`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## 3. Running Automated Tests

Run the backend test suite:
```bash
pytest backend/tests/ -v
```

---

## 4. API Structure & Implemented Endpoints

### Health
- `GET /health` — Check backend service health and version.

### Authentication & Users
- `GET /api/v1/auth/me` — Return current authenticated user profile & role.
- `POST /api/v1/auth/login` — Authenticate via Supabase Auth.
- `POST /api/v1/auth/logout` — Invalidate user session.
- `GET /api/v1/users/me` — Return current profile.
- `GET /api/v1/users` *(Admin only)* — List platform users.
- `PATCH /api/v1/users/{user_id}/role` *(Admin only)* — Assign role (`admin`, `user`, `researcher`, `scientist`, `viewer`).

### Datasets & Quality
- `GET /api/v1/datasets` — List datasets with domain (`oceanography`, `fisheries`, etc.) and quality filters.
- `GET /api/v1/datasets/{dataset_id}` — Get single dataset metadata.
- `POST /api/v1/datasets` — Register a dataset.
- `PATCH /api/v1/datasets/{dataset_id}` — Update dataset metadata.
- `DELETE /api/v1/datasets/{dataset_id}` — Delete a dataset.
- `GET /api/v1/datasets/{dataset_id}/quality` — Return 0–100 quality score, status (`passed`, `flagged`, `failed`), and validation notes.
- `GET /api/v1/datasets/{dataset_id}/provenance` — Return ingestion metadata and audit logs.

### Uploads & Phase 3 Integration Hook
- `POST /api/v1/uploads` — Upload raw dataset file, stage, and detect format.
- `GET /api/v1/uploads/{upload_id}` — Get upload status and detected format.
- `GET /api/v1/uploads/{upload_id}/preview` — Return parsed preview (first 10 rows).
- `POST /api/v1/uploads/{upload_id}/process` — Execute ingestion parser and Phase 4 Quality Pipeline, registering the dataset.
- `DELETE /api/v1/uploads/{upload_id}` — Cancel staged upload.

### Unified Marine (Cross-Domain)
- `GET /api/v1/marine/observations` — Unified observations across oceanography, fisheries, and biodiversity.
- `GET /api/v1/marine/summary` — Aggregate summary counts across all marine datasets.
- `POST /api/v1/marine/query` — Structured multi-dimensional spatial/temporal query.

### Oceanography
- `GET /api/v1/ocean/observations` — Ocean observations with depth, temperature, salinity, DO filters.
- `GET /api/v1/ocean/observations/{observation_id}` — Get single ocean observation.
- `GET /api/v1/ocean/summary` — Aggregate min/max/avg stats for temperature, salinity, oxygen, and depth.
- `GET /api/v1/ocean/trends` — Time-series trends bucketed by day, week, month, or year.

### Fisheries
- `GET /api/v1/fisheries/observations` — Catch records with species, fishing zone, and gear filters.
- `GET /api/v1/fisheries/observations/{observation_id}` — Get single catch record.
- `GET /api/v1/fisheries/summary` — Total catch (kg), effort (hours), distinct species count.
- `GET /api/v1/fisheries/trends` — Catch trends over time.

### Species & Taxonomy
- `GET /api/v1/species` — Search/list species from taxonomy catalog.
- `GET /api/v1/species/{species_id}` — Full taxonomic profile.
- `GET /api/v1/species/{species_id}/occurrences` — Spatial/temporal occurrences.
- `GET /api/v1/species/{species_id}/distribution` — Geographic bounding box and depth distribution.

### Scientific Modules & Deferred Phase Hooks
- `GET /api/v1/edna/samples` & `GET /api/v1/edna/detections` — Query real `public.edna_samples` and `public.edna_results` from database.
- `GET /api/v1/otolith/samples` — Query real `public.otolith_samples` from database.
- `POST /api/v1/otolith/analyse` *(Deferred — 501 Not Implemented)* — Clean integration hook for Phase 7 Otolith Computer Vision annuli detection pipeline.
- `POST /api/v1/analysis/correlation` *(Deferred — 501 Not Implemented)* — Clean integration hook for Phase 6 scientific statistical analysis module.
- `GET /api/v1/ml/models` — Query active models registered in `public.ml_models`.
- `POST /api/v1/ml/predict` *(Deferred — 501 Not Implemented)* — Clean integration hook for Phase 8 ML inference models.
- `GET /api/v1/alerts` & `GET /api/v1/alerts/summary` — Query real alerts from `public.alerts`.

---

## 5. Upload Processing & Dataset Registration Flow

The upload and dataset flow connects as follows:
```text
Frontend (POST /api/v1/uploads)
          ↓
UploadService.create_upload()  [Staging via _STAGING_UPLOADS & format detection (CSV/TSV/TXT)]
          ↓
Frontend (GET /api/v1/uploads/{id}/preview) [Parses top 10 rows with delimiter awareness]
          ↓
POST /api/v1/uploads/{upload_id}/process
          ↓
Delimited Text Parser          [Parses raw records using csv.DictReader]
          ↓
Phase 4 Quality Pipeline       [data_pipeline.QualityPipeline: computes QC score, validation notes, provenance]
          ↓
Dataset Registration           [Persists record in public.datasets (PostgreSQL + PostGIS)]
          ↓
Available for Queries          [/api/v1/datasets, /api/v1/marine/observations, /api/v1/ocean, etc.]
```


