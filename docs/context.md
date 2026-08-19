# CMLRE Marine Data Platform — Project Context

## 1. Project Identity

**Working title:** AI-Driven Unified Data Platform for Oceanographic, Fisheries, and Molecular Biodiversity Insights

**Organisation/context:** CMLRE, Kochi (Centre for Marine Living Resources & Ecology), an attached office under the Ministry of Earth Sciences, Government of India. CMLRE works on mapping, assessment, monitoring and scientific understanding of marine living resources in India's EEZ.

The platform is intended to bring heterogeneous marine datasets and scientific analyses into one unified environment instead of forcing researchers to work with disconnected datasets and specialised tools.

---

## 2. Problem Statement

The core requirement is:

> Develop an AI-driven unified platform that integrates oceanographic, fisheries, and molecular biodiversity datasets into a single intelligent system to support marine research, sustainable fisheries management, biodiversity conservation, and data-driven decision-making through advanced analytics and predictive insights.

The platform is not intended to be merely a dashboard. Its central workflow is:

**heterogeneous marine data → standardisation → unified data → domain-specific analysis → scientific analysis → AI-assisted interpretation → researcher-facing outputs**

---

## 3. Problem Being Solved

Marine scientific information exists in different forms and formats:

- Oceanographic observations
- CTD data
- NetCDF data
- Sensor data
- Fisheries records
- Biodiversity / occurrence records
- Darwin Core data
- Molecular / eDNA sequences
- FASTA files
- Otolith images
- Taxonomic information
- Scientific literature and metadata

These sources differ in format, schema, units, naming conventions, metadata, provenance, spatial representation and temporal representation.

The platform therefore needs a common ingestion and standardisation layer before analysis.

The central value proposition is:

> Convert heterogeneous marine scientific inputs into a unified, queryable and analysable marine data layer, then combine computational analysis with scientific knowledge to generate useful research insights.

---

## 4. Target Users

- Marine Scientists
- Researchers
- Conservationists
- Fisheries Managers
- Decision-makers

The platform is primarily research/science oriented while also supporting conservation, fisheries-management and decision-support use cases.

---

# 5. High-Level Solution

The agreed process flow is:

```text
Marine Data
    ↓
Data Ingestion & Standardisation
    ↓
Unified Marine Data
    ↓
Specialized Analysis
    ↓
Scientific Analysis
    ↓
AI-Assisted Insights
    ↓
Dashboard / Research Workspace
    ↓
End Users
```

Supporting relationships:

```text
Marine Data ─────────────→ AI-Assisted Insights
       Scientific Knowledge

Specialized Analysis ───→ Scientific Analysis
       Scientific Evidence

Scientific Analysis ────→ AI-Assisted Insights
       Scientific Context

Scientific Analysis ────→ Dashboard
       Results / Visualisation

AI-Assisted Insights ───→ Dashboard
       AI Insights

Dashboard ──────────────→ End Users
       Research Insights
```

---

# 6. Two Diagram Levels

Two representations were intentionally developed.

### Detailed Technical Architecture

Contains:

- Frontend container
- Backend container
- Supabase Auth
- Supabase PostgreSQL + PostGIS
- ChromaDB
- External LLM provider
- Scientific analysis modules
- Deployment
- API relationships
- Authentication flow
- Storage and retrieval relationships

This is for explaining **how the software is implemented**.

### Process Flow Architecture

Contains the scientific workflow:

**Marine Data → Ingestion → Unified Data → Analysis → AI Insights → Dashboard → End Users**

This is for the PPT and judges. It intentionally avoids exposing every software component.

The process-flow diagram should remain a **conceptual scientific workflow**, not become another technical architecture diagram.

---

# 7. Marine Data

The process-flow input block is deliberately named simply **Marine Data**.

It represents:

- Oceanography
- Fisheries & Biodiversity
- Taxonomy
- Otoliths
- eDNA
- Research Literature

The detailed architecture further specifies:

- Oceanographic Data — CTD / NetCDF / Sensor Data
- Fisheries & Biodiversity — Darwin Core / Occurrence Records
- Molecular Data — FASTA / eDNA Sequences
- Otolith Data — Otolith Images
- Research Literature — Scientific Documents / Metadata

---

# 8. Data Ingestion & Standardisation

Responsibilities:

- Upload
- Format detection
- Schema mapping
- Cleaning
- Unit standardisation
- Metadata handling
- Validation
- Provenance

Conceptually:

> Convert heterogeneous scientific inputs into a common structure.

The detailed architecture considers formats including:

- CSV
- TSV
- NetCDF
- CTD
- TXT

A specific architecture correction was made:

> The **validate** arrow goes from **Data Ingestion & Standardisation → Data Quality Control**.

---

# 9. Data Quality Control

Responsibilities include:

- Missing-value checks
- Range checks
- Consistency checks
- Quality scoring
- QARTOD-style oceanographic QC concepts

QC happens after ingestion/standardisation and before the data is trusted for downstream analysis.

---

# 10. Unified Marine Data

This represents the integrated marine data layer.

Conceptually it contains:

- Standardised observations
- Species and taxonomy
- Spatial and temporal records
- Otolith / eDNA records
- Metadata
- Provenance

The detailed architecture maps this layer to:

**Supabase PostgreSQL + PostGIS**

PostGIS is used for spatial queries.

---

# 11. Specialized Analysis

Domain-specific scientific processing is performed for:

### Otolith Analysis

Potential processing:

- Image preprocessing
- Shape / morphometric feature extraction
- CNN / ONNX inference
- Species classification
- Confidence score

### eDNA / Molecular Analysis

Potential processing:

- FASTA validation
- Sequence preprocessing
- Barcode / reference matching
- Species detection

### Taxonomy & Species Identification

Potential processing:

- Taxonomic hierarchy
- Species lookup
- Image-based identification where applicable
- Reference metadata

These modules turn standardised/domain-specific data into **scientific evidence** for broader scientific analysis.

---

# 12. Scientific Analysis

The cross-domain analytical stage includes:

- Spatial analysis
- Temporal analysis / trends
- Cross-domain correlation
- Biodiversity indicators
- Species analysis
- Ecosystem relationships
- Ecosystem insights

The intended idea is:

```text
Oceanographic conditions
        +
Fisheries observations
        +
Biodiversity / taxonomy
        +
eDNA evidence
        +
Otolith / species evidence
        ↓
Cross-domain scientific analysis
```

The purpose is to derive meaningful scientific relationships rather than simply display raw records.

---

# 13. AI-Assisted Insights

The AI layer helps researchers interact with analysed data and scientific knowledge.

Planned capabilities:

- Scientific querying
- Knowledge retrieval
- RAG
- Evidence-backed summaries
- AI-generated research insights

Important decision:

> **RAG is part of the current target solution and is not marked optional.**

However, RAG is intentionally implemented **last**.

Reason:

- The core data pipeline must work first.
- Scientific analysis must work first.
- The dashboard must work first.
- RAG can then be connected to stable data and analysis layers.
- If RAG cannot be completed reliably, it can be removed without destroying the core platform.

So the implementation strategy is:

**Core platform → Scientific analysis → Dashboard → RAG/AI enhancement**

---

# 14. RAG / AI Technical Direction

### Vector store

**ChromaDB**

Intended use:

- Scientific literature embeddings
- Marine dataset embeddings
- Semantic retrieval

### LLM provider

External LLM provider represented by:

- Gemini
- Groq

Conceptual flow:

```text
User scientific question
        ↓
Relevant scientific / marine context retrieval
        ↓
Prompt/context construction
        ↓
External LLM
        ↓
Structured / evidence-backed response
        ↓
Research workspace
```

The detailed architecture represented the RAG engine as:

**Semantic Retrieval + ChromaDB + Gemini/Groq + Structured Scientific Summary**

The final provider choice can be made during implementation based on access, cost, latency and reliability.

---

# 15. Research Workspace / Dashboard

The frontend is a single research-facing application.

Planned capabilities include:

### Frontend Dashboard

- Visualisation
- Maps
- Analytics
- AI Results

### Marine Globe / Map

- Species locations
- Bathymetry
- Spatial exploration

### Multi-Parameter Dashboard

- Oceanographic trends
- Fisheries
- Biodiversity
- Cross-domain visualisation

### Study Workbench

- Otolith
- eDNA
- Taxonomy
- Species identification

### Natural Language Query

- Scientific questions
- RAG-powered insights

### Project & Research Workspace

- Projects
- Study notes
- Query history

### Report Export

- Academic PDF reports

---

# 16. Frontend Technology

- React
- Vite
- Tailwind CSS
- Three.js

Three.js is intended for the 3D marine globe/map and related spatial visualisation.

The frontend communicates with the backend through REST/JSON APIs.

---

# 17. Backend Technology

- Python 3.11
- FastAPI
- Modular monolith architecture

Important principle:

> All scientific operations should go through FastAPI rather than the frontend directly accessing internal processing modules.

Conceptual flow:

```text
Frontend
   ↓
FastAPI
   ↓
Scientific/service modules
   ↓
Database / processing
   ↓
Structured response
   ↓
Frontend visualisation
```

---

# 18. Backend Functional Modules

### Data Ingestion & Standardisation

- File upload
- Format detection
- Schema mapping
- Cleaning
- Validation
- Unit standardisation
- Metadata
- Provenance

### Data Quality Control

- Missing values
- Range checks
- Consistency checks
- Quality scoring
- QARTOD-style QC

### Scientific Analytics

- Spatial analysis
- Temporal analysis
- Cross-domain correlation
- Biodiversity indicators
- Ecosystem insights

### FastAPI REST endpoints

The detailed architecture previously represented endpoints along the lines of:

```text
/api/ingest
/api/rag/query
/api/otolith
/api/edna
/api/taxonomy
/api/qc
```

These are the intended functional API areas, not a rigid requirement that every endpoint must retain exactly these names.

---

# 19. Database and Storage

## Supabase

Primary structured data store:

**Supabase PostgreSQL + PostGIS**

Intended contents:

- Marine observations
- CTD / oceanographic records
- Fisheries & biodiversity records
- Taxonomy
- Otolith metadata
- eDNA results
- Projects
- Query history
- Study notes

PostGIS supports spatial queries.

---

# 20. Authentication

The detailed architecture includes:

**Supabase Auth**

with:

- Authenticated session
- JWT
- JWT verification

Conceptually:

```text
Frontend
   ↓
Authenticated session / JWT
   ↓
Supabase Auth
   ↓
JWT verification
   ↓
Backend/API
```

Authentication is part of the technical architecture but is intentionally omitted from the simplified process-flow diagram.

---

# 21. Deployment

Planned deployment concept:

**Docker Compose**

with:

- Frontend container
- Backend container
- Supabase Cloud

Architecture wording:

> Reproducible • Environment-based configuration • Cloud-ready

A diagram correction was made during iteration:

> Do not show a misleading direct **Backend → Supabase** arrow where the intended meaning is deployment. Runtime data access and deployment topology should be represented separately.

---

# 22. Important Architecture Decisions

### Specialized scientific modules

The specialised analysis boxes may visually sit outside the backend container while still being backend functionality.

If asked:

> “Why are these outside the backend container?”

Answer:

> “They are specialised scientific processing modules functionally executed by the backend. They are shown separately to make the scientific workflow readable rather than overcrowding the backend container.”

### RAG

RAG is included in the current solution and implemented last.

### Scientific Analysis → RAG

A direct Scientific Analysis → RAG arrow was removed from the detailed architecture.

The conceptual process-flow relationship is:

**Scientific Analysis → AI-Assisted Insights**, labelled **Scientific Context**.

### Validate

The correct relationship is:

**Data Ingestion & Standardisation → Data Quality Control**

### Simplification

The process-flow diagram should not expose React, FastAPI, Supabase, ChromaDB, JWT, containers or endpoint names unless the slide specifically calls for technical architecture.

---

# 23. Input-to-Output Logic

Complete conceptual pipeline:

```text
1. Marine Data
   ↓
2. Ingestion & Standardisation
   ↓
3. Unified Marine Data
   ↓
4. Domain-Specific / Specialized Analysis
   ↓
5. Scientific Evidence
   ↓
6. Scientific Analysis
   ↓
7. Scientific Context
   ↓
8. AI-Assisted Insights
   ↓
9. AI Insights
   ↓
10. Dashboard / Research Workspace
   ↓
11. Research Insights
   ↓
12. End Users
```

Additional knowledge path:

```text
Marine Data
    ↓
Scientific Knowledge
    ↓
AI-Assisted Insights
```

Visualisation path:

```text
Scientific Analysis
    ↓
Results / Visualisation
    ↓
Dashboard
```

---

# 24. Example End-to-End Scenario

1. A researcher supplies CTD/oceanographic data, fisheries records, eDNA sequences, otolith images, taxonomy or literature.
2. The ingestion layer detects formats and converts heterogeneous inputs into a common structure.
3. Cleaning, unit standardisation, schema mapping, metadata and provenance handling are performed.
4. Data is stored in the unified marine data layer.
5. Relevant specialised modules process eDNA, otolith and taxonomy data.
6. Scientific analysis performs spatial, temporal and cross-domain analysis and derives biodiversity/ecosystem indicators.
7. AI-assisted functionality combines analysed results with scientific knowledge.
8. RAG can retrieve relevant context and generate evidence-backed summaries.
9. Results are presented through maps, dashboards, species information, analytical results, AI insights and reports.
10. Marine scientists and other target users consume the results.

---

# 25. MVP Philosophy

The MVP should demonstrate the complete value chain rather than trying to fully implement every possible scientific capability.

Minimum convincing demonstration:

```text
Realistic marine input
        ↓
Ingestion
        ↓
Standardisation / QC
        ↓
Storage
        ↓
Meaningful scientific analysis
        ↓
Visualisation
        ↓
Research-facing result
```

AI/RAG is an enhancement to this core pipeline and comes after the foundational system works.

Prioritise **working integration** over a large number of partially implemented features.

---

# 26. Implementation Order

## Phase 1 — Foundation

- Repository/project setup
- Frontend/backend structure
- Docker setup
- Environment configuration
- Supabase setup
- Database schema
- Basic authentication
- API skeleton

## Phase 2 — Data Ingestion

- File upload
- Format detection
- Schema mapping
- Cleaning
- Standardisation
- Metadata/provenance
- Data quality checks

## Phase 3 — Unified Marine Data

- PostgreSQL schema
- PostGIS spatial storage
- Ingestion persistence
- Querying
- Sample marine datasets

## Phase 4 — Scientific Processing

Implement the core specialised modules and scientific analytics required for the MVP.

Priority areas:

- Taxonomy/species identification
- eDNA processing
- Otolith analysis
- Spatial/temporal analysis
- Cross-domain/biodiversity analysis

Keep depth realistic for the available implementation time.

## Phase 5 — Frontend Research Workspace

Build:

- Dashboard
- Maps
- Marine-data visualisation
- Scientific-analysis views
- Study/workbench interface
- Result presentation

## Phase 6 — Integration

Connect:

```text
Frontend
   ↕
FastAPI
   ↕
Scientific modules
   ↕
Supabase/PostGIS
```

Verify that the complete data journey works.

## Phase 7 — RAG / AI

Only after the core system is stable:

- Prepare scientific documents/data for retrieval
- Generate embeddings
- Populate ChromaDB
- Implement semantic retrieval
- Integrate Gemini/Groq
- Build scientific query flow
- Produce structured/evidence-backed summaries
- Connect AI results to the dashboard

## Phase 8 — Final Hardening

- Testing
- Error handling
- Performance checks
- UI cleanup
- Deployment
- Demo data
- Presentation workflow
- Documentation

---

# 27. Two-Person Team

The project is being implemented by a **two-person team**.

A practical split is:

## Person 1 — Frontend + Integration

Primary responsibility:

- React/Vite/Tailwind application
- Dashboard
- Maps / Three.js
- Visualisation
- Study workspace
- API integration
- Frontend authentication handling
- Final user workflow

## Person 2 — Backend + Data/Scientific Pipeline

Primary responsibility:

- FastAPI
- Ingestion
- Standardisation
- QC
- Supabase/PostGIS schema
- Scientific processing
- Domain-specific modules
- Analytics
- Later RAG/ChromaDB/LLM integration

## Shared

Both jointly handle:

- Architecture decisions
- API contracts
- Testing
- Git integration
- Demo workflow
- Documentation
- Final presentation

RAG is deliberately delayed so it does not block the core MVP.

---

# 28. Data Model Philosophy

The unified data model should preserve:

- Original source information
- Standardised values
- Units
- Spatial information
- Temporal information
- Taxonomy
- Provenance
- Quality information

Do not discard useful provenance simply because values have been standardised.

The goal is not merely to store a cleaned number; the platform should retain enough context to explain where the information came from and how it was processed.

---

# 29. Scientific Quality and Trust

Because this is a scientific platform, AI output should not be treated as scientific ground truth.

The system therefore emphasises:

- Validated data
- Quality control
- Provenance
- Scientific evidence
- Scientific context
- Evidence-backed summaries

The AI layer assists researchers rather than silently replacing scientific judgement.

---

# 30. Presentation Narrative

Do not begin the solution explanation with:

> “We have React, FastAPI, Supabase, ChromaDB and Gemini.”

The stronger story is:

> “Marine data exists in many heterogeneous forms. We first ingest and standardise it into a unified marine data layer. Domain-specific analyses such as eDNA, otolith and taxonomy processing generate scientific evidence. We then perform cross-domain scientific analysis and present the results through a research workspace. Finally, an AI-assisted layer can combine the analysed data with scientific knowledge to let researchers ask questions and receive evidence-backed insights.”

If judges ask about implementation:

> “The frontend is React/Vite/Tailwind/Three.js, the backend is Python/FastAPI, structured data is stored in Supabase PostgreSQL/PostGIS, and ChromaDB is used for semantic retrieval in the RAG layer, with Gemini/Groq as the external LLM layer and Supabase Auth/JWT for authentication.”

---

# 31. Technology Stack

| Layer | Technology / Choice |
|---|---|
| Frontend | React |
| Build tool | Vite |
| Styling | Tailwind CSS |
| 3D / spatial visualisation | Three.js |
| Backend | Python 3.11 |
| API | FastAPI |
| Backend architecture | Modular monolith |
| Primary database | Supabase PostgreSQL |
| Spatial database | PostGIS |
| Authentication | Supabase Auth / JWT |
| Vector store | ChromaDB |
| LLM | Gemini / Groq |
| Containerisation | Docker |
| Local orchestration | Docker Compose |
| Deployment concept | Supabase Cloud + application containers |

---

# 32. External / Existing Data Integrations Mentioned Earlier

Earlier planning referenced sources such as:

- GBIF
- Wikipedia APIs

These were described as already implemented/functionally available in the prior project context. Treat them as existing/possible integrations rather than automatically requiring every external source to be rebuilt for the MVP.

---

# 33. What the Platform Is NOT

It is not merely:

- A file uploader
- A database
- A dashboard
- A chatbot
- An image classifier
- An eDNA tool

Its differentiating concept is the **integration of these scientific workflows into one unified marine-data platform**.

The important chain is:

> **Integration → Standardisation → Analysis → Cross-domain understanding → AI-assisted interpretation → Decision support**

The technologies support this chain; they are not the product by themselves.

---

# 34. Process-Flow Diagram Baseline

The current conceptual diagram is:

```text
                 ┌──────────────────────────┐
                 │       MARINE DATA        │
                 └────────────┬─────────────┘
                              │ Data Intake
                              ↓
                 ┌──────────────────────────┐
                 │ INGEST & STANDARDISE     │
                 └────────────┬─────────────┘
                              │ Standardised Data
                              ↓
                 ┌──────────────────────────┐
                 │   UNIFIED MARINE DATA    │
                 └───────┬───────────┬──────┘
                         │           │
          Domain-specific Data       │ Marine Data
                         ↓           ↓
                ┌─────────────┐  ┌─────────────────┐
                │ SPECIALIZED │  │   SCIENTIFIC    │
                │   ANALYSIS  │→ │    ANALYSIS     │
                └─────────────┘  └────────┬────────┘
                                          │
                                  Scientific Context
                                          ↓
                               ┌─────────────────────┐
Scientific Knowledge ────────→ │ AI-ASSISTED         │
                               │ INSIGHTS             │
                               │ Scientific Querying  │
                               │ Knowledge Retrieval  │
                               │ RAG                  │
                               │ Evidence-backed      │
                               │ Summaries            │
                               └──────────┬──────────┘
                                          │ AI Insights
                                          ↓
                               ┌─────────────────────┐
                               │      DASHBOARD      │
                               └──────────┬──────────┘
                                          │ Research Insights
                                          ↓
                               ┌─────────────────────┐
                               │      END USERS      │
                               └─────────────────────┘

Scientific Analysis ─────────→ Dashboard
        Results / Visualisation
```

The actual PPT diagram may route arrows differently for space/readability, but the semantics should remain the same.

---

# 35. Detailed Architecture Baseline

The detailed architecture previously contained:

### Inputs

- Oceanographic Data — CTD / NetCDF / Sensor Data
- Fisheries & Biodiversity — Darwin Core / Occurrence Records
- Molecular Data — FASTA / eDNA Sequences
- Otolith Data — Otolith Images
- Research Literature — Scientific Documents / Metadata

### Frontend

React + Vite + Tailwind CSS + Three.js

Modules:

- Frontend Dashboard
- Marine Globe / Map
- Multi-Parameter Dashboard
- Study Workbench
- Natural Language Query
- Project & Research Workspace
- Report Export

### Backend

Python 3.11 + FastAPI + Modular Monolith

Modules:

- Data Ingestion & Standardisation
- Data Quality Control
- Scientific Analytics
- FastAPI REST Endpoints
- RAG & AI Query Engine

### Scientific Analysis

- eDNA / Molecular Analysis
- Otolith Analysis
- Taxonomy & Species Identification

### Data

Supabase PostgreSQL + PostGIS

### AI / retrieval

ChromaDB + external LLM provider

### Authentication

Supabase Auth / JWT

### Deployment

Docker Compose + frontend container + backend container + Supabase Cloud

---

# 36. Development Principles

### Build vertically

Whenever possible, make one complete scientific path work end-to-end before implementing many isolated features.

Example:

```text
Upload
→ Validate
→ Standardise
→ Store
→ Analyse
→ Display
```

is more valuable for the MVP than ten disconnected screens.

### Keep modules replaceable

Specialised scientific algorithms should be isolated from the API layer so they can be improved without redesigning the entire system.

### Keep the AI layer decoupled

The core application must not depend on the LLM being available for basic ingestion, storage, analysis or visualisation.

### Preserve provenance

Scientific users need to understand the origin and quality of data.

### Prefer reproducibility

Use:

- Docker
- Environment-based configuration
- Documented setup
- Repeatable data-processing steps

---

# 37. Definition of a Convincing MVP

A convincing MVP should allow the team to demonstrate:

1. A marine dataset can be supplied.
2. The system recognises/handles the input.
3. Data is cleaned/standardised.
4. Data quality is checked.
5. Data is stored in the unified marine data layer.
6. Scientific analysis can be run.
7. Results are visualised.
8. A researcher can interact with the result.
9. Specialised analyses demonstrate the marine-science focus.
10. AI/RAG can be demonstrated after the core workflow is stable.

The demo should show a **complete story**, not isolated features.

---

# 38. RAG Implementation Rule

Explicit project decision:

> **RAG is included in the target solution and should be implemented, but it comes last.**

Do not mark it optional in the current architecture.

The sequence is:

```text
Core platform
    ↓
Data + scientific analysis
    ↓
Dashboard
    ↓
RAG / AI enhancement
```

If RAG works, it strengthens the final system.

If RAG cannot be completed reliably, the team can remove that layer while retaining the core marine-data platform.

---

# 39. Team Mental Model

Every team member should understand the project at three levels.

### Level 1 — One sentence

> A unified marine-data platform that standardises heterogeneous marine datasets, performs cross-domain scientific analysis, and provides AI-assisted research insights.

### Level 2 — Process

> Data → Standardise → Unify → Specialised Analysis → Scientific Analysis → AI Insights → Dashboard → Researchers.

### Level 3 — Implementation

> React/Vite/Tailwind/Three.js → FastAPI/Python → scientific services → Supabase PostgreSQL/PostGIS, with ChromaDB + Gemini/Groq for the RAG layer and Supabase Auth/JWT for authentication.

---

# 40. Final Working Baseline

Unless the team deliberately changes the architecture during implementation, use this as the baseline:

```text
INPUTS
Marine Data
    │
    ▼
INGESTION
Data Ingestion & Standardisation
    │
    ▼
UNIFIED DATA
Supabase PostgreSQL + PostGIS
    │
    ├──────────────► Specialized Analysis
    │                 ├── Otolith
    │                 ├── eDNA / Molecular
    │                 └── Taxonomy
    │
    ▼
SCIENTIFIC ANALYSIS
Spatial / Temporal / Cross-domain /
Biodiversity / Species / Ecosystem
    │
    ├──────────────► Dashboard
    │                  Results / Visualisation
    │
    ▼
AI-ASSISTED INSIGHTS
Scientific Querying / Knowledge Retrieval /
RAG / Evidence-backed Summaries
    │
    ▼
RESEARCH WORKSPACE / DASHBOARD
    │
    ▼
END USERS
```

Supporting knowledge:

```text
Marine Data
     │
     └──── Scientific Knowledge ────► AI-Assisted Insights
```

RAG infrastructure:

```text
AI-Assisted Insights
       │
       ▼
   ChromaDB
       │
   semantic retrieval
       │
       ▼
 Gemini / Groq
```

Application infrastructure:

```text
React + Vite + Tailwind + Three.js
                │
                ▼
       Python + FastAPI
                │
        ┌───────┴────────┐
        ▼                ▼
Scientific Services   Supabase
                      PostgreSQL
                      + PostGIS

Supabase Auth / JWT
```

Deployment:

```text
Docker Compose
├── Frontend Container
├── Backend Container
└── Supabase Cloud
```

This is the working project context to use when implementing the MVP and preparing the final presentation.
