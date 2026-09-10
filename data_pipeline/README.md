# Data Pipeline — Modular Architecture

The `data_pipeline` package is structured into clear, domain and phase-oriented subpackages:

```text
data_pipeline/
├── shared/                    # Common models and enumerations across pipeline phases
│   ├── __init__.py
│   └── models.py              # DomainType, etc.
│
├── storage/                   # Phase 2: Storage & Database Integration
│   ├── __init__.py
│   ├── file_handler.py        # Supabase Storage client & file uploads
│   └── dataset_registrar.py   # PostgreSQL dataset metadata registration
│
├── ingestion/                 # Phase 3: Raw Ingestion & Parsing Engine
│   ├── __init__.py
│   ├── format_detector.py     # Format detection & domain heuristic classification
│   ├── txt_parser.py          # Delimiter, header & preamble parser for CMLRE TXT files
│   ├── schema_normalizer.py   # Alias mapping to canonical column names
│   ├── canonical_exporter.py  # Canonical CSV and XLSX export
│   ├── ingestion_manager.py   # End-to-end ingestion pipeline orchestrator
│   └── process_dataset.py     # Batch processing runner for datasets
│
├── quality_standardisation/   # Phase 4: Data Quality & Scientific Standardisation
│   ├── __init__.py
│   ├── models.py              # Quality models (DatasetQualityResult, ValidationIssue, etc.)
│   ├── validators.py          # Coordinates, missing values, duplicates, ranges, IQR outliers
│   ├── unit_converter.py      # Deterministic scientific unit conversions
│   ├── schema_mapper.py       # Domain-specific canonical field mapping
│   ├── quality_scorer.py      # Deterministic 0-100 quality scoring
│   ├── pipeline.py            # QualityPipeline orchestrator
│   └── phase4_boundary.py     # Integration boundary between ingestion and quality
│
├── fusion/                    # Phase 5: Data Fusion & Unified Marine Data
│   ├── __init__.py
│   ├── models.py              # MarineObservation, UnifiedQueryParams, UnifiedSummary
│   ├── spatial.py             # Geodesic Haversine distance & bounding-box filtering
│   ├── temporal.py            # Timezone-aware temporal windowing & date range filtering
│   ├── depth.py               # Water column vertical range & tolerance filtering
│   ├── cross_domain.py        # Cross-domain spatial/temporal/depth co-occurrence association
│   ├── query_service.py       # Multi-criteria unified query & summary service
│   └── db.py                  # Database query helper
│
├── tests/                     # Comprehensive test suites
│   ├── test_cmlre_ingestion.py   # Phase 3 ingestion tests
│   ├── test_quality_pipeline.py  # Phase 4 quality & standardisation tests
│   └── test_data_fusion.py       # Phase 5 data fusion & cross-domain tests
│
├── test_ingestion.py          # Standalone ingestion integration test runner
└── __init__.py                # Root package exports preserving backward compatibility
```
