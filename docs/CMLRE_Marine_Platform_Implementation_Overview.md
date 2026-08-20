# CMLRE Marine Intelligence Platform — Implementation Overview & Working Baseline

## 1. Purpose

This document is the implementation-level baseline for the **CMLRE Marine Intelligence Platform**. It is intended for the two-person development team, Antigravity, coding agents, and future LLM sessions.

Use this together with the repository's `context.md`. Do not silently change architecture decisions. Proposed changes must be explicitly approved.

## 2. Project Identity

**Working title:** AI-Driven Unified Data Platform for Oceanographic, Fisheries, and Molecular Biodiversity Insights

The platform is intended to transform heterogeneous marine scientific inputs into a unified, queryable, spatially/temporally aligned environment for research, fisheries management, biodiversity monitoring and decision support.

Core idea:

```text
Heterogeneous Marine Data
        ↓
Ingestion
        ↓
Validation / Quality Control
        ↓
Standardisation
        ↓
Spatial + Temporal Fusion
        ↓
Unified Marine Data
        ↓
Scientific Analysis
        ↓
AI / ML Insights
        ↓
Research Workspace / Dashboard
        ↓
Decision Support
```

## 3. Target Data

### Oceanographic
CTD, NetCDF, sensor observations, temperature, salinity, dissolved oxygen, chlorophyll, pressure, pH, currents, depth.

### Fisheries
Catch, effort, species, fishing locations, gear, fishing zones, vessel information where available.

### Biodiversity
Species occurrences, Darwin Core-style records, taxonomy, species distribution and biodiversity indicators.

### Molecular / eDNA
eDNA samples, FASTA/FASTQ, barcode/reference information, taxonomic assignments, species detections and confidence.

### Imaging / Otolith
Otolith images, morphometric features, species classification and age-related information where available.

### Scientific Knowledge
Research papers, scientific documents, species information, metadata and research notes.

These inputs differ in format, schema, units, names, metadata, quality, provenance and spatial/temporal representation.

## 4. Target Users

- Marine Scientists
- Researchers
- Oceanographers
- Fisheries Scientists
- Biodiversity / Molecular Researchers
- Conservationists
- Fisheries Managers
- Decision-makers
- Research institutions

## 5. Final Technology Decisions

### Frontend
- React
- Vite
- Tailwind CSS
- Leaflet or MapLibre for the MVP 2D marine map
- Recharts / Plotly

A 3D globe is not a core MVP requirement.

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic
- Modular monolith

Frontend communicates with backend through APIs. Scientific/database logic remains in backend services.

### Database
**Supabase PostgreSQL + PostGIS** is the sole primary structured database.

### Storage
**Supabase Storage** for large/raw files:
CSV, Excel, JSON, NetCDF, CTD/TXT, FASTA/FASTQ, images, otolith images, reports, ML artifacts.

PostgreSQL stores file metadata and storage paths.

### Authentication
**Supabase Auth + JWT**. No custom password database.

### Optional RAG / Vector Search
**ChromaDB** if RAG is implemented.

Potential LLM providers:
- Gemini
- Groq

**Important:** RAG is OPTIONAL. It is an enhancement, not a core dependency. The platform must work completely without it. Implement it only after the core system is stable and only ship it if it is reliable and demonstrable.

### Scientific / Data
Pandas / Polars, NumPy, GeoPandas, Xarray, SciPy, Biopython, OpenCV.

### ML
Scikit-learn, XGBoost, PyTorch, ONNX where useful.

### Docker
Introduced later during deployment; do not create the `docker/` directory during foundation.

## 6. Repository Structure

```text
/
├── context.md
├── README.md
├── .gitignore
├── .env.example
│
├── frontend/
├── backend/
├── ml/
├── analysis/
├── rag/
├── scripts/
├── docs/
└── data_pipeline/
```

Responsibilities:

- `frontend/` — React UI, pages, maps, charts and user workflows
- `backend/` — FastAPI application, service layer, APIs, auth middleware
- `ml/` — model training/inference, feature engineering, evaluation
- `analysis/` — scientific statistics, spatial/temporal and cross-domain analysis
- `rag/` — optional embeddings, retrieval and LLM functionality
- `scripts/` — safe development/setup/seed utilities
- `docs/` — architecture, database, API and implementation documentation
- `data_pipeline/` — ingestion, detection, mapping, cleaning, QC, standardisation and provenance
- `docker/` — intentionally added only in the later deployment phase

## 7. Git Workflow

```text
main
└── dev
    ├── feature/*
    ├── fix/*
    ├── experiment/*
    └── chore/*
```

Rules:
- `main` = stable
- `dev` = integration
- all working branches start from `dev`
- merge feature work into `dev`
- promote stable `dev` to `main`
- do not create long-lived branches named `frontend`, `backend`, `ml`, etc.; branches represent work, not folders

## 8. Completed Phase 0 — Project Foundation

Completed:
- repository structure
- project/context baseline
- component READMEs
- `.gitignore`
- `.env.example`
- root README
- development conventions
- Git branch strategy

No feature implementation was intended in Phase 0.

## 9. Completed Phase 1 — Database Foundation

Supabase PostgreSQL/PostGIS schema has been created and audited.

### 21 application tables across 12 domains

1. Identity: `profiles`
2. Projects/Sources: `projects`, `data_sources`, `datasets`
3. Spatial: `stations`, `samples`
4. Oceanography: `oceanographic_observations`
5. Taxonomy/Species: `taxonomy`, `species`, `species_occurrences`
6. Fisheries: `fisheries_records`
7. eDNA: `edna_samples`, `edna_results`
8. Otolith/Vision: `otolith_samples`, `otolith_results`
9. AI/ML: `ml_models`, `predictions`
10. Scientific Analysis: `analysis_jobs`, `analysis_results`
11. Alerts: `alerts`
12. Provenance/Audit: `audit_logs`

### Database capabilities
- PostgreSQL 17.6
- PostGIS 3.5.2
- spatial `geography(Point, 4326)` fields on major marine entities
- spatial GIST indexes
- temporal/query indexes
- foreign-key integrity
- JSONB for genuinely flexible scientific metadata
- timestamp triggers
- coordinate synchronization triggers
- profile provisioning from Supabase Auth

## 10. Database Philosophy

PostgreSQL/PostGIS is the system of record for structured scientific information.

It stores:
- standardised observations
- metadata
- spatial and temporal records
- taxonomy
- datasets
- samples
- analysis results
- ML model metadata
- predictions
- alerts
- provenance

Large raw files belong in Supabase Storage.

JSONB is used only where source variability justifies flexible storage.

## 11. Authentication & Security

Conceptual flow:

```text
Frontend
  ↓
Supabase Auth
  ↓
JWT / Session
  ↓
FastAPI verification
  ↓
Application authorization
```

`profiles.id` links to `auth.users.id`.

There are no custom password or credential tables.
Roles include:
- admin
- user

RLS is enabled across the application tables.

### Current security note
The audit found broad authenticated CRUD policies on several domain tables. This is acceptable during current development/integration, but later security hardening must restrict access by role, project membership and ownership.

### Mandatory secret-handling rule
Never hardcode:
- Supabase URL
- database connection strings
- passwords
- service-role keys
- API keys

Do not put credentials into source files, migration scripts, verification scripts, documentation or logs.

When a Supabase MCP server is available, **use the Supabase MCP for Supabase administrative/schema operations**. Do not bypass the MCP with ad-hoc credential-bearing database scripts. If MCP cannot perform an operation, stop and report the limitation rather than creating an insecure workaround.

## 12. Provenance & Lineage

The intended lineage is:

```text
Data Source
    ↓
Dataset
    ↓
Sample / Observation
    ↓
Analysis
    ↓
Prediction / Result
    ↓
Alert
```

A result should eventually be traceable back to its source dataset and processing history.

## 13. Data Pipeline

```text
Raw Data
    ↓
Format Detection
    ↓
Schema Mapping
    ↓
Validation
    ↓
Cleaning
    ↓
Unit Standardisation
    ↓
Quality Control
    ↓
Spatial / Temporal Normalisation
    ↓
Provenance Recording
    ↓
PostgreSQL/PostGIS
```

Quality checks include:
- missing values
- duplicates
- invalid coordinates
- invalid timestamps
- outliers
- unit inconsistencies
- schema mismatches
- range/consistency checks

## 14. Unified Marine Data Layer

The central innovation is joining:

```text
Oceanographic Data
+
Fisheries Data
+
Biodiversity / Species Data
+
eDNA Data
+
Otolith / Image Evidence
+
Taxonomy
```

using:
- time
- latitude
- longitude
- depth
- station
- sample
- species
- dataset
- source

The platform should support spatial/temporal cross-domain queries such as finding ocean observations near a fish catch and eDNA sample within a time window.

## 15. Scientific Modules

### eDNA
Potential path:

```text
FASTA / FASTQ
→ Validation
→ Sequence preprocessing
→ Reference/barcode matching
→ Taxonomic assignment
→ Species detection
→ Confidence
→ Database
```

The MVP does not need to recreate an entire production genomics pipeline.

### Otolith
Potential path:

```text
Image
→ Preprocessing
→ Feature extraction
→ CNN / transfer learning
→ Classification / estimation
→ Confidence
→ Database
```

Keep the module replaceable.

### Taxonomy
- species search
- hierarchy
- scientific/common names
- synonyms
- external identifiers
- reference metadata

## 16. Scientific Analysis

Keep scientific analysis separate from generic AI.

Initial capabilities:
- spatial analysis
- temporal analysis
- trends
- biodiversity indicators
- species distribution
- ecosystem relationships
- cross-domain correlations

Examples:

```text
Temperature ↔ Species Presence
Oxygen ↔ Biodiversity
Fishing Pressure ↔ Species Diversity
Chlorophyll ↔ Habitat
Ocean Conditions ↔ Catch
```

## 17. AI / ML Strategy

Use a small number of meaningful models.

### Model 1 — Environmental Anomaly Detection
Purpose: detect unusual environmental conditions.
Possible features: temperature, salinity, oxygen, chlorophyll, depth.
Possible approach: Isolation Forest or other validated anomaly detection.
Output: Normal / Anomalous.

### Model 2 — Fish Habitat Suitability
Possible features:
SST, salinity, chlorophyll, oxygen, depth, latitude, longitude.
Possible models:
XGBoost / Random Forest.
Output: habitat suitability score.

### Model 3 — Catch Prediction
Possible features:
historical catch, species, temperature, chlorophyll, location, season, effort.
Possible models:
XGBoost / Random Forest.

### Optional image/species model
Only when data and time justify it.

Do not build models just to increase the AI count.

## 18. ML Governance

Model metadata should include:
- model_name
- version
- task
- algorithm
- features
- training_dataset
- metrics
- artifact_path
- created_at
- status

Predictions should retain:
- model/version
- source record
- prediction
- confidence
- location where relevant
- prediction time
- explanation metadata where applicable

AI predictions are not scientific ground truth.

## 19. FastAPI

FastAPI is the runtime application gateway.

Functional areas may include:

```text
/auth
/datasets
/uploads
/ocean
/fisheries
/species
/edna
/otolith
/analysis
/ml
/alerts
/reports
/rag
```

Exact endpoint names can evolve.

The stable architecture is:

```text
React
  ↓
FastAPI
  ↓
Service Modules
  ↓
Database / Storage / ML
```

## 20. Frontend Research Workspace

Planned areas:
- login
- command center
- data engine
- dataset explorer
- ocean explorer
- fisheries explorer
- species explorer
- eDNA explorer
- scientific analysis
- AI insights
- alerts
- reports

### Marine map
Potential layers:
- ocean observations
- fisheries activity
- species occurrences
- eDNA detections
- biodiversity indicators
- AI predictions
- risk zones

Potential filters:
- date
- depth
- species
- region
- dataset
- variable

A location panel should eventually combine ocean conditions, species, catch, eDNA, analysis and AI outputs.

## 21. Optional RAG / LLM

RAG is **optional**.

It should never block the core platform.

Correct priority:

```text
Core Platform
    ↓
Data Pipeline
    ↓
Scientific Analysis
    ↓
ML
    ↓
Dashboard
    ↓
Optional RAG / LLM
```

Potential RAG pipeline:

```text
Scientific Papers
Research Documents
Species Knowledge
Project Notes
Relevant Metadata
        ↓
Chunking
        ↓
Embeddings
        ↓
ChromaDB
        ↓
Semantic Retrieval
        ↓
Relevant Context
        ↓
LLM
        ↓
Evidence-backed Response
```

The LLM should be grounded in database results, computed analyses, retrieved documents and source metadata where possible.

### Shipping rule
Implement and ship RAG only if it is reliable, integrated and demonstrable.
If not, omit it without delaying the core system.

## 22. Alerts & Decision Support

Potential flow:

```text
Scientific Analysis / ML
        ↓
Risk / Threshold Logic
        ↓
Alert
        ↓
Dashboard
```

Potential alert types:
- environmental anomaly
- biodiversity risk
- fisheries risk
- species detection
- oxygen/hypoxia-related conditions

## 23. Reports

*Note: Reports have been removed from the MVP and will not be implemented.*

## 24. Implementation Roadmap

### Phase 0 — Project Foundation — COMPLETED
Repository structure, configuration placeholders, documentation, Git conventions.

### Phase 1 — Database Foundation — COMPLETED
Supabase PostgreSQL/PostGIS, schema, relationships, auth linkage, RLS foundation, indexes, provenance, audit and verification.

### Phase 2 — File Storage + Authentication — COMPLETED
- Supabase Storage `marine-files` bucket and logical paths
- Storage RLS policies (authenticated read/insert, owner/admin update/delete)
- `handle_new_user()` trigger for automated profile creation with `admin` and `user` roles
- File metadata linkage with `public.datasets`
- Integration guide documented in `docs/storage_auth_integration.md`

### Phase 3 — Data Ingestion Engine
- file upload
- format detection
- schema reading
- preview
- dataset registration
- processing status
- mapping to internal schema

Initial formats: TXT (converted to CSV or Excel), CSV, Excel, JSON, NetCDF, CTD where appropriate.

Target:
```text
Upload → Store → Detect → Preview → Register
```

### Phase 4 — Data Quality + Standardisation
- missing values
- duplicates
- coordinate validation
- timestamps
- outliers
- unit normalisation
- schema mapping
- quality score
- provenance

Target:
```text
Raw → Validated → Standardised → Quality-scored
```

### Phase 5 — Data Fusion + Unified Marine Data
- spatial alignment
- temporal alignment
- depth alignment
- common marine model
- cross-domain linking
- PostGIS queries
- unified views

Target:
```text
Ocean + Fisheries + Biodiversity + eDNA → Unified Marine Data
```

### Phase 6 — Scientific Analysis
- ocean trends
- fisheries trends
- species distribution
- biodiversity indicators
- spatial/temporal analysis
- correlations
- ecosystem relationships

### Phase 7 — Domain-Specific Scientific Modules
- taxonomy
- eDNA
- otolith/image
- species identification

### Phase 8 — AI / ML
Order:
1. environmental anomaly detection
2. fish habitat suitability
3. catch prediction
4. optional image/species model

For each model:
```text
Data → Features → Training → Evaluation → Storage → Inference
```

### Phase 9 — FastAPI Integration
Expose the working backend through stable APIs and connect frontend/service/database/ML layers.

### Phase 10 — Frontend Research Workspace
Implement the user-facing application using real APIs.

### Phase 11 — Interactive Marine Map
Layers, filters, time/depth controls, prediction/risk layers and location details.

### Phase 12 — Optional RAG / LLM Enhancement
Only if time, reliability and data quality permit.

### Phase 13 — Alerts + Decision Support (Optional)
Goal: convert analysis/prediction into useful notifications and dashboard alerts.

### Phase 14 — Reports + Export
*Note: Reports have been removed from the MVP and will not be implemented.*

### Phase 15 — Testing + Hardening
Backend tests, data validation tests, ML evaluation, RLS/security review, frontend tests, error handling and performance checks.

### Phase 16 — Docker + Deployment
Create `docker/`, Dockerfiles, Docker Compose, environment config and cloud deployment.

## 25. MVP Priority

### MVP-1 — Core path
```text
Login
↓
Upload CSV
↓
Supabase Storage
↓
Dataset Metadata
↓
Validation
↓
PostgreSQL/PostGIS
↓
Map
```

### MVP-2 — Cross-domain integration
```text
Ocean + Fisheries + Biodiversity
↓
Fusion
↓
Unified Map
```

### MVP-3 — Scientific intelligence
```text
Unified Data
↓
Scientific Analysis
↓
ML Prediction
↓
Risk / Insight
```

### MVP-4 — Specialized science
eDNA + Otolith + Taxonomy

### MVP-5 — Optional AI assistant
RAG + LLM

### MVP-6 — Productisation
Alerts + Reports + Testing + Deployment

## 26. Two-Person Team

### Person 1 — Frontend / Product Integration
Own:
- React/Vite/Tailwind
- maps/charts
- dashboard
- research workspace
- auth UI
- API integration
- reports/alerts UI

### Person 2 — Backend / Data / Scientific / AI
Own:
- Supabase/PostgreSQL/PostGIS
- Supabase Storage
- FastAPI
- ingestion
- QC
- standardisation
- fusion
- scientific analysis
- eDNA
- otolith
- ML
- optional RAG backend

### Shared
Architecture, API contracts, database changes, testing, Git integration, deployment, demo, documentation and scientific validation.

## 27. AI-Assisted Development Rules

Use coding AI for:
- boilerplate
- SQL
- FastAPI scaffolding
- Pydantic models
- React components
- tests
- preprocessing utilities
- debugging
- documentation

Human review is mandatory for:
- scientific assumptions
- data quality rules
- eDNA interpretation
- taxonomy
- ML evaluation
- scientific claims
- risk thresholds
- scientific conclusions

## 28. Completed Status

```text
Repository Foundation        ✅
Supabase PostgreSQL          ✅
PostGIS                      ✅
Database Schema              ✅
Auth Foundation              ✅
RLS Foundation              ✅
Spatial Indexes              ✅
Provenance Structure         ✅
ML Metadata Tables           ✅
Analysis Tables              ✅
Alerts Tables                ✅
Database Documentation       ✅
Database Audit               ✅
Supabase Storage Bucket      ✅
Storage Security & Policies  ✅
Auth ↔ Profile Automation   ✅
Storage Integration Guide    ✅
```

Not yet implemented:

```text
Real login UI               ⏳
FastAPI app                 ⏳
Data ingestion              ⏳
QC / standardisation        ⏳
Data fusion                 ⏳
Scientific analysis         ⏳
eDNA processing             ⏳
Otolith processing          ⏳
ML models                   ⏳
Frontend dashboard          ⏳
Marine map                  ⏳
Alerts engine               ⏳
Reports                     ⏳
RAG / LLM                   ⏳ OPTIONAL
Docker / deployment         ⏳
```

## 29. Immediate Next Step

The next implementation target is **Phase 3 — Data Ingestion Engine**.

Do not jump to ML or RAG.

Establish:

```text
File Upload / Ingestion
+
Format Detection (TXT to CSV)
+
Dataset Metadata Registration
```

Then build the first real ingestion vertical slice:

```text
Authenticated Researcher
        ↓
Upload Dataset
        ↓
Supabase Storage
        ↓
Register Dataset
        ↓
Validate
        ↓
Standardise
        ↓
PostgreSQL/PostGIS
        ↓
Query
        ↓
Visualise
```

## 30. Definition of Done for the MVP

The core MVP is convincing when a researcher can:

1. Sign in.
2. Upload a realistic marine dataset.
3. Store the original file in Supabase Storage.
4. Convert CMLRE TXT files into CSV or Excel files.
5. Register metadata in PostgreSQL.
6. Validate and standardise the data.
7. Calculate/report quality.
8. Store observations with spatial and temporal information.
9. Combine at least oceanographic + fisheries + biodiversity information.
10. Run meaningful scientific analysis.
11. Visualise results on a map/dashboard.
12. Run at least one meaningful ML model.
13. View a prediction/risk/insight.
14. Demonstrate an eDNA or otolith workflow.
15. Trace results back to the dataset/source.
16. (Optional) Demonstrate RAG/LLM if it has been implemented reliably.

**RAG is NOT required for the definition of done.**

The platform is successful when the core scientific data journey works end-to-end even without the LLM layer.

## 31. Final Mental Model

### One sentence
> A unified marine-data platform that transforms heterogeneous oceanographic, fisheries and biodiversity information into standardised, spatially aligned scientific data and actionable AI-assisted insights.

### Process
```text
Marine Data
→ Ingestion
→ Quality
→ Standardisation
→ Fusion
→ Scientific Analysis
→ ML
→ Dashboard
→ Decision Support
```

### Implementation
```text
React / Vite / Tailwind
        ↓
FastAPI / Python
        ↓
Data + Scientific Services
        ↓
Supabase PostgreSQL + PostGIS
        +
Supabase Storage
        +
Supabase Auth

Optional:
ChromaDB + Gemini/Groq
```

The product is not defined by the technology names. Its core value is:

> **Unify heterogeneous marine information, align it spatially and temporally, analyse it scientifically, and turn it into useful research and decision-support outputs.**
