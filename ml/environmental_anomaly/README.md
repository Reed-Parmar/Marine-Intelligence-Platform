# Environmental Anomaly Detection ML Pipeline

**Phase 14.1 — CMLRE Marine Intelligence Platform**  
*Centre for Marine Living Resources & Ecology (CMLRE), Ministry of Earth Sciences, Government of India*

---

## 1. Overview & Objective

The **Environmental Anomaly Detection** module detects extreme, unusual, and hazardous oceanographic conditions—such as **Marine Heatwaves (MHW)**, **thermal anomalies**, and **cold upwelling surges**—from satellite and in-situ observations.

Because physical marine anomalies lack universal ground-truth labels, this module implements an unsupervised machine learning architecture based on **Isolation Forest** combined with an **empirical spatial-temporal SST baseline**.

---

## 2. Scientific Conceptual Flow

```text
Raw NetCDF4 / HDF5 / CSV
        ↓
Dynamic Loader & Inspector (h5py, streaming, no full-RAM load)
        ↓
Quality Filtering & Preprocessing (Kelvin→Celsius, fill values, land mask)
        ↓
Spatial-Temporal SST Climatology Baseline (Spatial-monthly grid)
        ↓
SST Anomaly Calculation (T_obs - T_baseline)
        ↓
Cyclic Feature Engineering (sin/cos month and day-of-year)
        ↓
Isolation Forest Anomaly Model
        ↓
Calibrated Severity Scoring (0-100 scale: Low, Moderate, High, Critical)
        ↓
Unsupervised Evaluation (Distributions, persistence, physical alignment)
        ↓
API-Ready Inference Engine (FastAPI & Dashboard Integration)
```

---

## 3. Study Region: Strict IHO S-23 Arabian Sea Demarcation

The study domain is strictly bounded to the **Arabian Sea** in accordance with **International Hydrographic Organization (IHO) Publication S-23 (*Limits of Oceans and Seas*, Section 38)**:

```text
                          25°N  Cape Jiwani (61.74°E, 25.02°N)
                                 / \
         Gulf of Oman           /   \  PAKISTAN
             \                 /     \
              \               /       \
  Ras al Hadd (59.80°E, 22.53°N)       \   INDIA
  (Oman)                                \  (Western Shelf)
                                         \
                                          \
  Ras Fartak (52.23°E, 15.63°N)            \
      \                                     \
       \  Gulf of Aden                       \
        \                                     \
  Ras Asir (51.28°E, 11.83°N)                  \  Lakshadweep
  (Somalia)                                     \  Sea
                                                 \
                           5°N ------------------- 78°E (Kanyakumari / S. India)
                               50°E
```

### Demarcation Rules & Sub-basin Exclusions

1. **Persian Gulf Excluded**:
   - Boundary: Waters west of the Strait of Hormuz ($\text{Longitude} \le 56.5^\circ\text{E}$ and $\text{Latitude} \ge 23.5^\circ\text{N}$).
   - Rationale: Ultra-shallow, hyper-saline ($>40\text{ PSU}$) basin with extreme seasonal SST swings ($18.6^\circ\text{C}$ to $36.3^\circ\text{C}$, $\sigma = 5.15^\circ\text{C}$ vs Arabian Sea $\sigma = 1.71^\circ\text{C}$). Unmasked inclusion skews baselines and produces false-positive anomalies.
   - Excluded cells: **433 cells/day** ($0.73\%$ of ocean pixels).

2. **Gulf of Oman Excluded**:
   - Boundary: Northwest of the geodesic line connecting **Ras al Hadd, Oman** ($59.80^\circ\text{E}, 22.53^\circ\text{N}$) to **Cape Jiwani, Pakistan** ($61.74^\circ\text{E}, 25.02^\circ\text{N}$).
   - Excluded cells: **1,069 cells/day** ($1.80\%$ of ocean pixels).

3. **Gulf of Aden Excluded**:
   - Boundary: West of the geodesic line connecting **Ras Asir, Somalia** ($51.28^\circ\text{E}, 11.83^\circ\text{N}$) to **Ras Fartak, Yemen** ($52.23^\circ\text{E}, 15.63^\circ\text{N}$).
   - Excluded cells: **1,188 cells/day** ($2.00\%$ of ocean pixels).

4. **Retained Arabian Sea Core**:
   - Bounded by the coastlines of Pakistan and Western India, extending south to $5.00^\circ\text{N}$ and east to $78.00^\circ\text{E}$ (including the Lakshadweep Sea and western Indian continental shelf).
   - Retained cells: **56,747 cells/day** (**95.47%** of valid ocean pixels).
   - 731-day observation count (full grid): **41,482,057 observations**.
   - 731-day observation count (stride=2, $\approx 18.5\text{ km}$): **10,405,054 observations**.

---

## 4. Supported Input Variables

The dynamic loader automatically maps incoming datasets with canonical aliases:

| Variable | Aliases | Description |
| :--- | :--- | :--- |
| `analysed_sst` | `analysed_sst`, `sst`, `thetao`, `temperature` | Sea Surface Temperature (Celsius or auto-converted Kelvin) |
| `latitude` | `lat`, `latitude`, `nav_lat` | Geographic latitude ([-90.0, 90.0]) |
| `longitude` | `lon`, `longitude`, `nav_lon` | Geographic longitude (normalized to [-180.0, 180.0]) |
| `time` | `time`, `timestamp`, `date` | Epoch days/seconds or ISO-8601 timestamps |
| `analysis_error` | `analysis_error`, `sst_error`, `uncertainty` | Measurement/interpolation uncertainty |
| `sea_ice_fraction` | `sea_ice_fraction`, `ice_fraction` | Ice concentration (included only if variance > 0) |
| `mask` | `mask`, `land_mask` | Surface flags (e.g. 1=sea, 2=land) |

---

## 4. SST Baseline & Scientific Limitations

### The Baseline Calculation
$$\text{SST Anomaly} = T_{\text{observed}} - T_{\text{baseline}}(\text{location}, \text{month})$$

1. **Level 1 (Cell Baseline)**: 1° $\times$ 1° discrete spatial grid cell monthly mean $\bar{T}(\text{cell}, \text{month})$.
2. **Level 2 (Latitudinal Band Fallback)**: 5° regional latitudinal band monthly mean $\bar{T}(\text{band}, \text{month})$.
3. **Level 3 (Global Monthly Fallback)**: Study-area overall monthly mean $\bar{T}(\text{month})$.

> [!NOTE]
> **Scientific Limitation**: Multi-decadal (30-year) climatology is not assumed when only 1–2 years of observational data are available. The baseline represents an empirical seasonal-spatial proxy calculated over the available observation period.

---

## 5. Model Architecture & Severity Scoring

* **Algorithm**: Unsupervised `sklearn.ensemble.IsolationForest`
* **Features**: `sst_anomaly`, `analysed_sst`, `latitude`, `longitude`, `month_sin`, `month_cos`, optional `analysis_error`
* **Score Normalization**:
  Raw decision scores are inverted and mapped to a $[0, 100]$ scale where **higher = more anomalous**:
  * **Low** ($< 60$): Conditions within expected seasonal variations.
  * **Moderate** ($60 \le \text{Score} < 75$): Noticeable thermal perturbation.
  * **High** ($75 \le \text{Score} < 85$): Significant anomaly ($\ge +1.5^\circ\text{C}$ or $\le -1.5^\circ\text{C}$).
  * **Critical** ($\ge 85$): Severe Marine Heatwave or extreme upwelling surge.

---

## 6. Development vs. Production Protocol

* **Development Validation**: When the full compressed real dataset is not yet provided, the test suite uses a small synthetic NetCDF fixture generated by `generate_synthetic_environmental_netcdf()` strictly to verify the loader, preprocessing, baseline, training, serialization, and inference pipeline.
* **Production Training**: Once the user provides the complete original dataset:
  1. Inspect the file with `data_loader.inspect_dataset(filepath)` to report actual dimensions, dates, and variables.
  2. Train using `EnvironmentalAnomalyTrainer().fit_predict(...)`.
  3. Export model artifacts to `models/environmental_anomaly/`.
  4. Generate diagnostic outputs to `results/environmental_anomaly/`.
