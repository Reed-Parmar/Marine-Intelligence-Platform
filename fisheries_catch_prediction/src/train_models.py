"""
End-to-end training, validation, tuning, evaluation, and interpretability pipeline
for Fisheries Catch Prediction (Phase 14.3).
"""
import os
import sys
import json
import time
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
import xgboost as xgb
import shap

sys.path.insert(0, os.path.abspath("."))
from fisheries_catch_prediction.src.pipeline import (
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
    ALL_INPUT_FEATURES,
    engineer_features,
    build_preprocessor,
    BaselineCatchRegressor,
    calculate_metrics
)


def run_training_suite(base_dir: str = "fisheries_catch_prediction"):
    print("=" * 70)
    print("STARTING FISHERIES CATCH PREDICTION TRAINING SUITE")
    print("=" * 70)

    splits_dir = os.path.join(base_dir, "data", "splits")
    models_dir = os.path.join(base_dir, "models")
    reports_dir = os.path.join(base_dir, "reports")
    figures_dir = os.path.join(reports_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)

    # 1. Load Data Splits
    print("\n[Step 1] Loading chronological data splits...")
    df_train = pd.read_csv(os.path.join(splits_dir, "train.csv"))
    df_val = pd.read_csv(os.path.join(splits_dir, "val.csv"))
    df_test = pd.read_csv(os.path.join(splits_dir, "test.csv"))

    print(f"Train set: {len(df_train)} rows (Years {df_train['Year'].min()}-{df_train['Year'].max()})")
    print(f"Val set:   {len(df_val)} rows (Years {df_val['Year'].min()}-{df_val['Year'].max()})")
    print(f"Test set:  {len(df_test)} rows (Years {df_test['Year'].min()}-{df_test['Year'].max()})")

    # Engineer Features
    X_train_df = engineer_features(df_train)
    y_train = df_train["TotalCatchMT"].values.astype(np.float64)

    X_val_df = engineer_features(df_val)
    y_val = df_val["TotalCatchMT"].values.astype(np.float64)

    X_test_df = engineer_features(df_test)
    y_test = df_test["TotalCatchMT"].values.astype(np.float64)

    # 2. Build and Fit Preprocessor
    print("\n[Step 2] Fitting Preprocessor (ColumnTransformer) on Train data...")
    preprocessor = build_preprocessor()
    X_train_trans = preprocessor.fit_transform(X_train_df[ALL_INPUT_FEATURES])
    X_val_trans = preprocessor.transform(X_val_df[ALL_INPUT_FEATURES])
    X_test_trans = preprocessor.transform(X_test_df[ALL_INPUT_FEATURES])

    # Extract transformed feature names
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_trans_feature_names = cat_feature_names + NUMERICAL_FEATURES
    print(f"Total encoded features: {len(all_trans_feature_names)}")

    # 3. Baseline Models (Mean & Median)
    print("\n[Step 3] Training and Evaluating Simple Baselines...")
    mean_baseline = BaselineCatchRegressor(strategy="mean")
    mean_baseline.fit(X_train_trans, y_train)

    med_baseline = BaselineCatchRegressor(strategy="median")
    med_baseline.fit(X_train_trans, y_train)

    mean_val_metrics = calculate_metrics(y_val, mean_baseline.predict(X_val_trans))
    mean_test_metrics = calculate_metrics(y_test, mean_baseline.predict(X_test_trans))
    med_val_metrics = calculate_metrics(y_val, med_baseline.predict(X_val_trans))
    med_test_metrics = calculate_metrics(y_test, med_baseline.predict(X_test_trans))

    print(f"Mean Baseline  -> Val MAE: {mean_val_metrics['MAE']:.3f}, Val RMSE: {mean_val_metrics['RMSE']:.3f}, Val R2: {mean_val_metrics['R2']:.4f}")
    print(f"Median Baseline-> Val MAE: {med_val_metrics['MAE']:.3f}, Val RMSE: {med_val_metrics['RMSE']:.3f}, Val R2: {med_val_metrics['R2']:.4f}")

    joblib.dump(mean_baseline, os.path.join(models_dir, "baseline", "mean_baseline.joblib"))
    joblib.dump(med_baseline, os.path.join(models_dir, "baseline", "median_baseline.joblib"))

    # 4. Random Forest Baseline ML Model
    print("\n[Step 4] Training Random Forest Regressor (n_estimators=200, max_depth=16)...")
    t0_rf = time.time()
    rf_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=16,
        min_samples_split=6,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train_trans, y_train)
    rf_train_time = time.time() - t0_rf
    print(f"Random Forest fit completed in {rf_train_time:.2f} s")

    rf_val_preds = np.clip(rf_model.predict(X_val_trans), 0, None)
    rf_test_preds = np.clip(rf_model.predict(X_test_trans), 0, None)
    rf_val_metrics = calculate_metrics(y_val, rf_val_preds)
    rf_test_metrics = calculate_metrics(y_test, rf_test_preds)

    print(f"Random Forest  -> Val MAE: {rf_val_metrics['MAE']:.3f}, Val RMSE: {rf_val_metrics['RMSE']:.3f}, Val R2: {rf_val_metrics['R2']:.4f}")
    joblib.dump(rf_model, os.path.join(models_dir, "random_forest", "random_forest.joblib"))

    # 5. XGBoost Primary Model (Default Configuration)
    print("\n[Step 5] Training Initial XGBoost Primary Model...")
    xgb_base = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30
    )
    xgb_base._estimator_type = "regressor"
    xgb_base.fit(
        X_train_trans, y_train,
        eval_set=[(X_val_trans, y_val)],
        verbose=False
    )
    xgb_base_val_preds = np.clip(xgb_base.predict(X_val_trans), 0, None)
    xgb_base_test_preds = np.clip(xgb_base.predict(X_test_trans), 0, None)
    xgb_base_val_metrics = calculate_metrics(y_val, xgb_base_val_preds)
    xgb_base_test_metrics = calculate_metrics(y_test, xgb_base_test_preds)

    print(f"XGBoost Base   -> Val MAE: {xgb_base_val_metrics['MAE']:.3f}, Val RMSE: {xgb_base_val_metrics['RMSE']:.3f}, Val R2: {xgb_base_val_metrics['R2']:.4f}")
    xgb_base._estimator_type = "regressor"
    xgb_base.save_model(os.path.join(models_dir, "xgboost", "xgboost_primary.json"))
    joblib.dump(xgb_base, os.path.join(models_dir, "xgboost", "xgboost_primary.joblib"))

    # 6. Controlled Hyperparameter Tuning on Validation Set Only
    print("\n[Step 6] Running Controlled Hyperparameter Tuning (Validation Only)...")
    candidate_configs = [
        {"max_depth": 5, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 1},
        {"max_depth": 6, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 1},
        {"max_depth": 6, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 1},
        {"max_depth": 6, "learning_rate": 0.08, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 1},
        {"max_depth": 7, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 3},
        {"max_depth": 7, "learning_rate": 0.05, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 3},
        {"max_depth": 7, "learning_rate": 0.07, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 5},
        {"max_depth": 8, "learning_rate": 0.03, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 5},
        {"max_depth": 8, "learning_rate": 0.05, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 3},
        {"max_depth": 8, "learning_rate": 0.05, "subsample": 0.90, "colsample_bytree": 0.90, "min_child_weight": 5},
        {"max_depth": 9, "learning_rate": 0.04, "subsample": 0.85, "colsample_bytree": 0.85, "min_child_weight": 5},
        {"max_depth": 9, "learning_rate": 0.06, "subsample": 0.90, "colsample_bytree": 0.90, "min_child_weight": 5}
    ]

    tuning_results = []
    best_config = None
    best_val_mae = float("inf")
    best_val_r2 = -float("inf")

    for i, cfg in enumerate(candidate_configs, 1):
        m = xgb.XGBRegressor(
            objective="reg:squarederror",
            n_estimators=600,
            learning_rate=cfg["learning_rate"],
            max_depth=cfg["max_depth"],
            subsample=cfg["subsample"],
            colsample_bytree=cfg["colsample_bytree"],
            min_child_weight=cfg["min_child_weight"],
            random_state=42,
            n_jobs=-1,
            early_stopping_rounds=30
        )
        m._estimator_type = "regressor"
        m.fit(X_train_trans, y_train, eval_set=[(X_val_trans, y_val)], verbose=False)
        val_pred = np.clip(m.predict(X_val_trans), 0, None)
        met = calculate_metrics(y_val, val_pred)

        record = {
            "config_id": i,
            "params": cfg,
            "best_iteration": int(m.best_iteration),
            "val_MAE": met["MAE"],
            "val_RMSE": met["RMSE"],
            "val_R2": met["R2"],
            "val_sMAPE": met["sMAPE"],
            "val_MedAE": met["MedAE"]
        }
        tuning_results.append(record)
        print(f"Config {i:2d}: depth={cfg['max_depth']}, lr={cfg['learning_rate']}, subsample={cfg['subsample']} | iter={m.best_iteration:3d} | Val MAE={met['MAE']:.3f}, RMSE={met['RMSE']:.3f}, R2={met['R2']:.4f}")

        # Selection criterion: minimize Validation MAE with high R2
        if met["MAE"] < best_val_mae:
            best_val_mae = met["MAE"]
            best_val_r2 = met["R2"]
            best_config = {**cfg, "n_estimators": m.best_iteration + 10}

    print(f"\nOptimal Configuration Selected based on Validation MAE ({best_val_mae:.3f} MT, R2={best_val_r2:.4f}):")
    print(best_config)

    # 7. Train Final Model with Selected Hyperparameters
    print("\n[Step 7] Training Final Tuned Model on Train (monitoring Val)...")
    final_xgb = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=best_config.get("n_estimators", 500),
        learning_rate=best_config["learning_rate"],
        max_depth=best_config["max_depth"],
        subsample=best_config["subsample"],
        colsample_bytree=best_config["colsample_bytree"],
        min_child_weight=best_config["min_child_weight"],
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30
    )
    final_xgb._estimator_type = "regressor"
    final_xgb.fit(X_train_trans, y_train, eval_set=[(X_val_trans, y_val)], verbose=False)

    final_val_preds = np.clip(final_xgb.predict(X_val_trans), 0, None)
    final_val_metrics = calculate_metrics(y_val, final_val_preds)

    # 8. FINAL EVALUATION ON STRICTLY UNTOUCHED TEST SET (2019-2022)
    print("\n" + "=" * 70)
    print("[Step 8] FINAL TEST EVALUATION (Evaluated ONCE on Untouched 2019-2022 Test Set)")
    print("=" * 70)
    final_test_preds = np.clip(final_xgb.predict(X_test_trans), 0, None)
    final_test_metrics = calculate_metrics(y_test, final_test_preds)

    for k, v in final_test_metrics.items():
        print(f"  {k:22s}: {v:.4f}" if isinstance(v, float) else f"  {k:22s}: {v}")

    # 9. Model Comparison Summary
    comparison_table = {
        "Mean_Baseline": {"validation": mean_val_metrics, "test": mean_test_metrics},
        "Median_Baseline": {"validation": med_val_metrics, "test": med_test_metrics},
        "Random_Forest": {"validation": rf_val_metrics, "test": rf_test_metrics},
        "XGBoost_Initial": {"validation": xgb_base_val_metrics, "test": xgb_base_test_metrics},
        "XGBoost_Final_Tuned": {"validation": final_val_metrics, "test": final_test_metrics}
    }
    with open(os.path.join(reports_dir, "model_comparison_data.json"), "w") as f:
        json.dump(comparison_table, f, indent=2)

    with open(os.path.join(reports_dir, "tuning_experiments.json"), "w") as f:
        json.dump({"candidate_configs": tuning_results, "best_config": best_config}, f, indent=2)

    # 10. Final Test Diagnostic Figures
    print("\n[Step 9] Generating Diagnostic Figures...")
    sns.set_theme(style="whitegrid")
    test_residuals = final_test_preds - y_test

    # Figure 1: Actual vs Predicted Scatter
    fig, ax = plt.subplots(figsize=(8, 7))
    sample_idx = np.random.choice(len(y_test), size=min(5000, len(y_test)), replace=False)
    ax.scatter(y_test[sample_idx], final_test_preds[sample_idx], alpha=0.3, color="teal", s=15, edgecolors="none")
    max_val = min(1500, max(y_test[sample_idx].max(), final_test_preds[sample_idx].max()))
    ax.plot([0, max_val], [0, max_val], "r--", lw=2, label="Perfect Agreement (1:1)")
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_title(f"Test Set (2019-2022): Actual vs Predicted Catch (R²={final_test_metrics['R2']:.3f})", fontsize=12, fontweight="bold")
    ax.set_xlabel("Actual Catch (Metric Tons)", fontsize=11)
    ax.set_ylabel("Predicted Catch (Metric Tons)", fontsize=11)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "actual_vs_predicted.png"), dpi=150)
    plt.close()

    # Figure 2: Residuals vs Predicted
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(final_test_preds[sample_idx], test_residuals[sample_idx], alpha=0.3, color="navy", s=15, edgecolors="none")
    ax.axhline(0, color="red", linestyle="--", lw=2)
    ax.set_xlim(0, max_val)
    ax.set_ylim(-600, 600)
    ax.set_title("Test Set Residuals vs Predicted Catch", fontsize=12, fontweight="bold")
    ax.set_xlabel("Predicted Catch (Metric Tons)", fontsize=11)
    ax.set_ylabel("Residual (Predicted - Actual, MT)", fontsize=11)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "residuals_vs_predicted.png"), dpi=150)
    plt.close()

    # Figure 3: Residual Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    res_clipped = np.clip(test_residuals, -300, 300)
    sns.histplot(res_clipped, bins=60, kde=True, ax=ax, color="indigo")
    ax.axvline(0, color="red", linestyle="--", lw=1.5, label="Zero Error")
    ax.axvline(final_test_metrics["Bias"], color="orange", linestyle=":", lw=2, label=f"Mean Bias ({final_test_metrics['Bias']:.2f} MT)")
    ax.set_title("Test Residual Error Distribution (Bounded [-300, 300] MT for Visualization)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Prediction Error (Predicted - Actual, MT)", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.legend(frameon=True)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "residual_distribution.png"), dpi=150)
    plt.close()

    # 11. Error Analysis by Strata
    print("\n[Step 10] Running Stratified Error Analysis...")
    df_test_eval = df_test.copy()
    df_test_eval["PredictedCatchMT"] = final_test_preds
    df_test_eval["Residual"] = test_residuals
    df_test_eval["AbsError"] = np.abs(test_residuals)

    # By Gear
    gear_error = df_test_eval.groupby("Gear").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # By Fleet (Top 10)
    top_fleets = df_test_eval["Fleet"].value_counts().head(10).index
    fleet_error = df_test_eval[df_test_eval["Fleet"].isin(top_fleets)].groupby("Fleet").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # By Year
    year_error = df_test_eval.groupby("Year").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    # By Catch Magnitude Tier
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

    df_test_eval["Catch_Tier"] = df_test_eval["TotalCatchMT"].apply(catch_tier)
    tier_error = df_test_eval.groupby("Catch_Tier").agg(
        Records=("TotalCatchMT", "count"),
        Mean_Actual=("TotalCatchMT", "mean"),
        Mean_Predicted=("PredictedCatchMT", "mean"),
        MAE=("AbsError", "mean"),
        RMSE=("Residual", lambda x: float(np.sqrt(np.mean(x ** 2)))),
        Bias=("Residual", "mean")
    ).reset_index()

    error_analysis_data = {
        "by_gear": gear_error.to_dict(orient="records"),
        "by_fleet": fleet_error.to_dict(orient="records"),
        "by_year": year_error.to_dict(orient="records"),
        "by_tier": tier_error.to_dict(orient="records")
    }
    with open(os.path.join(reports_dir, "error_analysis_data.json"), "w") as f:
        json.dump(error_analysis_data, f, indent=2)

    # Plot Error by Catch Tier
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=tier_error, x="Catch_Tier", y="MAE", ax=ax, palette="Blues_r")
    ax.set_title("Mean Absolute Error Across Catch Magnitude Tiers", fontsize=12, fontweight="bold")
    ax.set_xlabel("Catch Magnitude Tier")
    ax.set_ylabel("MAE (Metric Tons)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "error_by_magnitude.png"), dpi=150)
    plt.close()

    # 12. Feature Importance & SHAP Interpretability
    print("\n[Step 11] Calculating Feature Importance and SHAP Values...")
    # Native XGBoost Feature Importance
    importances = final_xgb.feature_importances_
    feat_imp_df = pd.DataFrame({
        "Feature": all_trans_feature_names,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)
    feat_imp_df.to_csv(os.path.join(reports_dir, "feature_importance.csv"), index=False)

    # Plot Top 15 Features
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=feat_imp_df.head(15), x="Importance", y="Feature", ax=ax, palette="mako")
    ax.set_title("XGBoost Native Feature Importance (Gain-Based)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Relative Importance Score")
    plt.tight_layout()
    fig.savefig(os.path.join(figures_dir, "feature_importance_top15.png"), dpi=150)
    plt.close()

    # SHAP TreeExplainer
    print("Computing SHAP values for test sample (500 instances)...")
    np.random.seed(42)
    shap_sample_idx = np.random.choice(X_test_trans.shape[0], size=min(500, X_test_trans.shape[0]), replace=False)
    X_shap = X_test_trans[shap_sample_idx]
    
    explainer = shap.TreeExplainer(final_xgb)
    shap_values = explainer.shap_values(X_shap)

    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(shap_values, X_shap, feature_names=all_trans_feature_names, show=False, max_display=15)
    plt.title("SHAP Feature Attribution Summary (Test Sample)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "shap_summary.png"), dpi=150, bbox_inches="tight")
    plt.close()

    # 13. Model Persistence
    print("\n[Step 12] Persisting Final Model & Preprocessing Pipeline...")
    final_dir = os.path.join(models_dir, "final_model")
    os.makedirs(final_dir, exist_ok=True)

    # Save final model
    final_xgb._estimator_type = "regressor"
    final_xgb.save_model(os.path.join(final_dir, "final_model.json"))
    joblib.dump(final_xgb, os.path.join(final_dir, "final_model.joblib"))
    # Save preprocessor
    joblib.dump(preprocessor, os.path.join(final_dir, "preprocessing.joblib"))

    # Feature schema
    feature_schema = {
        "raw_input_columns": ALL_INPUT_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "numerical_features": NUMERICAL_FEATURES,
        "encoded_feature_names": all_trans_feature_names,
        "target_variable": "TotalCatchMT",
        "target_units": "Metric Tons (MT)",
        "expected_dtypes": {
            "Fleet": "str",
            "Gear": "str",
            "Effort": "float",
            "EffortUnits": "str",
            "Month": "int (1-12)",
            "Year": "int (e.g. 2026)",
            "Latitude": "float (-45.0 to 30.0)",
            "Longitude": "float (20.0 to 150.0)",
            "SpatialResolution": "float (default 1.0)"
        }
    }
    with open(os.path.join(final_dir, "feature_schema.json"), "w") as f:
        json.dump(feature_schema, f, indent=2)

    # Model metadata
    metadata = {
        "model_name": "IOTC Surface Fisheries Catch Predictor",
        "model_type": "XGBoost Regressor (Tuned)",
        "model_version": "1.0.0",
        "training_framework": "xgboost",
        "framework_version": xgb.__version__,
        "dataset": "IOTC-2024-WPB22-DATA05-CESurface (FAO/IOTC Official)",
        "target": "TotalCatchMT",
        "target_units": "Metric Tons (MT)",
        "training_period": "1970-2014 (155,605 rows)",
        "validation_period": "2015-2018 (27,880 rows)",
        "test_period": "2019-2022 (27,692 rows)",
        "best_hyperparameters": best_config,
        "validation_metrics": final_val_metrics,
        "final_test_metrics": final_test_metrics,
        "random_seed": 42
    }
    with open(os.path.join(final_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 70)
    print("ALL TRAINING, EVALUATION, AND PERSISTENCE TASKS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return metadata


if __name__ == "__main__":
    run_training_suite()
