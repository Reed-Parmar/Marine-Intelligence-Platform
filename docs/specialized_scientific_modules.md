# Phase 7 — Domain-Specific Scientific Modules Architecture & Reference

## 1. Overview & Purpose

**Phase 7 — Domain-Specific Scientific Modules** provides specialized marine-science analytical pipelines for:
1. **eDNA (Environmental DNA)**: Sequence validation (FASTA/FASTQ), deterministic preprocessing, reference matching, species detection, and confidence scoring.
2. **Otolith / Marine Image Analysis**: Image validation, preprocessing, morphological feature extraction, and ML-ready classification abstractions.
3. **Taxonomy**: Multi-criteria search, 7-rank Linnaean hierarchy retrieval, synonym mapping, and taxon resolution.

```text
Phase 3: Ingestion (CMLRE TXT/CSV/Excel/FASTA/Images)
        ↓
Phase 4: Quality & Standardisation
        ↓
Phase 5: Data Fusion
        ↓
Phase 6: Scientific Analysis (Trends, Biodiversity, Spatial/Temporal)
        ↓
PHASE 7: DOMAIN-SPECIFIC SCIENTIFIC MODULES (eDNA, Otoliths, Taxonomy)
        ↓
Future Phase 8: AI / ML Engine (BLAST, CNN Otolith Models, Neural Embeddings)
```

> [!IMPORTANT]
> **Scientific Integrity & Non-ML Baseline Notice**:
> Phase 7 establishes clean, modular pipelines and Protocol interfaces (`ReferenceMatcher`, `ImageFeatureExtractor`, `OtolithClassifier`). The baseline implementations in Phase 7 are deterministic, rule-based heuristics designed for rapid testing and demonstrations. All outputs clearly declare `is_ml_prediction=False` and report `confidence_method="deterministic_baseline"`, ensuring Phase 8 teammates can drop in trained deep learning models without modifying the public APIs.

---

## 2. Architecture & Folder Structure

The `data_pipeline/specialized_science/` package is structured into decoupled domain modules:

```text
data_pipeline/specialized_science/
├── __init__.py               # Top-level package exports
├── common/
│   ├── __init__.py
│   ├── models.py             # EvidenceType, IdentificationStatus, ScientificEvidence, SpecializedResult, StorageRepository
│   └── result.py             # Result builders and formatting utilities
├── edna/
│   ├── __init__.py
│   ├── validation.py         # Multi-line FASTA and 4-line FASTQ validators
│   ├── preprocessing.py      # Base cleanup, GC content, ambiguous base filtering, Phred trimming
│   ├── matching.py           # ReferenceMatcher protocol, ExactMatcher, KmerSimilarityMatcher
│   ├── detection.py          # Species detection and transparent baseline confidence scoring
│   └── service.py            # EDNAService orchestrator with storage boundary
├── otolith/
│   ├── __init__.py
│   ├── preprocessing.py      # Image format validation, dimension checks, PIL/NumPy normalization
│   ├── features.py           # ImageFeatureExtractor protocol and BaselineMorphologicalFeatureExtractor
│   ├── classification.py     # OtolithClassifier protocol and BaselineOtolithClassifier
│   └── service.py            # OtolithAnalysisService orchestrator with storage boundary
└── taxonomy/
    ├── __init__.py
    ├── hierarchy.py          # TaxonomicRank enum, TaxonHierarchy (Kingdom -> Species), TaxonRecord
    ├── search.py             # Exact, common-name, and partial substring search engine
    ├── synonyms.py           # SynonymResolver for mapping deprecated/junior synonyms
    └── service.py            # TaxonomyService with curated northern Indian Ocean reference fauna
```

---

## 3. Module Workflows

### 3.1 eDNA Pipeline (`data_pipeline/specialized_science/edna/`)

```text
Raw FASTA / FASTQ / String
        ↓
1. Validation (Structure, IUPAC Nucleotides, FASTQ Phred Qualities)
        ↓
2. Preprocessing (Uppercase, Gap Stripping, GC Ratio, End-Trimming)
        ↓
3. Reference Matching (Exact Substring / K-mer Containment Similarity)
        ↓
4. Species Detection & Baseline Confidence Scoring
        ↓
5. Taxonomy Resolution (Canonical Scientific Name & Lineage)
        ↓
6. Storage Repository Persistence -> SpecializedResult
```

#### Deterministic Baseline Confidence Formula:
$$\text{Confidence} = \text{SimilarityScore} \times \min\left(1.0, \max\left(0.85, \frac{\text{Length}}{150\text{ bp}}\right)\right) \times \text{SeparationMarginBonus}$$

- **`CONFIRMED`**: Confidence $\ge 0.85$ (Exact match / high k-mer identity).
- **`PROVISIONAL`**: Confidence $\ge 0.70$ (Subfragment match).
- **`FLAGGED`**: Ambiguity detected when top 2 candidates have $< 0.01$ similarity margin.
- **`UNRESOLVED`**: Matches below confidence threshold or no candidate found.

---

### 3.2 Otolith / Image Analysis Pipeline (`data_pipeline/specialized_science/otolith/`)

```text
Image Input (Path / Bytes / PIL Image)
        ↓
1. Validation (Format PNG/JPEG/TIFF, Readability, Dimensions >= 32x32)
        ↓
2. Preprocessing (Luminance Conversion, 224x224 Resize, Float [0.0, 1.0] Array)
        ↓
3. Morphological Feature Extraction (Aspect Ratio, Intensity Moments, Gradients, Entropy)
        ↓
4. Classification (Baseline Heuristic or Phase 8 CNN Model)
        ↓
5. Taxonomy Resolution (Common Name & Family Hierarchy)
        ↓
6. Storage Repository Persistence -> SpecializedResult
```

#### Extracted Morphological Features:
- **Geometry**: `aspect_ratio`, `orig_width`, `orig_height`, `circularity_estimate`
- **Intensity Moments**: `mean_intensity`, `std_intensity`, `min_intensity`, `max_intensity`, `median_intensity`, `contrast_ratio`
- **Gradients & Texture**: `gradient_h_energy`, `gradient_v_energy`, `gradient_magnitude_mean`, `entropy`

---

### 3.3 Taxonomy Service (`data_pipeline/specialized_science/taxonomy/`)

Maintains an indexed catalog of marine flora and fauna:
- **7-Rank Lineage**: Kingdom $\rightarrow$ Phylum $\rightarrow$ Class $\rightarrow$ Order $\rightarrow$ Family $\rightarrow$ Genus $\rightarrow$ Species.
- **Search Modes**:
  - `exact`: Exact case-insensitive scientific name match.
  - `common`: Common vernacular name lookup (e.g. *"Indian Mackerel"*, *"Giant Tiger Prawn"*).
  - `partial`: Substring containment matching.
  - `auto`: Unified search checking exact $\rightarrow$ common $\rightarrow$ synonym $\rightarrow$ partial.
- **Synonym Resolution**: Automatically maps junior/deprecated names (e.g. *Scomber kanagurta* $\rightarrow$ *Rastrelliger kanagurta*) to accepted canonical names.

---

## 4. Phase 8 AI / ML Extension Points

Phase 7 provides explicit Protocols allowing Phase 8 machine learning models to be injected without touching core service code:

| Extension Point | Protocol Interface | Phase 7 Baseline | Phase 8 AI/ML Replacement |
| :--- | :--- | :--- | :--- |
| **eDNA Matcher** | `ReferenceMatcher` | `KmerSimilarityMatcher` | NCBI BLAST+ / Neural Sequence Embeddings |
| **Image Features** | `ImageFeatureExtractor` | `BaselineMorphologicalFeatureExtractor` | ResNet50 / ViT Deep Embeddings |
| **Otolith Classifier**| `OtolithClassifier` | `BaselineOtolithClassifier` | PyTorch / ONNX Trained CNN Model |
| **Persistence** | `StorageRepository` | `InMemoryStorageRepository` | PostgreSQL / Supabase Vector Storage |

### Example: Plugging a Phase 8 CNN Model into Phase 7:

```python
from data_pipeline.specialized_science import OtolithAnalysisService, OtolithFeatureVector, OtolithClassificationResult

# 1. Teammate creates Phase 8 PyTorch / ONNX model implementing OtolithClassifier Protocol
class TrainedOtolithCNN:
    def classify(self, feature_vector: OtolithFeatureVector) -> OtolithClassificationResult:
        # Run CNN inference...
        return OtolithClassificationResult(
            predicted_species="Thunnus albacares",
            predicted_age_years=4,
            confidence_score=0.97,
            is_ml_model=True,
            classifier_name="otolith_resnet50_v2",
        )

# 2. Inject into Phase 7 Service
service = OtolithAnalysisService(classifier=TrainedOtolithCNN())
result = service.analyze_image("path/to/otolith.jpg")

print(f"Species: {result.target_entity} | ML Prediction: {result.is_ml_prediction}")
```

---

## 5. Example Code Usages

### eDNA Analysis:
```python
from data_pipeline.specialized_science import EDNAService

service = EDNAService()

# Analyze a raw nucleotide sequence
seq = "CCAATCTATCATATGACTTCTGTGCGTCAGACCGGCATGGAAGGGCACCGCCCTGAGCCT..."
result = service.analyze_sequence(seq, seq_id="sample_01")

print(f"Target: {result.target_entity} ({result.common_name})")
print(f"Status: {result.status} | Confidence: {result.confidence_score} ({result.confidence_level})")
print(f"Lineage: {result.taxonomic_hierarchy}")
```

### Otolith Image Analysis:
```python
from data_pipeline.specialized_science import OtolithAnalysisService

service = OtolithAnalysisService()
result = service.analyze_image("sample_otolith.png")

print(f"Predicted Species: {result.target_entity}")
print(f"Features: {result.evidence.features}")
```

### Taxonomy Search & Resolution:
```python
from data_pipeline.specialized_science import TaxonomyService

tax = TaxonomyService()

# Resolve synonym
res = tax.resolve_taxon("Scomber kanagurta")
print(f"Accepted: {res.scientific_name} | Is Synonym: {res.is_synonym}")

# Full hierarchy
hier = tax.get_hierarchy("Thunnus albacares")
print(f"Family: {hier.family} | Genus: {hier.genus}")
```

---

## 6. Limitations & Boundaries

1. **Deterministic Heuristics**: Baseline matchers and classifiers use algorithmic string distance and morphological bounds. High-confidence biological identification in production requires validated reference libraries and trained Phase 8 deep learning models.
2. **Quality Scores**: FASTQ quality score parsing supports standard Phred+33 ASCII encoding.
3. **No External APIs Required**: All components operate completely offline with zero external network or GPU dependencies.
