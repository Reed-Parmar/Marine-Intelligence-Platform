# Phase 6 — Scientific Analysis Architecture & Reference

## 1. Overview & Purpose

**Phase 6 — Scientific Analysis** turns the unified marine observations produced by Phase 5 (`data_pipeline.fusion`) into deterministic, reproducible, and explainable scientific outputs.

```text
Phase 3: Ingestion (CMLRE TXT/CSV/Excel/JSON)
        ↓
Phase 4: Quality & Standardisation (QARTOD, Units, Provenance)
        ↓
Phase 5: Data Fusion (Unified Observation Layer & 3D Spatial-Temporal-Depth Matching)
        ↓
PHASE 6: SCIENTIFIC ANALYSIS (Descriptive & Inferential Marine Intelligence)
        ↓
Scientific Insights & Dashboard Visualizations
        ↓
Future Phase 8: AI / ML Engine (Predictive Intelligence)
```

> [!IMPORTANT]
> **Scientific Integrity Notice**: Phase 6 strictly computes deterministic mathematical and statistical metrics. All cross-domain correlations and ecosystem relationship syntheses explicitly label findings as empirical associations, never asserting ungrounded biological or physical causation.

---

## 2. Architecture & Module Structure

The `data_pipeline/analysis/` package is structured into focused, domain-aligned scientific modules:

```text
data_pipeline/analysis/
├── __init__.py           # Package exports
├── models.py             # Typed dataclasses (OceanTrendResult, BiodiversityResult, etc.)
├── ocean.py              # Oceanographic physical & chemical trend analysis
├── fisheries.py          # Fisheries catch allocations and landing trends
├── biodiversity.py      # Species distribution, richness, Shannon, Simpson & Pielou indices
├── spatial.py            # Spatial grid cell binning & multi-domain regional comparison
├── temporal.py           # Multi-scale time-series & northern Indian Ocean seasonal dynamics
├── correlation.py        # Cross-domain Pearson & Spearman correlation with 3D pairing
├── ecosystem.py          # Multi-domain ecosystem relationship synthesis
└── service.py            # ScientificAnalysisService main orchestrator facade
```

---

## 3. Supported Analyses & Scientific Formulas

### Analysis 1 — Oceanographic Trends (`data_pipeline/analysis/ocean.py`)
Computes time-aggregated statistics (mean, min, max, standard deviation, linear regression slope) for physical/chemical ocean variables:
- `temperature` (°C)
- `salinity` (PSU)
- `dissolved_oxygen` (mg/L)
- `chlorophyll` (mg/m³)
- `ph` (pH)
- `turbidity` (NTU)
- `pressure` (dbar)

**Rate of Change (Linear Slope)**:
$$\text{Slope } \beta = \frac{\sum (t_i - \bar{t})(y_i - \bar{y})}{\sum (t_i - \bar{t})^2}$$

---

### Analysis 2 — Fisheries Trends (`data_pipeline/analysis/fisheries.py`)
Analyzes commercial and scientific landing volumes:
- Total catch (kg), average catch per record, min/max catch
- Taxonomic breakdown by target species
- Spatial allocation by fishing zone and gear type
- Time-series progression across days/months/years

> [!NOTE]
> Catch data represents harvested landing weights and is distinctly categorized from active fishing effort (e.g. vessel days, trawl hours).

---

### Analysis 3 — Species Distribution (`data_pipeline/analysis/biodiversity.py`)
Maps taxonomic occurrences across horizontal and vertical space:
- Species spatial centroids: $(\bar{\text{lat}}, \bar{\text{lon}})$
- Bathymetric vertical bounds: $[\text{depth}_{\min}, \text{depth}_{\max}]$
- Location-aware occurrence points formatted for map overlays
- Bounding-box coverage

---

### Analysis 4 — Biodiversity Indicators (`data_pipeline/analysis/biodiversity.py`)
Computes classical ecological community indices from species occurrence frequencies $n_i$ and total abundance $N = \sum n_i$:

1. **Species Richness ($S$)**: Total count of unique taxa.
2. **Relative Abundance ($p_i$)**: $p_i = \frac{n_i}{N}$
3. **Shannon-Wiener Diversity Index ($H'$)**:
   $$H' = -\sum_{i=1}^S p_i \ln(p_i)$$
4. **Gini-Simpson Diversity Index ($1 - D$)**:
   $$1 - D = 1 - \sum_{i=1}^S p_i^2$$
5. **Pielou's Species Evenness ($J'$)**:
   $$J' = \frac{H'}{\ln(S)} \quad (\text{for } S > 1)$$

---

### Analysis 5 — Spatial Analysis & Grid Binning (`data_pipeline/analysis/spatial.py`)
Performs spatial aggregation using Phase 5 geodesic Haversine distance and bounding boxes:
- Bounding box filtering `[west, south, east, north]`
- Radial point filtering `(center_lat, center_lon, radius_km)`
- Regular spatial grid binning (e.g. $0.5^\circ$ or $1.0^\circ$ cells) reporting observation counts, species richness, dominant domains, and variable means per cell.

---

### Analysis 6 — Temporal Dynamics & Seasons (`data_pipeline/analysis/temporal.py`)
Aggregates time series across multi-temporal scales:
- `daily` (`%Y-%m-%d`), `monthly` (`%Y-%m`), `yearly` (`%Y`)
- **Northern Indian Ocean Seasonal Regimes**:
  - **Pre-Monsoon**: March – May
  - **SW-Monsoon**: June – September
  - **Post-Monsoon**: October – November
  - **Winter**: December – February

---

### Analysis 7 — Cross-Domain Correlation (`data_pipeline/analysis/correlation.py`)
Pairs observations across domains within a configurable 3D space-time neighborhood ($\Delta s \le 50\text{ km}, \Delta t \le 72\text{ h}, \Delta z \le 50\text{ m}$) and computes:

1. **Pearson Linear Correlation ($r$)**:
   $$r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$$
2. **Spearman Rank Correlation ($\rho$)**:
   $$\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$
   *(Note: The simplified formula above assumes no tied ranks. When tied ranks occur, the calculation applies fractional rank averaging followed by the tie-corrected Pearson correlation of the ranked data: $\rho = r(\text{rank}(x), \text{rank}(y))$.)*
3. **Two-Tailed Significance ($p$-value)**:
   Computed using the two-tailed Student's $t$-distribution survival function across $n - 2$ degrees of freedom. Statistical significance is evaluated against the hypothesis decision threshold $\alpha = 0.05$.

---

### Analysis 8 — Ecosystem Relationships Synthesis (`data_pipeline/analysis/ecosystem.py`)
Integrates physical, chemical, biological, and fisheries dimensions into comprehensive synthesis reports:
- `temperature_species`: Temperature ↔ Species Abundance
- `oxygen_biodiversity`: Dissolved Oxygen ↔ Biological Occurrence Abundance
- `chlorophyll_habitat`: Chlorophyll-a ↔ Occurrence Abundance
- `fishing_diversity`: Fishing Pressure ↔ Species Abundance
- `ocean_catch`: Ocean Conditions ↔ Fisheries Catch

---

## 4. Example Usage

```python
from data_pipeline.analysis import ScientificAnalysisService
from data_pipeline.fusion.models import UnifiedQueryParams

# 1. Oceanographic Trends
ocean_trend = ScientificAnalysisService.analyze_ocean_trends(
    variable="temperature",
    time_aggregation="monthly"
)
print(f"Overall Mean Temp: {ocean_trend.overall_mean}°C | Trend: {ocean_trend.trend_direction}")

# 2. Biodiversity Indicators
bio_metrics = ScientificAnalysisService.calculate_biodiversity()
print(f"Richness: {bio_metrics.species_richness} | Shannon H': {bio_metrics.shannon_index}")

# 3. Cross-Domain Correlation
correlation = ScientificAnalysisService.calculate_correlation(
    domain_x="oceanography",
    variable_x="temperature",
    domain_y="biodiversity",
    variable_y="individual_count",
    method="pearson"
)
print(f"Correlation r: {correlation.correlation_coefficient} | Interpretation: {correlation.interpretation}")

# 4. Ecosystem Synthesis
ecosystem_report = ScientificAnalysisService.analyze_ecosystem_relationship(
    theme_key="temperature_species"
)
print(f"Theme: {ecosystem_report.theme}")
print(f"Narrative: {ecosystem_report.summary_narrative}")
```

---

## 5. Integration with Future Phases

- **Phase 8 (AI / ML Engine)**: Consumes structured `TrendDataPoint`, `SpatialGridCell`, and `CorrelationResult` features to train environmental anomaly detection, habitat suitability, and catch prediction models.
- **Phase 9 (FastAPI Backend)**: Exposes endpoints (`/api/v1/analysis/...`) returning JSON-serialized `.to_dict()` outputs from typed Phase 6 models.
- **Phase 10 (Frontend Workspace)**: Powers interactive time-series charts, spatial heatmaps, biodiversity dials, and cross-domain correlation scatterplots in the command center.
