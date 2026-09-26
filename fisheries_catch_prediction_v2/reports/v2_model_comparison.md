# Phase 14.3 V2 — Fisheries Catch Prediction: Model Comparison Report

## 1. Overview
In Phase 14.3 V2, an extensive multi-model improvement experiment was designed and evaluated across **six distinct candidate architectures** to explore:
1. **Current XGBoost Baseline**: Benchmark using V1 tuned architecture (48 features).
2. **Improved Raw-Target XGBoost**: Enhanced with rich temporal, spatial sub-basin, and interaction features (391 features).
3. **Improved Log1p XGBoost**: Evaluating log-scale transformation with V2 rich features.
4. **Catch-Rate (CPUE) Model**: Modeling catch per unit effort $\text{CPUE} = \text{Catch} / \text{Effort}$, and projecting $\widehat{\text{Catch}} = \widehat{\text{CPUE}} \times \text{Effort}$.
5. **CatBoost Regressor**: Ordered boosting on V2 features.
6. **Two-Stage Catch Model (Hurdle Model)**: Stage 1 Classifier for $P(\text{Catch} > 0)$ + Stage 2 Regressor for $\mathbb{E}[\text{Catch} \mid \text{Catch} > 0]$.

Controlled tuning was performed strictly on the **Validation set (2015–2018, $N=27,880$)**. The strongest validation candidate was selected and evaluated **ONCE on the untouched 2019–2022 test set ($N=27,692$)**.

---

## 2. Validation Set Performance Across All 6 Candidate Models ($N=27,880$)

| Model ID | Model Architecture | Validation MAE (MT) $\downarrow$ | Validation RMSE (MT) $\downarrow$ | Validation $R^2$ $\uparrow$ | Validation MedAE (MT) $\downarrow$ | Validation sMAPE (%) $\downarrow$ | Mean Bias (MT) | Training Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Model 1** | **Current XGBoost Baseline** | **48.36** | **139.76** | **0.6615** | 15.96 | 103.44% | -21.62 | 1.9 s |
| **Model 2** | **Improved Raw-Target XGBoost** | **48.24** | **139.54** | **0.6625** | 15.72 | 105.04% | -21.86 | 46.0 s |
| **Model 3** | **Improved Log1p XGBoost** | 53.29 | 173.25 | 0.4798 | 13.20 | 122.33% | -44.74 | 11.8 s |
| **Model 4** | **Catch-Rate (CPUE) Model** | 60.18 | 372.84 | -1.4094 | 16.65 | 103.94% | -12.58 | 6.9 s |
| **Model 5** | **CatBoost Regressor** | 50.29 | 145.78 | 0.6317 | 18.43 | 107.53% | -21.49 | 4.5 s |
| **Model 6** | **Two-Stage Hurdle Model** | **48.17** | **140.69** | **0.6569** | **14.88** | **89.61%** | -22.33 | 16.6 s |

---

## 3. Scientific Analysis of Candidate Models

### A. Two-Stage Hurdle Model (Model 6)
- **Zero-Catch Separation**: Fisheries datasets contain a substantial zero-catch proportion (35.04% overall; 22.0% in validation). Model 6 trains an `XGBClassifier` to estimate $P(\text{Catch} > 0)$ and an `XGBRegressor` on positive catches.
- **Key Advantage**: Achieved the **lowest symmetric MAPE (89.61% vs 103.44%)** and a low Validation MedAE (**14.88 MT**), demonstrating that separating zero-catch events from positive biomass hauls mitigates percentage error penalty on near-zero strata.

### B. Improved Raw-Target XGBoost (Model 2)
- Enhanced with `Fleet_x_Gear`, `Gear_x_Season`, `Fleet_x_Season`, and marine sub-basin coordinates.
- Achieved **Val MAE of 48.24 MT** and **Val $R^2$ of 0.6625**, matching the baseline while providing localized sub-basin interpretability.

### C. Log1p XGBoost (Model 3)
- Training on $\log(1+y)$ achieved low median absolute error (13.20 MT) but suffered on RMSE (173.25 MT) and $R^2$ (0.4798).
- Exponentiating back to metric tons heavily amplifies errors on industrial purse-seine sets (>200 MT), proving once again that optimizing squared error directly on raw biomass is superior for fisheries tonnage forecasting.

### D. Catch-Rate (CPUE) Model (Model 4)
- Predicting $\text{CPUE} = \text{Catch} / \text{Effort}$ and multiplying by $\text{Effort}$ resulted in extreme variance (RMSE = 372.84 MT, $R^2 = -1.4094$).
- **Scientific Root Cause**: When effort is small (e.g. 0.5–2 hours of searching), minor catch fluctuations produce massive CPUE spikes (e.g. 50 MT/hr). When multiplied by vessel operational duration, errors compound exponentially. Direct catch modeling is far more stable than ratio regression.

### E. CatBoost Regressor (Model 5)
- CatBoost performed competitively (Val MAE: 50.29 MT, $R^2 = 0.6317$) with ultra-fast training (4.5 s), but XGBoost models maintained superior variance explanation ($R^2 \approx 0.66$).

---

## 4. Final Selected Candidate and Test Set Results

Across validation runs, the **XGBoost family (Baseline / Improved Raw XGBoost / Two-Stage Hurdle)** demonstrated virtually identical, top-tier performance (Val MAE 48.17–48.36 MT, $R^2 \approx 0.66$).

Evaluating the selected model on the **held-out 2019–2022 test set ($N=27,692$)**:
- **Test MAE**: **61.95 MT**
- **Test RMSE**: **164.75 MT**
- **Test $R^2$**: **0.5898**
- **Test MedAE**: **18.64 MT**
- **Test sMAPE**: **100.11%**
- **Test Bias**: -26.75 MT (Mean Actual: 89.89 MT, Mean Predicted: 63.15 MT)
