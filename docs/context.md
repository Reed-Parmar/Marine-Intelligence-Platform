# CMLRE Marine Data Platform — Project Context

## 1. Project Identity

**Working title:** AI-Driven Unified Data Platform for Oceanographic, Fisheries, and Molecular Biodiversity Insights

**Organisation/context:** CMLRE, Kochi (Centre for Marine Living Resources & Ecology), an attached office under the Ministry of Earth Sciences, Government of India.

The platform brings heterogeneous marine datasets and scientific analyses into one unified environment instead of forcing researchers to work across disconnected datasets and specialised tools.

---

# 2. Core Problem

Marine scientific information exists in heterogeneous forms:

- Oceanographic observations
- CTD data
- NetCDF data
- Sensor data
- Fisheries records
- Biodiversity / occurrence records
- Darwin Core data
- Molecular / eDNA sequences
- FASTA / FASTQ files
- Otolith images
- Taxonomic information
- Scientific literature and metadata

These sources differ in format, schema, units, naming conventions, metadata, provenance, spatial representation and temporal representation.

The platform therefore needs to:

> **Ingest → validate → standardise → fuse → analyse → interpret → visualise**

The central value proposition is:

> Convert heterogeneous marine scientific inputs into a unified, queryable and analysable marine data layer, then combine scientific analysis with AI-assisted interpretation to generate useful research insights.

---

# 3. Target Users

- Marine Scientists
- Researchers
- Conservationists
- Fisheries Managers
- Decision-makers

The platform is primarily research/science oriented while also supporting conservation, fisheries-management and decision-support use cases.

---

# 4. Core Scientific Workflow

```text
Marine Data
    ↓
Data Ingestion
    ↓
Data Quality Control
    ↓
Data Standardisation
    ↓
Data Fusion & Spatial-Temporal Alignment
    ↓
Unified Marine Data
    ↓
Scientific / Domain Analysis
    ↓
AI / ML Insights
    ↓
Dashboard / Research Workspace
    ↓
End Users
```

The core innovation is the **Data Fusion & Spatial-Temporal Alignment** layer.

The platform must connect data using common dimensions such as:

- Time
- Latitude
- Longitude
- Depth
- Species
- Sample
- Station
- Dataset

---

# 5. Final Technology Decisions

## Frontend

- React
- Vite
- Tailwind CSS
- Leaflet or MapLibre for 2D maps
- Recharts / Plotly for visualisation

A 2D interactive marine map is preferred for the MVP. A 3D globe is not a core requirement.

## Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic
- Modular monolith architecture

All scientific operations should be accessed through FastAPI rather than the frontend directly accessing internal processing code.

## Primary Database

**Supabase PostgreSQL + PostGIS**

This is the primary structured and spatial database.

It stores:

- Users / application profiles
- Projects
- Datasets
- Data sources
- Stations
- Samples
- Oceanographic observations
- Fisheries records
- Species / taxonomy
- Species occurrences
- eDNA results
- Otolith metadata/results
- Scientific analysis results
- ML model metadata
- Predictions
- Alerts
- Audit/provenance information

## Authentication

**Supabase Auth + JWT**

Do not build a custom password/authentication database.

Application-level user information and roles are stored in PostgreSQL and linked to Supabase Auth.

Example roles:

- Admin
- User

## File Storage

**Supabase Storage**

Raw and large files are stored outside PostgreSQL:

- CSV
- Excel
- JSON
- NetCDF
- CTD files
- FASTA / FASTQ
- Images
- Otolith images
- Reports

PostgreSQL stores the file metadata and storage path.


## RAG / Vector Store

**ChromaDB**

Used only for semantic/vector retrieval, not as the primary scientific database.

Planned content:

- Scientific literature embeddings
- Marine research documents
- Species knowledge
- Useful dataset/document metadata

## LLM

External LLM provider:

- Gemini
- Groq

The final provider can be selected during implementation based on access, reliability, latency and cost.

## Scientific / Data Libraries

- Pandas / Polars
- NumPy
- GeoPandas
- Xarray
- SciPy
- Biopython
- OpenCV

## ML

- Scikit-learn
- XGBoost
- PyTorch
- ONNX where useful for deployment

## Containerisation / Deployment

Docker and Docker Compose will be introduced in a later phase.

Do not create the `docker/` directory during Phase 0.

---

# 6. Repository Structure

The locked top-level structure is:

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

The `docker/` directory is intentionally introduced only in a later implementation phase.

Suggested responsibilities:

```text
frontend/       → React/Vite/Tailwind UI
backend/        → FastAPI application and service layer
ml/             → ML training/inference/model utilities
analysis/       → scientific and cross-domain analysis
rag/            → embeddings/retrieval/LLM functionality
scripts/        → setup, utility and seed scripts
docs/           → architecture, API, database and developer documentation
data_pipeline/  → ingestion, QC, standardisation, transformation and provenance
```

---

# 7. Git Workflow

Branches:

```text
main
└── dev
    ├── feature/*
    ├── fix/*
    ├── experiment/*
    └── chore/*
```

Rules:

- `main` is the stable branch.
- `dev` is the integration branch.
- Every working branch is created from `dev`.
- Feature/fix/experiment/chore branches are merged into `dev`.
- `main` receives stable releases from `dev`.
- Do not develop directly on `main`.

---

# 8. Database Philosophy

PostgreSQL/PostGIS is the system of record for structured marine data.

The database should preserve:

- Original source information
- Standardised values
- Units
- Spatial information
- Temporal information
- Taxonomy
- Provenance
- Quality information

Do not discard provenance merely because values have been cleaned or standardised.

The goal is not only to store a cleaned value, but to preserve enough context to explain:

> where it came from → how it was processed → how it was analysed → which result used it

---

# 9. Data Quality Philosophy

The data pipeline must explicitly handle:

- Missing values
- Duplicate records
- Invalid coordinates
- Invalid timestamps
- Outliers
- Unit inconsistencies
- Schema mismatches
- Range/consistency violations

Each dataset should have a quality status/score and validation information where appropriate.

Oceanographic quality-control concepts such as QARTOD-style checks may be incorporated where useful.

---

# 10. Scientific Modules

## Oceanographic Analysis

Examples:

- Temperature trends
- Salinity trends
- Dissolved oxygen trends
- Chlorophyll trends
- Environmental anomaly detection
- Spatial/temporal analysis

## Fisheries Analysis

Examples:

- Catch trends
- Species distribution
- Fishing pressure
- Fishing effort
- Catch/environment relationships
- Habitat suitability

## Biodiversity / Taxonomy

Examples:

- Species lookup
- Taxonomic hierarchy
- Species occurrences
- Species distribution
- Biodiversity indicators

## eDNA / Molecular Analysis

Potential pipeline:

```text
FASTA / FASTQ
    ↓
Validation
    ↓
Sequence preprocessing
    ↓
Reference / barcode matching
    ↓
Taxonomic identification
    ↓
Species detection + confidence
    ↓
PostgreSQL
```

The MVP does not need to implement a complete genomics research pipeline from scratch. The platform must demonstrate the integration and scientific result flow.

## Otolith / Image Analysis

Potential pipeline:

```text
Image
    ↓
Preprocessing
    ↓
Feature extraction
    ↓
CNN / transfer learning
    ↓
Species / age classification
    ↓
Confidence
    ↓
PostgreSQL
```

Keep this modular and realistic for the available data and time.

---

# 11. Scientific Analysis Layer

Scientific analysis operates across domains.

Core capabilities:

- Spatial analysis
- Temporal analysis
- Cross-domain correlation
- Biodiversity indicators
- Species analysis
- Ecosystem relationships
- Ecosystem risk analysis

Examples:

```text
Temperature ↔ Species Presence
Oxygen ↔ Biodiversity
Fishing Pressure ↔ Species Diversity
Chlorophyll ↔ Fish Habitat
Ocean Conditions ↔ Catch
```

Scientific analysis must remain distinct from generic AI.

---

# 12. AI / ML Strategy

The project should use AI/ML where it provides meaningful scientific value.

Do not build many models just for the sake of calling the system AI-powered.

## ML Model 1 — Environmental Anomaly Detection

Purpose:

Detect unusual marine environmental conditions.

Possible features:

- Temperature
- Salinity
- Dissolved oxygen
- Chlorophyll
- Depth

Possible model:

- Isolation Forest
- Other validated anomaly-detection methods

Output:

```text
Normal / Anomalous
```

## ML Model 2 — Fish Habitat Suitability

Purpose:

Predict habitat suitability/species presence.

Possible features:

- SST
- Salinity
- Chlorophyll
- Oxygen
- Depth
- Latitude
- Longitude

Possible models:

- XGBoost
- Random Forest

Output:

```text
Habitat Suitability Score
```

## ML Model 3 — Fisheries / Catch Prediction

Purpose:

Forecast expected catch or catch intensity.

Possible features:

- Historical catch
- Species
- Temperature
- Chlorophyll
- Location
- Season
- Fishing effort

Possible models:

- XGBoost
- Random Forest

## Optional Model — Species/Image Classification

Use image/eDNA evidence where the available dataset supports a meaningful prototype.

ML models must be evaluated with appropriate metrics and must not be presented as scientific ground truth.

---

# 13. ML Model Management

Maintain model metadata in PostgreSQL.

Example fields:

```text
model_name
version
task
algorithm
features
training_dataset
metrics
artifact_path
created_at
status
```

Predictions should retain:

```text
model_id
model_version
input/source reference
prediction
confidence/score
location where relevant
prediction_time
metadata/explanation
```

MLflow can be introduced later if model versioning becomes complex, but it is not required for the foundation.

---

# 14. FastAPI Application Layer

The API acts as the gateway between frontend and scientific/backend services.

Planned functional areas:

```text
/api/auth
/api/datasets
/api/uploads
/api/ocean
/api/fisheries
/api/species
/api/edna
/api/otolith
/api/analysis
/api/ml
/api/alerts
/api/reports
/api/rag
```

Names may change during implementation. The functional responsibilities are more important than exact endpoint names.

The frontend should never directly access internal scientific-processing modules.

---

# 15. RAG / LLM Strategy

RAG is strictly optional. If it is implemented successfully, only then will it be shown; otherwise, it will be removed from the final MVP.
RAG is part of the target solution, but it is deliberately implemented **after the core platform is working**.

Order:

```text
Core Platform
    ↓
Data + Scientific Analysis
    ↓
Dashboard
    ↓
RAG / AI Enhancement
```

RAG pipeline:

```text
Scientific Documents
Research Literature
Species Knowledge
Project Notes
Dataset Metadata
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
Evidence-backed Scientific Response
```

The AI should not invent scientific conclusions.

Where possible, answers should be grounded in:

- Database results
- Scientific analysis
- Retrieved documents
- Dataset/source metadata

The core platform must continue working even when the LLM is unavailable.

---

# 16. Research Dashboard

The frontend is a single research-facing application.

Planned modules:

### Command Center

- Dataset count
- Observations
- Species
- eDNA records
- Active analyses
- Alerts

### Data Engine

- Dataset upload
- Dataset explorer
- Processing status
- Quality score
- Validation results
- Provenance

### Ocean Explorer

- Temperature
- Salinity
- Oxygen
- Chlorophyll
- Depth
- Time filters

### Fisheries Explorer

- Catch
- Species
- Fishing effort
- Fishing zones
- Trends

### Species Explorer

- Species search
- Taxonomy
- Distribution
- Occurrences
- eDNA detections

### eDNA Explorer

- Samples
- Species detected
- Confidence
- Location
- Time

### AI Insights

- Predictions
- Anomalies
- Risk scores
- Scientific summaries

### Alerts

- Environmental anomalies
- Biodiversity risk
- Fisheries risk
- Species alerts

### Reports

- PDF
- CSV
- Analysis summaries
- Map/results export

---

# 17. Interactive Marine Map

The map should be a major demonstration component.

Potential layers:

- Ocean observations
- Fisheries activity
- Species occurrences
- eDNA detections
- Biodiversity hotspots
- AI predictions
- Risk zones

Filters:

- Date
- Depth
- Species
- Region
- Dataset
- Variable

A location interaction should be able to combine:

```text
Location
Time
Depth
Ocean condition
Species
Catch
eDNA
Scientific analysis
AI prediction
```

This is the visible demonstration of cross-domain data fusion.

---

# 18. Alerts / Decision Support

Connect analytics and ML outputs to an alert layer.

Example:

```text
Environmental anomaly
        ↓
ML / scientific analysis
        ↓
Threshold / risk condition
        ↓
Alert
        ↓
Dashboard
```

Example alert:

```text
HIGH BIODIVERSITY RISK

Region: Arabian Sea
Confidence: 86%

Potential contributing factors:
↑ SST
↓ Oxygen
↑ Fishing pressure
↓ Species diversity
```

Alerts are decision-support outputs, not automatic scientific truth.

---

# 19. Reports

*Note: Reports functionality has been removed from the scope of the MVP. This feature will not be implemented.*

---

# 20. Implementation Phases

This is the **locked implementation plan**.

## Phase 0 — Project Foundation

Goal: establish the repository and development foundation only.

Tasks:

- Create Git repository
- Create `main` and `dev` branches
- Establish feature/fix/experiment/chore branching convention
- Create top-level folder structure
- Create placeholder files
- Create `.gitignore`
- Create `.env.example`
- Create root README
- Establish basic development conventions
- Lock the project structure

Do NOT:

- Create database tables
- Connect MCP
- Implement APIs
- Build frontend pages
- Build ML models
- Implement RAG
- Add Docker

**Deliverable:**

```text
Stable repository foundation
```

---

## Phase 1 — Database Foundation

Goal: establish the real Supabase backend foundation.

Tasks:

- Create Supabase project/connection
- Enable PostGIS
- Design and create relational schema
- Create profiles/role structure linked to Supabase Auth
- Create projects/datasets/data source tables
- Create stations/samples
- Create oceanographic tables
- Create fisheries tables
- Create species/taxonomy/occurrence tables
- Create eDNA tables
- Create otolith tables
- Create analysis tables
- Create ML metadata/prediction tables
- Create alerts
- Add provenance/audit information
- Add required indexes and spatial indexes
- Configure initial Row Level Security policies

**Deliverable:**

```text
Working PostgreSQL + PostGIS schema
```

---

## Phase 2 — File Storage + Authentication

Goal: establish secure file and user foundations.

Tasks:

- Configure Supabase Storage buckets
- Create file metadata relationships in PostgreSQL
- Create minimal Supabase Auth flow
- Add role handling
- Implement JWT verification architecture
- Verify protected access

**Deliverable:**

```text
Login + file storage + protected user flow
```

---

## Phase 3 — Data Ingestion Engine

Goal: make the first real data path work.

Tasks:

- Upload files
- Save files to Supabase Storage
- Detect supported formats
- Read schemas
- Preview records
- Create dataset metadata
- Track processing status
- Map incoming fields to the internal schema

Initial supported formats can include:

- TXT (Mainly TXT will be used as CMLRE provides TXT files for data; these will be converted to CSV or Excel)
- CSV
- Excel
- JSON
- CTD

**Deliverable:**

```text
Upload → Store → Detect → Preview → Register Dataset
```

---

## Phase 4 — Data Quality + Standardisation

Goal: turn raw inputs into reliable research data.

Tasks:

- Missing-value detection
- Duplicate detection
- Coordinate validation
- Timestamp validation
- Range checks
- Outlier detection
- Unit conversion
- Schema validation
- Quality score
- Validation notes
- Provenance recording

Create the standard internal representation for:

```text
time
latitude
longitude
depth
station
sample
species
dataset
source
```

**Deliverable:**

```text
Raw dataset → Validated + standardised dataset
```

---

## Phase 5 — Data Fusion + Unified Marine Data

Goal: implement the core innovation.

Tasks:

- Spatial alignment
- Temporal alignment
- Depth alignment
- Common Marine Data Model
- Cross-domain linking
- Spatial queries through PostGIS
- Unified observation/query views
- Ocean + fisheries + biodiversity integration

**Deliverable:**

```text
Ocean + Fisheries + Biodiversity + eDNA
        ↓
Unified Marine Data
```

This phase is the core differentiator of the platform.

---

## Phase 6 — Scientific Analysis

Goal: create useful scientific outputs before introducing heavy ML.

Tasks:

- Oceanographic trends
- Fisheries trends
- Species distribution
- Biodiversity indicators
- Spatial analysis
- Temporal analysis
- Cross-domain correlation
- Ecosystem relationships

Initial demonstrations:

```text
Temperature ↔ Species
Oxygen ↔ Biodiversity
Fishing Pressure ↔ Diversity
Chlorophyll ↔ Habitat
Ocean Conditions ↔ Catch
```

**Deliverable:**

```text
Unified Data → Scientific Results
```

---

## Phase 7 — Domain-Specific Scientific Modules

Goal: add the specialized marine-science capabilities.

### eDNA

- FASTA/FASTQ validation
- Sequence preprocessing
- Reference matching
- Species detection
- Confidence
- Result storage

### Otolith / Image

- Image upload
- Preprocessing
- Feature extraction
- Classification
- Confidence
- Result storage

### Taxonomy

- Species search
- Taxonomic hierarchy
- Synonym/reference handling
- Species identification support

**Deliverable:**

```text
Specialized scientific evidence
```

---

## Phase 8 — AI / ML Engine

Goal: add genuinely useful predictive intelligence.

Implement in this order:

### Model 1
Environmental anomaly detection

### Model 2
Fish habitat suitability

### Model 3
Catch prediction

### Optional
Image/species classification

For every model:

- Prepare data
- Engineer features
- Train
- Validate
- Evaluate
- Save model
- Register metadata
- Implement inference
- Store predictions

Do not create many weak models.

**Deliverable:**

```text
Scientific Data → ML Prediction / Score
```

---

## Phase 9 — FastAPI Integration

Goal: expose the system cleanly through APIs.

Tasks:

- Dataset APIs
- Upload APIs
- Ocean APIs
- Fisheries APIs
- Species APIs
- eDNA APIs
- Otolith APIs
- Scientific analysis APIs
- ML inference APIs
- Alert APIs
- Report APIs
- Authentication/authorization middleware

**Deliverable:**

```text
Frontend ↔ FastAPI ↔ Services ↔ Supabase/ML
```

---

## Phase 10 — Frontend Research Workspace

Goal: build the real user experience on top of working APIs.

Build in this order:

1. Login
2. Command Center
3. Data Engine
4. Dataset explorer
5. Ocean Explorer
6. Fisheries Explorer
7. Species Explorer
8. eDNA Explorer
9. Scientific Analysis
10. AI Insights
11. Alerts
12. Reports

**Deliverable:**

```text
End-to-end researcher-facing application
```

---

## Phase 11 — Interactive Marine Map

Goal: turn data fusion into a visible feature.

Implement:

- Spatial layers
- Time filter
- Depth filter
- Species filter
- Dataset filter
- Layer toggles
- Point/region details
- AI prediction layers
- Risk zones

**Deliverable:**

```text
Interactive Unified Marine Map
```

---

## Phase 12 — RAG + LLM (Optional)

Goal: add scientific natural-language interaction after the core platform is stable.

Tasks:

- Prepare scientific documents
- Chunk documents
- Generate embeddings
- Populate ChromaDB
- Build retrieval
- Integrate Gemini/Groq
- Build scientific query service
- Connect database results where appropriate
- Generate evidence-backed summaries
- Display source/context information

Example:

```text
Question
  ↓
Query Understanding
  ↓
Database Analysis + Vector Retrieval
  ↓
Relevant Scientific Context
  ↓
LLM
  ↓
Evidence-backed Answer
```

**Deliverable:**

```text
Scientific Q&A / AI research assistant
```

---

## Phase 13 — Alerts + Decision Support (Optional)

Goal: convert analysis/prediction into useful notifications.

Tasks:

- Define thresholds
- Risk scoring
- Environmental alerts
- Biodiversity alerts
- Fisheries alerts
- Species alerts
- Dashboard notification system

**Deliverable:**

```text
AI / Analytics → Alert → Decision Support
```

---

## Phase 14 — Reports + Export

*Note: Reports have been removed from the MVP and will not be implemented.*

---

## Phase 15 — Testing + Hardening

Goal: make the system reliable.

Tasks:

### Backend

- API tests
- Authentication tests
- Database tests
- Validation tests

### Data

- Invalid coordinates
- Bad timestamps
- Missing values
- Duplicates
- Wrong units
- Schema mismatches

### ML

Use task-appropriate metrics:

- MAE
- RMSE
- R²
- Precision
- Recall
- F1
- Confusion matrix

### Frontend

- Login
- Upload
- Maps
- Filters
- Charts
- Role permissions
- Error states

### System

- Logging
- Error handling
- Performance checks
- Security checks

**Deliverable:**

```text
Stable MVP
```

---

## Phase 16 — Docker + Deployment

Docker is intentionally introduced here, not during Phase 0.

Tasks:

- Create `docker/`
- Containerise frontend
- Containerise backend
- Docker Compose
- Environment-based configuration
- Production configuration
- Deploy frontend
- Deploy FastAPI
- Connect Supabase Cloud
- Smoke testing

**Deliverable:**

```text
Reproducible + deployable platform
```

---

# 21. MVP Priority

The project must prioritise a working vertical path over breadth.

## MVP-1

```text
Login
 ↓
Upload CSV
 ↓
Supabase Storage
 ↓
Validation
 ↓
PostgreSQL/PostGIS
 ↓
Display on map
```

## MVP-2

```text
Ocean + Fisheries + Biodiversity
 ↓
Fusion
 ↓
Unified Map
```

## MVP-3

```text
Scientific Analysis
 ↓
AI/ML Prediction
 ↓
Risk/Insight
```

## MVP-4

```text
eDNA + Otolith
```

## MVP-5

```text
RAG + LLM
```

## MVP-6

```text
Alerts + Reports + Deployment
```

A complete working path is more important than ten disconnected features.

---

# 22. Two-Person Team

## Person 1 — Frontend + Integration

Primary:

- React/Vite/Tailwind
- Dashboard
- Maps
- Charts
- Research workspace
- Authentication UI
- API integration
- Final user workflow

## Person 2 — Backend + Data + Scientific/AI

Primary:

- Supabase/PostgreSQL/PostGIS
- Storage
- FastAPI
- Data ingestion
- QC
- Standardisation
- Data fusion
- Scientific analysis
- eDNA/otolith processing
- ML
- RAG backend

## Shared

Both jointly handle:

- Architecture decisions
- API contracts
- Database/data-model decisions
- Testing
- Git integration
- Demo workflow
- Documentation
- Deployment
- Final presentation

---

# 23. AI-Assisted Development Rules

AI coding assistants may be used extensively for:

- Boilerplate
- SQL
- FastAPI scaffolding
- Pydantic models
- React components
- API integration
- Validation functions
- Testing
- Debugging
- Documentation
- ML preprocessing utilities

Human validation is required for:

- Scientific assumptions
- Data-quality rules
- eDNA interpretation
- Taxonomic identification
- ML evaluation
- Model claims
- Scientific conclusions

AI-generated code must be reviewed before merging.

---

# 24. Development Principles

### Build vertically

Prefer:

```text
Upload
→ Validate
→ Standardise
→ Store
→ Analyse
→ Display
```

over building many disconnected components.

### Keep modules replaceable

Scientific algorithms should be isolated from API routing.

### Keep AI decoupled

The core platform must work without the LLM.

### Preserve provenance

Always retain source and processing context.

### Prefer reproducibility

Use:

- Environment variables
- Repeatable scripts
- Documented setup
- Later Dockerisation
- Version control

### Avoid unnecessary infrastructure

Do not introduce another database or platform component unless there is a concrete requirement.

---

# 25. What the Platform Is Not

It is not merely:

- A file uploader
- A database
- A dashboard
- A chatbot
- An image classifier
- An eDNA tool

Its differentiating concept is:

> **Integration → Standardisation → Fusion → Scientific Analysis → AI-assisted Intelligence → Decision Support**

---

# 26. Scientific Trust

AI output is not scientific ground truth.

The platform must emphasize:

- Validated data
- Quality control
- Provenance
- Scientific evidence
- Reproducible analysis
- Evidence-backed AI responses

AI assists researchers; it does not silently replace scientific judgement.

---

# 27. Final Architecture Baseline

```text
Marine Data
    ↓
Data Ingestion
    ↓
Data Quality & Standardisation
    ↓
Data Fusion & Spatial-Temporal Alignment
    ↓
Unified Marine Data
    │
    ├── Oceanographic Analysis
    ├── Fisheries Analysis
    ├── Biodiversity / Taxonomy
    ├── eDNA / Molecular
    └── Otolith / Image
    ↓
Scientific Analysis
    ↓
AI / ML
    ├── Anomaly Detection
    ├── Habitat Suitability
    └── Catch Prediction
    ↓
FastAPI
    ↓
React Research Workspace
    ├── Dashboard
    ├── Marine Map
    ├── Data Engine
    ├── Species Explorer
    ├── eDNA Explorer
    ├── AI Insights
    ├── Alerts
    └── Reports
    ↓
End Users
```

RAG/LLM sits as a later AI-assisted layer connected to the stable platform:

```text
Scientific Data + Analysis
        +
Scientific Documents / Knowledge
        ↓
Semantic Retrieval / ChromaDB
        ↓
Gemini / Groq
        ↓
Evidence-backed Scientific Q&A
```

---

# 28. Definition of Done

The MVP is considered convincing when a user can:

1. Authenticate.
2. Upload a realistic marine dataset.
3. Store the raw file in Supabase Storage.
4. Convert CMLRE TXT files into CSV or Excel files.
5. Register the dataset in PostgreSQL.
6. Validate and standardise the data.
7. Calculate a data-quality result.
8. Store spatial/temporal observations in PostGIS.
9. Combine at least oceanographic + fisheries + biodiversity data.
10. Run meaningful scientific analysis.
11. Visualise the result on a marine map/dashboard.
12. Run at least one meaningful ML model.
13. View a prediction/risk/insight.
14. Demonstrate at least one specialized eDNA or otolith workflow.
15. Trace a result back to its source/provenance.
16. (Optional) Demonstrate RAG/LLM after the core workflow is stable.

The demo must show a **complete end-to-end scientific story**, not isolated features.
