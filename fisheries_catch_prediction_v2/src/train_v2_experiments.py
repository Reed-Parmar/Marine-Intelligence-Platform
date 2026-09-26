"""
V2 Improvement Experiment Suite for Fisheries Catch Prediction (Phase 14.3 V2).
Builds, tunes, and compares 6 distinct model architectures on the Validation set:
1. Current XGBoost Baseline (V1 Architecture benchmark)
2. Improved Raw-Target XGBoost (with rich V2 temporal, spatial, interaction features)
3. Improved Log1p XGBoost (log1p target transformation)
4. Catch-Rate Model (CPUE = Catch / Effort modeling)
5. CatBoost Regressor (ordered boosting on V2 features)
6. Two-Stage Catch Model (Hurdle model: Stage 1 Classifier + Stage 2 Positive Regressor)

Selects the strongest validation candidate, then evaluates ONCE on the held-out 2019-2022 test set.
"""
import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostRegressor
import xgboost as xgb

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from fisheries_catch_prediction.src.pipeline import (
    ALL_INPUT_FEATURES as V1_INPUT_FEATURES,
    engineer_features as engineer_features_v1,
    build_preprocessor as build_preprocessor_v1
)
from fisheries_catch_prediction_v2.src.features_v2 import (
    ALL_FEATURES_V2,
    ALL_CATEGORICAL_V2,
    NUMERICAL_V2,
    engineer_features_v2
)
from fisheries_catch_prediction_v2.src.pipeline_v2 import (
    build_preprocessor_v2,
    calculate_metrics
)


def run_v2_experiment(base_dir: str = "fisheries_catch_prediction_v2"):
    print("=" * 75)
    print("STARTING FISHERIES CATCH PREDICTION V2 IMPROVEMENT EXPERIMENTS")
    print("=" * 75)

    splits_dir = os.path.join(base_dir, "data", "splits")
    models_dir = os.path.join(base_dir, "models")
    reports_dir = os.path.join(base_dir, "reports")
    figures_dir = os.path.join(reports_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    # 1. Load Data Splits
    print("\n[Step 1] Loading identical chronological data splits...")
    df_train = pd.read_csv(os.path.join(splits_dir, "train.csv"))
    df_val = pd.read_csv(os.path.join(splits_dir, "val.csv"))
    df_test = pd.read_csv(os.path.join(splits_dir, "test.csv"))

    print(f"Train set: {len(df_train)} rows (1970-2014, { (df_train['TotalCatchMT'] == 0).mean()*100:.1f}% zeros)")
    print(f"Val set:   {len(df_val)} rows (2015-2018, { (df_val['TotalCatchMT'] == 0).mean()*100:.1f}% zeros)")
    print(f"Test set:  {len(df_test)} rows (2019-2022, { (df_test['TotalCatchMT'] == 0).mean()*100:.1f}% zeros)")

    y_train = df_train["TotalCatchMT"].values.astype(np.float64)
    y_val = df_val["TotalCatchMT"].values.astype(np.float64)
    y_test = df_test["TotalCatchMT"].values.astype(np.float64)

    # 2. V1 Features Setup (For Model 1 Baseline Benchmark)
    print("\n[Step 2] Preparing V1 Baseline Features...")
    df_train_v1 = engineer_features_v1(df_train)
    df_val_v1 = engineer_features_v1(df_val)
    df_test_v1 = engineer_features_v1(df_test)

    pre_v1 = build_preprocessor_v1()
    X_train_v1 = pre_v1.fit_transform(df_train_v1[V1_INPUT_FEATURES])
    X_val_v1 = pre_v1.transform(df_val_v1[V1_INPUT_FEATURES])
    X_test_v1 = pre_v1.transform(df_test_v1[V1_INPUT_FEATURES])

    # 3. V2 Features Setup (For Models 2 - 6)
    print("\n[Step 3] Engineering Rich V2 Features (Temporal, Spatial, Sub-basin, Interactions)...")
    df_train_v2 = engineer_features_v2(df_train)
    df_val_v2 = engineer_features_v2(df_val)
    df_test_v2 = engineer_features_v2(df_test)

    pre_v2 = build_preprocessor_v2()
    X_train_v2 = pre_v2.fit_transform(df_train_v2[ALL_FEATURES_V2])
    X_val_v2 = pre_v2.transform(df_val_v2[ALL_FEATURES_V2])
    X_test_v2 = pre_v2.transform(df_test_v2[ALL_FEATURES_V2])
    print(f"V2 Transformed Features: {X_train_v2.shape[1]} columns")

    validation_summary = {}

    # =========================================================================
    # MODEL 1: Current XGBoost Baseline (V1 Benchmark)
    # =========================================================================
    print("\n" + "=" * 50)
    print("[MODEL 1] Current XGBoost Baseline (V1 Benchmark)")
    print("=" * 50)
    t0 = time.time()
    m1 = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=175,
        learning_rate=0.06,
        max_depth=9,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=5,
        random_state=42,
        n_jobs=-1
    )
    m1._estimator_type = "regressor"
    m1.fit(X_train_v1, y_train, eval_set=[(X_val_v1, y_val)], verbose=False)
    m1_val_pred = np.clip(m1.predict(X_val_v1), 0, None)
    m1_val_metrics = calculate_metrics(y_val, m1_val_pred)
    m1_val_metrics["train_time_sec"] = round(time.time() - t0, 2)
    validation_summary["1_Current_XGBoost_Baseline"] = m1_val_metrics
    print(f"Val MAE: {m1_val_metrics['MAE']:.3f} MT, RMSE: {m1_val_metrics['RMSE']:.3f} MT, R2: {m1_val_metrics['R2']:.4f}")
    joblib.dump(m1, os.path.join(models_dir, "model1_v1_baseline", "model1_v1_baseline.joblib"))

    # =========================================================================
    # MODEL 2: Improved Raw-Target XGBoost (V2 Features + Tuning)
    # =========================================================================
    print("\n" + "=" * 50)
    print("[MODEL 2] Improved Raw-Target XGBoost (V2 Features + Controlled Tuning)")
    print("=" * 50)
    # Controlled tuning on validation set
    m2_configs = [
        {"max_depth": 7, "learning_rate": 0.05, "subsample": 0.85, "min_child_weight": 4},
        {"max_depth": 8, "learning_rate": 0.06, "subsample": 0.90, "min_child_weight": 5},
        {"max_depth": 9, "learning_rate": 0.05, "subsample": 0.90, "min_child_weight": 5},
        {"max_depth": 10, "learning_rate": 0.05, "subsample": 0.90, "min_child_weight": 6}
    ]
    best_m2_cfg = None
    best_m2_mae = float("inf")
    best_m2_model = None

    t0_m2 = time.time()
    for cfg in m2_configs:
        m2_cand = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=400,
            learning_rate=cfg["learning_rate"],
            max_depth=cfg["max_depth"],
            subsample=cfg["subsample"],
            colsample_bytree=0.85,
            min_child_weight=cfg["min_child_weight"],
            random_state=42,
            n_jobs=-1,
            early_stopping_rounds=30
        )
        m2_cand._estimator_type = "regressor"
        m2_cand.fit(X_train_v2, y_train, eval_set=[(X_val_v2, y_val)], verbose=False)
        cand_pred = np.clip(m2_cand.predict(X_val_v2), 0, None)
        cand_mae = float(np.mean(np.abs(cand_pred - y_val)))
        print(f"  Cfg depth={cfg['max_depth']}, lr={cfg['learning_rate']}, child={cfg['min_child_weight']} | iter={m2_cand.best_iteration:3d} -> Val MAE: {cand_mae:.3f} MT")
        if cand_mae < best_m2_mae:
            best_m2_mae = cand_mae
            best_m2_cfg = cfg
            best_m2_model = m2_cand

    m2_val_pred = np.clip(best_m2_model.predict(X_val_v2), 0, None)
    m2_val_metrics = calculate_metrics(y_val, m2_val_pred)
    m2_val_metrics["train_time_sec"] = round(time.time() - t0_m2, 2)
    m2_val_metrics["best_config"] = best_m2_cfg
    validation_summary["2_Improved_Raw_XGBoost"] = m2_val_metrics
    print(f"Selected Model 2 -> Val MAE: {m2_val_metrics['MAE']:.3f} MT, RMSE: {m2_val_metrics['RMSE']:.3f} MT, R2: {m2_val_metrics['R2']:.4f}")
    joblib.dump(best_m2_model, os.path.join(models_dir, "model2_improved_raw_xgb", "model2_improved_raw_xgb.joblib"))

    # =========================================================================
    # MODEL 3: Improved Log1p XGBoost
    # =========================================================================
    print("\n" + "=" * 50)
    print("[MODEL 3] Improved Log1p XGBoost (V2 Features)")
    print("=" * 50)
    t0_m3 = time.time()
    y_train_log = np.log1p(y_train)
    y_val_log = np.log1p(y_val)

    m3 = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=400,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.9,
        colsample_bytree=0.85,
        min_child_weight=5,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30
    )
    m3._estimator_type = "regressor"
    m3.fit(X_train_v2, y_train_log, eval_set=[(X_val_v2, y_val_log)], verbose=False)
    m3_val_pred = np.clip(np.expm1(m3.predict(X_val_v2)), 0, None)
    m3_val_metrics = calculate_metrics(y_val, m3_val_pred)
    m3_val_metrics["train_time_sec"] = round(time.time() - t0_m3, 2)
    validation_summary["3_Improved_Log1p_XGBoost"] = m3_val_metrics
    print(f"Val MAE: {m3_val_metrics['MAE']:.3f} MT, RMSE: {m3_val_metrics['RMSE']:.3f} MT, R2: {m3_val_metrics['R2']:.4f}")
    joblib.dump(m3, os.path.join(models_dir, "model3_improved_log1p_xgb", "model3_improved_log1p_xgb.joblib"))

    # =========================================================================
    # MODEL 4: Catch-Rate Model (CPUE = Catch / Effort)
    # =========================================================================
    print("\n" + "=" * 50)
    print("[MODEL 4] Catch-Rate Model (CPUE = TotalCatchMT / Effort)")
    print("=" * 50)
    t0_m4 = time.time()
    # Safe effort division
    train_effort = np.maximum(df_train_v2["Effort"].values, 0.1)
    val_effort = np.maximum(df_val_v2["Effort"].values, 0.1)
    y_train_cpue = y_train / train_effort
    y_val_cpue = y_val / val_effort

    m4 = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=400,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=5,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30
    )
    m4._estimator_type = "regressor"
    m4.fit(X_train_v2, y_train_cpue, eval_set=[(X_val_v2, y_val_cpue)], verbose=False)
    m4_val_cpue_pred = np.clip(m4.predict(X_val_v2), 0, None)
    m4_val_pred = np.clip(m4_val_cpue_pred * val_effort, 0, None)
    m4_val_metrics = calculate_metrics(y_val, m4_val_pred)
    m4_val_metrics["train_time_sec"] = round(time.time() - t0_m4, 2)
    validation_summary["4_Catch_Rate_CPUE_Model"] = m4_val_metrics
    print(f"Val MAE: {m4_val_metrics['MAE']:.3f} MT, RMSE: {m4_val_metrics['RMSE']:.3f} MT, R2: {m4_val_metrics['R2']:.4f}")
    joblib.dump(m4, os.path.join(models_dir, "model4_catch_rate_cpue", "model4_catch_rate_cpue.joblib"))

    # =========================================================================
    # MODEL 5: CatBoost Regressor
    # =========================================================================
    print("\n" + "=" * 50)
    print("[MODEL 5] CatBoost Regressor (V2 Transformed Features)")
    print("=" * 50)
    t0_m5 = time.time()
    m5 = CatBoostRegressor(
        iterations=400,
        depth=7,
        learning_rate=0.06,
        loss_function="RMSE",
        random_seed=42,
        thread_count=-1,
        early_stopping_rounds=30,
        verbose=False
    )
    m5.fit(X_train_v2, y_train, eval_set=(X_val_v2, y_val), verbose=False)
    m5_val_pred = np.clip(m5.predict(X_val_v2), 0, None)
    m5_val_metrics = calculate_metrics(y_val, m5_val_pred)
    m5_val_metrics["train_time_sec"] = round(time.time() - t0_m5, 2)
    validation_summary["5_CatBoost_Regressor"] = m5_val_metrics
    print(f"Val MAE: {m5_val_metrics['MAE']:.3f} MT, RMSE: {m5_val_metrics['RMSE']:.3f} MT, R2: {m5_val_metrics['R2']:.4f}")
    m5.save_model(os.path.join(models_dir, "model5_catboost", "model5_catboost.cbm"))
    joblib.dump(m5, os.path.join(models_dir, "model5_catboost", "model5_catboost.joblib"))

    # =========================================================================
    # MODEL 6: Two-Stage Catch Model (Hurdle: Stage 1 Classifier + Stage 2 Regressor)
    # =========================================================================
    print("\n" + "=" * 50)
    print("[MODEL 6] Two-Stage Catch Model (Hurdle: Stage 1 Classifier + Stage 2 Regressor)")
    print("=" * 50)
    t0_m6 = time.time()
    # Stage 1: Occurrence Classification
    y_train_occ = (y_train > 0.0).astype(int)
    y_val_occ = (y_val > 0.0).astype(int)

    clf_stage1 = xgb.XGBClassifier(
        objective="binary:logistic",
        n_estimators=300,
        learning_rate=0.06,
        max_depth=6,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30
    )
    clf_stage1.fit(X_train_v2, y_train_occ, eval_set=[(X_val_v2, y_val_occ)], verbose=False)
    p_occ_val = clf_stage1.predict_proba(X_val_v2)[:, 1]

    # Stage 2: Positive Catch Regression (Trained strictly on positive records)
    pos_mask_train = (y_train > 0.0)
    X_train_v2_pos = X_train_v2[pos_mask_train]
    y_train_pos = y_train[pos_mask_train]

    pos_mask_val = (y_val > 0.0)
    X_val_v2_pos = X_val_v2[pos_mask_val]
    y_val_pos = y_val[pos_mask_val]

    reg_stage2 = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=400,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=4,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30
    )
    reg_stage2._estimator_type = "regressor"
    reg_stage2.fit(X_train_v2_pos, y_train_pos, eval_set=[(X_val_v2_pos, y_val_pos)], verbose=False)
    mu_pos_val = np.clip(reg_stage2.predict(X_val_v2), 0, None)

    # Strategy A: Continuous Expected Value: E[Y] = P(Y > 0) * E[Y | Y > 0]
    pred_expected_val = p_occ_val * mu_pos_val

    # Strategy B: Hurdle Thresholding (Find optimal tau on validation set)
    best_tau = 0.5
    best_hurdle_mae = float("inf")
    best_hurdle_pred = None

    for tau in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
        pred_tau = np.where(p_occ_val >= tau, mu_pos_val, 0.0)
        tau_mae = float(np.mean(np.abs(pred_tau - y_val)))
        if tau_mae < best_hurdle_mae:
            best_hurdle_mae = tau_mae
            best_tau = tau
            best_hurdle_pred = pred_tau

    # Compare Continuous Expected vs Optimal Hurdle
    mae_expected = float(np.mean(np.abs(pred_expected_val - y_val)))
    if best_hurdle_mae < mae_expected:
        m6_val_pred = best_hurdle_pred
        hurdle_type = f"Thresholded (tau={best_tau})"
    else:
        m6_val_pred = pred_expected_val
        hurdle_type = "Continuous Expected Value (P * Mu)"

    m6_val_metrics = calculate_metrics(y_val, m6_val_pred)
    m6_val_metrics["train_time_sec"] = round(time.time() - t0_m6, 2)
    m6_val_metrics["hurdle_strategy"] = hurdle_type
    m6_val_metrics["best_tau"] = best_tau
    validation_summary["6_Two_Stage_Hurdle_Model"] = m6_val_metrics
    print(f"Val MAE: {m6_val_metrics['MAE']:.3f} MT, RMSE: {m6_val_metrics['RMSE']:.3f} MT, R2: {m6_val_metrics['R2']:.4f} ({hurdle_type})")

    # Persist stage 1 & 2
    joblib.dump(clf_stage1, os.path.join(models_dir, "model6_two_stage_hurdle", "stage1_classifier.joblib"))
    joblib.dump(reg_stage2, os.path.join(models_dir, "model6_two_stage_hurdle", "stage2_regressor.joblib"))

    # =========================================================================
    # VALIDATION CANDIDATE SELECTION
    # =========================================================================
    print("\n" + "=" * 75)
    print("VALIDATION PERFORMANCE COMPARISON ACROSS ALL 6 CANDIDATES")
    print("=" * 75)
    print(f"{'Model Name':30s} | {'Val MAE':10s} | {'Val RMSE':10s} | {'Val R2':8s} | {'Val MedAE':10s} | {'Time (s)':8s}")
    print("-" * 88)

    winning_model_name = None
    winning_val_mae = float("inf")

    for name, met in validation_summary.items():
        print(f"{name:30s} | {met['MAE']:10.3f} | {met['RMSE']:10.3f} | {met['R2']:8.4f} | {met['MedAE']:10.3f} | {met.get('train_time_sec', 0):8.1f}")
        if met["MAE"] < winning_val_mae:
            winning_val_mae = met["MAE"]
            winning_model_name = name

    print("-" * 88)
    print(f"STRONGEST VALIDATION CANDIDATE SELECTED: {winning_model_name} (Val MAE = {winning_val_mae:.3f} MT)")

    with open(os.path.join(reports_dir, "v2_validation_comparison.json"), "w") as f:
        json.dump(validation_summary, f, indent=2)

    # =========================================================================
    # FINAL EVALUATION ON STRICTLY UNTOUCHED TEST SET (2019-2022)
    # =========================================================================
    print("\n" + "=" * 75)
    print(f"EVALUATING WINNING MODEL ({winning_model_name}) ONCE ON UNTOUCHED 2019-2022 TEST SET")
    print("=" * 75)

    if "2_Improved_Raw_XGBoost" in winning_model_name:
        final_test_pred = np.clip(best_m2_model.predict(X_test_v2), 0, None)
        selected_model_obj = best_m2_model
    elif "5_CatBoost_Regressor" in winning_model_name:
        final_test_pred = np.clip(m5.predict(X_test_v2), 0, None)
        selected_model_obj = m5
    elif "6_Two_Stage" in winning_model_name:
        p_occ_test = clf_stage1.predict_proba(X_test_v2)[:, 1]
        mu_pos_test = np.clip(reg_stage2.predict(X_test_v2), 0, None)
        if "Thresholded" in m6_val_metrics["hurdle_strategy"]:
            final_test_pred = np.where(p_occ_test >= m6_val_metrics["best_tau"], mu_pos_test, 0.0)
        else:
            final_test_pred = p_occ_test * mu_pos_test
        selected_model_obj = {"stage1": clf_stage1, "stage2": reg_stage2, "strategy": m6_val_metrics["hurdle_strategy"]}
    elif "4_Catch_Rate" in winning_model_name:
        test_effort = np.maximum(df_test_v2["Effort"].values, 0.1)
        final_test_pred = np.clip(m4.predict(X_test_v2) * test_effort, 0, None)
        selected_model_obj = m4
    elif "3_Improved_Log1p" in winning_model_name:
        final_test_pred = np.clip(np.expm1(m3.predict(X_test_v2)), 0, None)
        selected_model_obj = m3
    else:
        final_test_pred = np.clip(m1.predict(X_test_v1), 0, None)
        selected_model_obj = m1

    final_test_metrics = calculate_metrics(y_test, final_test_pred)

    print("\nFINAL TEST METRICS (2019-2022):")
    for k, v in final_test_metrics.items():
        print(f"  {k:22s}: {v:.4f}" if isinstance(v, float) else f"  {k:22s}: {v}")

    # =========================================================================
    # DETAILED STRATIFIED TEST ERROR ANALYSIS
    # =========================================================================
    print("\n[Step 4] Performing Stratified Error Breakdown on Held-Out Test Set...")
    df_eval = df_test_v2.copy()
    df_eval["PredictedCatchMT"] = final_test_pred
    df_eval["Residual"] = final_test_pred - y_test
    df_eval["AbsError"] = np.abs(final_test_pred - y_test)

    # 1. Error by Catch Magnitude Tier
    def catch_tier(val):
        if val == 0:
            return "1_Zero_Catch (0 MT)"
        elif val <= 25:
            return "2_Low_Catch (0-25 MT)"
        elif val <= 100:
            return "3_Medium_Catch (25-100 MT)"
        elif val <= 300:
            return "4_High_Catch (100-300 MT)"
        else:
            return "5_Extreme_Catch (>300 MT)"

    df_eval["Catch_Tier"] = df_eval["TotalCatchMT"].apply(catch_tier)
    tier_err = df_eval.groupby("Catch_Tier").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # 2. Error by Fleet (Top 10)
    top_fleets = df_eval["Fleet"].value_counts().head(10).index
    fleet_err = df_eval[df_eval["Fleet"].isin(top_fleets)].groupby("Fleet").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # 3. Error by Gear
    gear_err = df_eval.groupby("Gear").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # 4. Error by Region
    region_err = df_eval.groupby("Region").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # 5. Error by Year
    year_err = df_eval.groupby("Year").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # 6. Error by Season
    season_err = df_eval.groupby("MonsoonSeason").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    error_analysis_v2 = {
        "by_catch_magnitude": tier_err.to_dict(orient="records"),
        "by_fleet": fleet_err.to_dict(orient="records"),
        "by_gear": gear_err.to_dict(orient="records"),
        "by_region": region_err.to_dict(orient="records"),
        "by_year": year_err.to_dict(orient="records"),
        "by_season": season_err.to_dict(orient="records")
    }
    with open(os.path.join(reports_dir, "v2_error_analysis_data.json"), "w") as f:
        json.dump(error_analysis_v2, f, indent=2)

    # Diagnostic Figures
    print("\n[Step 5] Generating V2 Diagnostic Plots...")
    sns.set_theme(style="whitegrid")

    # Figure 1: Actual vs Predicted
    fig, ax = plt.subplots(figsize=(8, 7))
    sample_idx = np.random.choice(len(y_test), size=min(5000, len(y_test)), replace=False)
    ax.scatter(y_test[sample_idx], final_test_pred[sample_idx], alpha=0.3, color="teal", s=15, edgecolors="none")
    max_val = min(1500, max(y_test[sample_idx].max(), final_test_pred[sample_idx].max()))
    ax.plot([0, max_val], [0, max_val], "r--", lw=2, label="1:1 Perfect Agreement")
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_title(f"V2 Winner ({winning_model_name}): Actual vs Predicted Catch (R²={final_test_metrics['R2']:.3f})", fontsize=12, fontweight="bold")
    ax.set_xlabel("Actual Catch (Metric Tons)")
    ax.set_ylabel("Predicted Catch (Metric Tons)")
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "v2_actual_vs_predicted.png"), dpi=150)
    plt.close()

    # Figure 2: Error by Catch Magnitude
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=tier_err, x="Catch_Tier", y="MAE", ax=ax, hue="Catch_Tier", legend=False, palette="Blues_r")
    ax.set_title("V2 Mean Absolute Error by Catch Magnitude Tier", fontsize=12, fontweight="bold")
    ax.set_xlabel("Catch Magnitude Tier")
    ax.set_ylabel("MAE (Metric Tons)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "v2_error_by_magnitude.png"), dpi=150)
    plt.close()

    # Figure 3: Error by Region
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=region_err, x="Region", y="MAE", ax=ax, hue="Region", legend=False, palette="viridis")
    ax.set_title("V2 Mean Absolute Error Across Marine Sub-Basins", fontsize=12, fontweight="bold")
    ax.set_xlabel("Marine Region")
    ax.set_ylabel("MAE (Metric Tons)")
    plt.xticks(rotation=25)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "v2_error_by_region.png"), dpi=150)
    plt.close()

    # Figure 4: Validation Comparison Bar Chart
    fig, ax = plt.subplots(figsize=(11, 5))
    val_df = pd.DataFrame([
        {"Model": k.replace("_", " "), "Val_MAE": v["MAE"], "Val_R2": v["R2"]}
        for k, v in validation_summary.items()
    ])
    sns.barplot(data=val_df, x="Model", y="Val_MAE", ax=ax, hue="Model", legend=False, palette="mako")
    ax.set_title("Validation MAE Comparison Across All 6 Candidate Models", fontsize=12, fontweight="bold")
    ax.set_xlabel("Model Architecture")
    ax.set_ylabel("Validation MAE (Metric Tons)")
    plt.xticks(rotation=25)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "v2_models_validation_mae.png"), dpi=150)
    plt.close()

    # =========================================================================
    # PERSIST V2 WINNING MODEL & METADATA
    # =========================================================================
    print("\n[Step 6] Persisting V2 Final Winning Model & Artifacts...")
    final_v2_dir = os.path.join(models_dir, "final_model")
    os.makedirs(final_v2_dir, exist_ok=True)

    joblib.dump(selected_model_obj, os.path.join(final_v2_dir, "final_model.joblib"))
    joblib.dump(pre_v2, os.path.join(final_v2_dir, "preprocessing.joblib"))

    v2_metadata = {
        "model_name": f"IOTC Fisheries Catch Predictor V2 ({winning_model_name})",
        "model_type": winning_model_name,
        "version": "2.0.0",
        "training_framework": "xgboost / catboost / scikit-learn",
        "validation_metrics": validation_summary[winning_model_name],
        "final_test_metrics": final_test_metrics,
        "input_features": ALL_FEATURES_V2,
        "categorical_features": ALL_CATEGORICAL_V2,
        "numerical_features": NUMERICAL_V2,
        "encoded_feature_count": int(X_train_v2.shape[1]),
        "training_period": "1970-2014 (155,605 rows)",
        "validation_period": "2015-2018 (27,880 rows)",
        "test_period": "2019-2022 (27,692 rows)",
        "random_seed": 42
    }
    with open(os.path.join(final_v2_dir, "model_metadata.json"), "w") as f:
        json.dump(v2_metadata, f, indent=2)

    with open(os.path.join(final_v2_dir, "feature_schema.json"), "w") as f:
        json.dump({
            "features": ALL_FEATURES_V2,
            "categorical": ALL_CATEGORICAL_V2,
            "numerical": NUMERICAL_V2,
            "target": "TotalCatchMT",
            "unit": "Metric Tons (MT)"
        }, f, indent=2)

    print("\n" + "=" * 75)
    print("V2 IMPROVEMENT EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)
    return v2_metadata


if __name__ == "__main__":
    run_v2_experiment()
