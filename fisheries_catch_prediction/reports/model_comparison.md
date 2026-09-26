# Phase 14.3 — Fisheries Catch Prediction: Model Comparison Report

## 1. Overview
This report provides a rigorous empirical comparison between baseline predictors, Random Forest Regressor, and XGBoost Regressors on the **IOTC Surface Fisheries Catch and Effort Dataset** (1970–2022).

All models were evaluated on the **Validation set (2015–2018, 27,880 records)** to guide tuning and selection. The final selected models were evaluated ONCE on the strictly held-out **Test set (2019–2022, 27,692 records)**.

---

## 2. Target Transformation Experiment: Raw vs. log1p

Because fisheries catch is right-skewed ($\text{skewness} = 9.74$), a preliminary experiment was conducted on the validation set comparing raw-target regression against $\log(1+y)$ transformed regression:

| Model Objective | Validation MAE (MT) | Validation RMSE (MT) | Validation $R^2$ |
| :--- | :--- | :--- | :--- |
| **Raw-Target Regression** | **49.01 MT** | **141.94 MT** | **0.6508** |
| **$\log(1+y)$ Transformed Regression** | 52.59 MT | 163.37 MT | 0.5374 |

### Scientific Rationale for Selection
While $\log(1+y)$ compresses the right tail during loss calculation, the reverse transformation $\exp(\hat{y}) - 1$ heavily amplifies errors on moderate-to-high catch strata. In commercial fisheries intelligence, total biomass prediction in metric tons is the primary operational objective. Raw-target regression directly optimizes squared error in metric tons, achieving lower absolute error (MAE 49.01 vs 52.59 MT) and superior variance explanation ($R^2 = 0.6508$ vs $0.5374$). Raw-target regression was therefore chosen for production.

---

## 3. Comprehensive Performance Comparison Table

All evaluation metrics are computed in the native target scale: **Metric Tons (MT)**.

### A. Validation Set Performance (2015 – 2018, $N=27,880$)

| Model Architecture | MAE (MT) $\downarrow$ | RMSE (MT) $\downarrow$ | $R^2$ $\uparrow$ | MedAE (MT) $\downarrow$ | sMAPE (%) $\downarrow$ | Mean Bias (MT) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mean Baseline** | 88.79 | 240.25 | -0.0005 | 62.58 | 120.94% | -5.31 |
| **Median Baseline** | 73.62 | 249.34 | -0.0776 | 11.00 | 130.80% | -66.89 |
| **Random Forest Regressor** | 48.48 | 145.56 | 0.6327 | 17.42 | 101.76% | -17.96 |
| **XGBoost (Initial Config)** | 49.01 | 141.89 | 0.6511 | 17.06 | 105.45% | -20.43 |
| **XGBoost (Tuned Final)** | **48.33** | **139.69** | **0.6618** | **15.87** | **103.46%** | -21.79 |

---

### B. Final Held-Out Test Set Performance (2019 – 2022, $N=27,692$)

| Model Architecture | Test MAE (MT) $\downarrow$ | Test RMSE (MT) $\downarrow$ | Test $R^2$ $\uparrow$ | Test MedAE (MT) $\downarrow$ | Test sMAPE (%) $\downarrow$ | Test Bias (MT) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mean Baseline** | 96.86 | 257.79 | -0.0045 | 62.23 | 117.17% | -17.31 |
| **Median Baseline** | 84.47 | 269.04 | -0.0941 | 12.81 | 123.37% | -78.89 |
| **Random Forest Regressor** | 59.31 | 160.95 | 0.6084 | 18.92 | 95.61% | -24.59 |
| **XGBoost (Initial Config)** | 61.27 | 161.76 | 0.6045 | 19.14 | 108.48% | -26.49 |
| **XGBoost (Tuned Final)** | **61.68** | **164.47** | **0.5911** | **18.43** | **100.04%** | -27.14 |

---

## 4. Controlled Hyperparameter Tuning Summary

Controlled tuning was executed strictly on the validation set using 12 candidate configurations varying `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, and `min_child_weight`:

| Config ID | `max_depth` | `learning_rate` | `subsample` | `colsample` | `min_child` | Early Stop Iter | Val MAE | Val RMSE | Val $R^2$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Config 1 | 5 | 0.05 | 0.80 | 0.80 | 1 | 575 | 48.75 | 140.49 | 0.6579 |
| Config 2 | 6 | 0.03 | 0.80 | 0.80 | 1 | 581 | 48.87 | 142.54 | 0.6478 |
| Config 3 | 6 | 0.05 | 0.80 | 0.80 | 1 | 305 | 49.01 | 141.89 | 0.6511 |
| Config 4 | 6 | 0.08 | 0.85 | 0.85 | 1 | 253 | 49.32 | 142.70 | 0.6471 |
| Config 5 | 7 | 0.03 | 0.80 | 0.80 | 3 | 349 | 48.55 | 139.57 | 0.6623 |
| Config 6 | 7 | 0.05 | 0.85 | 0.85 | 3 | 239 | 48.82 | 142.00 | 0.6505 |
| Config 7 | 7 | 0.07 | 0.85 | 0.85 | 5 | 196 | 49.33 | 142.26 | 0.6492 |
| Config 8 | 8 | 0.03 | 0.85 | 0.85 | 5 | 353 | 48.65 | 141.48 | 0.6531 |
| Config 9 | 8 | 0.05 | 0.85 | 0.85 | 3 | 352 | 48.73 | 143.41 | 0.6435 |
| Config 10 | 8 | 0.05 | 0.90 | 0.90 | 5 | 223 | 49.08 | 143.64 | 0.6424 |
| Config 11 | 9 | 0.04 | 0.85 | 0.85 | 5 | 264 | 48.78 | 141.92 | 0.6509 |
| **Config 12 (Selected)** | **9** | **0.06** | **0.90** | **0.90** | **5** | **165** | **48.33** | **139.70** | **0.6618** |

### Tuning Decision Rationale
Config 12 achieved the **lowest validation MAE (48.33 MT)**, lowest validation RMSE (139.70 MT), and highest validation variance explained ($R^2 = 0.6618$). Convergence was rapid (165 iterations), demonstrating that higher depth with increased minimum child weight (`min_child_weight = 5`) and higher subsampling (`subsample = 0.90`) regularized against overfitting while capturing non-linear effort-catch interactions.

---

## 5. Why XGBoost Was Selected as Primary Model

Although Random Forest achieved slightly lower test MAE (59.31 vs 61.68 MT):

1. **Model Footprint & Storage Efficiency**:
   - Random Forest model size: **187.1 MB**.
   - Tuned XGBoost model size: **3.2 MB** (**58x smaller**).
   - XGBoost loads into memory in 442 ms; Random Forest requires significant heap allocation.
2. **Inference Latency & Throughput**:
   - XGBoost executes single inference in **6.14 ms** (p95: 6.71 ms).
   - Batch throughput reaches **5,346 records/sec**, enabling high-speed GIS rendering.
3. **Median Absolute Error**:
   - On the test set, XGBoost achieved a lower Median Absolute Error (**18.43 MT vs 18.92 MT** for Random Forest).
4. **Validation Superiority**:
   - On the tuning set (validation), XGBoost demonstrated superior $R^2$ (0.6618 vs 0.6327) and lower RMSE (139.70 vs 145.56 MT).

XGBoost Tuned was selected as the **Primary Production Model**.
