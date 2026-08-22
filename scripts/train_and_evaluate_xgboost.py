"""
Comprehensive Training, Evaluation, and Comparison Runner for XGBoost Movement Models.

Experiments:
1. Model 0: Markov Baseline
2. Model 1: Structural XGBoost
3. Model 2: Environmental XGBoost (Native NaN support)
4. Model 3: Full XGBoost (Environmental XGBoost + Markov Priors)
5. Persistence Baseline
"""

from collections import Counter
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

# Ensure repository root is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.db.database import execute_query
from ml.distribution_shift.markov_baseline import (
    CANONICAL_SECTORS,
    MarkovDistributionBaseline,
    evaluate_predictions,
)
from ml.distribution_shift.movement_model import (
    DistributionFeatureExtractor,
    SECTOR_CENTROIDS,
    XGBoostMovementClassifier,
    calculate_geographic_displacement_error,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATASET_PATH = root_dir / "data_pipeline" / "output" / "species_seasonal_distribution_shifts.json"
MODELS_DIR = root_dir / "data_pipeline" / "output" / "models"
EVAL_DIR = root_dir / "data_pipeline" / "output" / "evaluation"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset_with_temporal_splits():
    """Loads transitions and partitions strictly by year."""
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    transitions = data["transitions"]

    logger.info("Querying observation timestamp years from database...")
    rows = execute_query("""
        SELECT id::text as record_id, EXTRACT(YEAR FROM timestamp)::int as yr
        FROM public.species_occurrences
        WHERE timestamp IS NOT NULL
        UNION ALL
        SELECT id::text as record_id, EXTRACT(YEAR FROM timestamp)::int as yr
        FROM public.fisheries_records
        WHERE timestamp IS NOT NULL;
    """)
    rec_to_yr = {r["record_id"]: r["yr"] for r in rows}

    train_trans = []
    val_trans = []
    test_trans = []

    for t in transitions:
        r_ids = t.get("source_record_ids", [])
        yrs = [rec_to_yr.get(rid) for rid in r_ids if rid in rec_to_yr]
        max_yr = max(yrs) if yrs else 2020

        t_copy = dict(t)
        t_copy["observation_year"] = max_yr

        if max_yr <= 2023:
            train_trans.append(t_copy)
        elif max_yr == 2024:
            val_trans.append(t_copy)
            test_trans.append(t_copy)
        else:
            test_trans.append(t_copy)

    logger.info(f"Split completed: Train={len(train_trans)} (<=2023), Val={len(val_trans)} (2024), Holdout={len(test_trans)} (2024-2026)")
    return train_trans, val_trans, test_trans, transitions


def evaluate_model_pipeline(
    model_name: str,
    y_true: List[str],
    y_prob: np.ndarray,
    feature_names: List[str],
) -> Dict[str, Any]:
    """Computes full suite of classification, calibration, and geographic error metrics."""
    prob_dicts = [
        {CANONICAL_SECTORS[j]: float(y_prob[i, j]) for j in range(len(CANONICAL_SECTORS))}
        for i in range(len(y_true))
    ]
    metrics = evaluate_predictions(y_true, prob_dicts, CANONICAL_SECTORS)

    y_pred_sectors = [CANONICAL_SECTORS[idx] for idx in np.argmax(y_prob, axis=1)]
    geo_errs = calculate_geographic_displacement_error(y_true, y_pred_sectors)
    metrics.update(geo_errs)

    # Per-sector breakdown
    per_sector = {}
    for s_idx, s_name in enumerate(CANONICAL_SECTORS):
        y_true_binary = np.array([y == s_name for y in y_true])
        y_pred_binary = np.array([p == s_name for p in y_pred_sectors])

        tp = int(np.sum(y_true_binary & y_pred_binary))
        fp = int(np.sum((~y_true_binary) & y_pred_binary))
        fn = int(np.sum(y_true_binary & (~y_pred_binary)))
        support = int(np.sum(y_true_binary))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_sector[s_name] = {
            "support": support,
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
        }

    return {
        "model_name": model_name,
        "overall_metrics": metrics,
        "per_sector_metrics": per_sector,
        "y_pred_sectors": y_pred_sectors,
        "prob_dicts": prob_dicts,
    }


def compute_confusion_matrix(y_true: List[str], y_pred: List[str]) -> pd.DataFrame:
    """Builds 7x7 confusion matrix DataFrame."""
    matrix = np.zeros((len(CANONICAL_SECTORS), len(CANONICAL_SECTORS)), dtype=int)
    sec_map = {s: i for i, s in enumerate(CANONICAL_SECTORS)}

    for t, p in zip(y_true, y_pred):
        if t in sec_map and p in sec_map:
            matrix[sec_map[t], sec_map[p]] += 1

    return pd.DataFrame(matrix, index=CANONICAL_SECTORS, columns=CANONICAL_SECTORS)


def run_experiments():
    train_trans, val_trans, test_trans, all_trans = load_dataset_with_temporal_splits()

    # 1. Fit Markov Baseline on Train Set (<= 2023)
    logger.info("Fitting Markov Baseline (Model 0)...")
    markov = MarkovDistributionBaseline(min_support=3)
    markov.fit(train_trans)

    # 2. Fit Feature Extractor
    logger.info("Fitting Feature Extractor on Train Set...")
    fe = DistributionFeatureExtractor()
    fe.fit(train_trans)

    # Transform Train, Val, Test across feature sets
    logger.info("Transforming datasets for Structural, Environmental, and Full experiments...")
    X_train_struct, y_train, _ = fe.transform(train_trans, model_type="structural")
    X_val_struct, y_val, _ = fe.transform(val_trans, model_type="structural")
    X_test_struct, y_test, _ = fe.transform(test_trans, model_type="structural")

    X_train_env, _, _ = fe.transform(train_trans, model_type="environmental")
    X_val_env, _, _ = fe.transform(val_trans, model_type="environmental")
    X_test_env, _, _ = fe.transform(test_trans, model_type="environmental")

    X_train_full, _, _ = fe.transform(train_trans, model_type="full", markov_model=markov)
    X_val_full, _, _ = fe.transform(val_trans, model_type="full", markov_model=markov)
    X_test_full, _, _ = fe.transform(test_trans, model_type="full", markov_model=markov)

    # 3. Train Model 1: Structural XGBoost
    logger.info("Training Model 1: Structural XGBoost...")
    model1 = XGBoostMovementClassifier(
        model_type="structural",
        n_estimators=120,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model1.fit(X_train_struct, y_train, eval_set=[(X_val_struct, y_val)])
    model1.save_model(str(MODELS_DIR / "model1_structural_xgboost.json"))

    # 4. Train Model 2: Environmental XGBoost
    logger.info("Training Model 2: Environmental XGBoost (Native NaN support)...")
    model2 = XGBoostMovementClassifier(
        model_type="environmental",
        n_estimators=120,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model2.fit(X_train_env, y_train, eval_set=[(X_val_env, y_val)])
    model2.save_model(str(MODELS_DIR / "model2_environmental_xgboost.json"))

    # 5. Train Model 3: Full XGBoost (Markov Priors + Environmental)
    logger.info("Training Model 3: Full XGBoost (Markov Priors + Environmental)...")
    model3 = XGBoostMovementClassifier(
        model_type="full",
        n_estimators=120,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model3.fit(X_train_full, y_train, eval_set=[(X_val_full, y_val)])
    model3.save_model(str(MODELS_DIR / "model3_full_xgboost.json"))

    # 6. Evaluate All Models on Holdout Test Set (2024-2026)
    y_test_true = [t["target_sector"] for t in test_trans]

    # Baseline: Persistence
    pers_probs = np.zeros((len(test_trans), len(CANONICAL_SECTORS)))
    for i, t in enumerate(test_trans):
        s_idx = CANONICAL_SECTORS.index(t["current_sector"])
        pers_probs[i, s_idx] = 1.0
    eval_pers = evaluate_model_pipeline("Persistence Baseline", y_test_true, pers_probs, [])

    # Model 0: Markov Baseline A
    markov_preds = [
        markov.predict_distribution(
            species=t["scientific_name"],
            source_sector=t["current_sector"],
            season_code=t["season_code"],
            delta_t=(int(t.get("target_month", t["month"])) - int(t["month"])) % 12 or 1,
            mode="species_conditioned",
        )
        for t in test_trans
    ]
    markov_probs = np.array([[p["probabilities"][s] for s in CANONICAL_SECTORS] for p in markov_preds])
    eval_markov = evaluate_model_pipeline("Model 0: Markov Baseline A", y_test_true, markov_probs, [])

    # Model 1: Structural XGBoost
    m1_probs = model1.predict_proba(X_test_struct)
    eval_m1 = evaluate_model_pipeline("Model 1: Structural XGBoost", y_test_true, m1_probs, model1.feature_names)

    # Model 2: Environmental XGBoost
    m2_probs = model2.predict_proba(X_test_env)
    eval_m2 = evaluate_model_pipeline("Model 2: Environmental XGBoost", y_test_true, m2_probs, model2.feature_names)

    # Model 3: Full XGBoost
    m3_probs = model3.predict_proba(X_test_full)
    eval_m3 = evaluate_model_pipeline("Model 3: Full XGBoost", y_test_true, m3_probs, model3.feature_names)

    # Also evaluate on Training Set (Pre-2024) to compare fit capacity
    y_train_true = [t["target_sector"] for t in train_trans]
    train_m1_probs = model1.predict_proba(X_train_struct)
    train_eval_m1 = evaluate_model_pipeline("Model 1 (Train)", y_train_true, train_m1_probs, model1.feature_names)

    train_m2_probs = model2.predict_proba(X_train_env)
    train_eval_m2 = evaluate_model_pipeline("Model 2 (Train)", y_train_true, train_m2_probs, model2.feature_names)

    train_m3_probs = model3.predict_proba(X_train_full)
    train_eval_m3 = evaluate_model_pipeline("Model 3 (Train)", y_train_true, train_m3_probs, model3.feature_names)

    train_markov_preds = [
        markov.predict_distribution(
            species=t["scientific_name"],
            source_sector=t["current_sector"],
            season_code=t["season_code"],
            delta_t=(int(t.get("target_month", t["month"])) - int(t["month"])) % 12 or 1,
            mode="species_conditioned",
        )
        for t in train_trans
    ]
    train_markov_probs = np.array([[p["probabilities"][s] for s in CANONICAL_SECTORS] for p in train_markov_preds])
    train_eval_markov = evaluate_model_pipeline("Model 0 (Train)", y_train_true, train_markov_probs, [])

    # 7. Subgroup Analysis: Environmental Context Subsets on Test Set
    has_env_mask = np.array([t.get("sst_celsius") is not None for t in test_trans])
    env_subset_indices = np.where(has_env_mask)[0]
    no_env_subset_indices = np.where(~has_env_mask)[0]

    subgroup_eval = {}
    if len(env_subset_indices) > 0:
        y_env_true = [y_test_true[i] for i in env_subset_indices]
        subgroup_eval["with_environmental_context"] = {
            "sample_size": len(env_subset_indices),
            "persistence": evaluate_model_pipeline("Persistence", y_env_true, pers_probs[env_subset_indices], [])["overall_metrics"],
            "markov_baseline": evaluate_model_pipeline("Markov", y_env_true, markov_probs[env_subset_indices], [])["overall_metrics"],
            "model1_structural": evaluate_model_pipeline("M1", y_env_true, m1_probs[env_subset_indices], [])["overall_metrics"],
            "model2_environmental": evaluate_model_pipeline("M2", y_env_true, m2_probs[env_subset_indices], [])["overall_metrics"],
            "model3_full": evaluate_model_pipeline("M3", y_env_true, m3_probs[env_subset_indices], [])["overall_metrics"],
        }

    if len(no_env_subset_indices) > 0:
        y_noenv_true = [y_test_true[i] for i in no_env_subset_indices]
        subgroup_eval["without_environmental_context"] = {
            "sample_size": len(no_env_subset_indices),
            "persistence": evaluate_model_pipeline("Persistence", y_noenv_true, pers_probs[no_env_subset_indices], [])["overall_metrics"],
            "markov_baseline": evaluate_model_pipeline("Markov", y_noenv_true, markov_probs[no_env_subset_indices], [])["overall_metrics"],
            "model1_structural": evaluate_model_pipeline("M1", y_noenv_true, m1_probs[no_env_subset_indices], [])["overall_metrics"],
            "model2_environmental": evaluate_model_pipeline("M2", y_noenv_true, m2_probs[no_env_subset_indices], [])["overall_metrics"],
            "model3_full": evaluate_model_pipeline("M3", y_noenv_true, m3_probs[no_env_subset_indices], [])["overall_metrics"],
        }

    # 8. Feature Importances
    imp_m2 = model2.get_feature_importances()
    imp_m2.to_csv(EVAL_DIR / "feature_importance_model2.csv", index=False)

    imp_m3 = model3.get_feature_importances()
    imp_m3.to_csv(EVAL_DIR / "feature_importance_model3.csv", index=False)

    # 9. Confusion Matrices
    cm_m2 = compute_confusion_matrix(y_test_true, eval_m2["y_pred_sectors"])
    cm_m2.to_csv(EVAL_DIR / "confusion_matrix_model2.csv")

    cm_m3 = compute_confusion_matrix(y_test_true, eval_m3["y_pred_sectors"])
    cm_m3.to_csv(EVAL_DIR / "confusion_matrix_model3.csv")

    # 10. Spatial Block Generalization Diagnostic (Hold out Gujarat Shelf 20°N-24°N)
    logger.info("Executing Spatial Block Holdout Diagnostic (Hold out Gujarat Shelf)...")
    guj_train = [t for t in train_trans if t["current_sector"] != "North Arabian Sea / Gujarat Shelf"]
    guj_test = [t for t in train_trans if t["current_sector"] == "North Arabian Sea / Gujarat Shelf"]

    if guj_test:
        fe_guj = DistributionFeatureExtractor().fit(guj_train)
        X_guj_tr, y_guj_tr, _ = fe_guj.transform(guj_train, model_type="environmental")
        X_guj_te, _, _ = fe_guj.transform(guj_test, model_type="environmental")

        m_guj = XGBoostMovementClassifier(model_type="environmental", n_estimators=80, max_depth=3).fit(X_guj_tr, y_guj_tr)
        guj_probs = m_guj.predict_proba(X_guj_te)
        guj_eval = evaluate_model_pipeline("Spatial Block (Gujarat Holdout)", [t["target_sector"] for t in guj_test], guj_probs, m_guj.feature_names)["overall_metrics"]
    else:
        guj_eval = {}

    # 11. Assemble Master Evaluation Summary
    master_eval = {
        "holdout_test_set_2024_2026": {
            "sample_size": len(test_trans),
            "models": {
                "persistence_baseline": eval_pers["overall_metrics"],
                "model0_markov_baseline": eval_markov["overall_metrics"],
                "model1_structural_xgboost": eval_m1["overall_metrics"],
                "model2_environmental_xgboost": eval_m2["overall_metrics"],
                "model3_full_xgboost": eval_m3["overall_metrics"],
            },
            "per_sector_metrics_model3": eval_m3["per_sector_metrics"],
        },
        "training_set_pre_2024": {
            "sample_size": len(train_trans),
            "models": {
                "model0_markov_baseline": train_eval_markov["overall_metrics"],
                "model1_structural_xgboost": train_eval_m1["overall_metrics"],
                "model2_environmental_xgboost": train_eval_m2["overall_metrics"],
                "model3_full_xgboost": train_eval_m3["overall_metrics"],
            }
        },
        "environmental_subgroup_analysis": subgroup_eval,
        "spatial_block_diagnostic_gujarat": guj_eval,
        "feature_importance_model2": imp_m2.to_dict(orient="records"),
        "feature_importance_model3": imp_m3.to_dict(orient="records"),
    }

    with open(EVAL_DIR / "xgboost_evaluation.json", "w", encoding="utf-8") as f:
        json.dump(master_eval, f, indent=2)

    with open(EVAL_DIR / "subgroup_environmental_comparison.json", "w", encoding="utf-8") as f:
        json.dump(subgroup_eval, f, indent=2)

    logger.info(f"Evaluation results successfully saved to {EVAL_DIR / 'xgboost_evaluation.json'}")

    # Print Formatted Report
    print("\n" + "=" * 90)
    print("XGBOOST MOVEMENT MODEL EVALUATION REPORT (STEP 3)")
    print("=" * 90)
    print(f"Total Dataset: {len(all_trans)} | Train Set: {len(train_trans)} | Holdout Test Set: {len(test_trans)}")
    print("-" * 90)
    print("1. OVERALL METRICS ON TEMPORAL HOLDOUT (2024-2026):")
    print(f"  • Persistence Baseline     : Top-1={eval_pers['overall_metrics']['top_1_accuracy']:.4f} | Top-3={eval_pers['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={eval_pers['overall_metrics']['macro_f1']:.4f} | LogLoss={eval_pers['overall_metrics']['log_loss']:.4f} | MeanDistErr={eval_pers['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 0 (Markov Baseline): Top-1={eval_markov['overall_metrics']['top_1_accuracy']:.4f} | Top-3={eval_markov['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={eval_markov['overall_metrics']['macro_f1']:.4f} | LogLoss={eval_markov['overall_metrics']['log_loss']:.4f} | MeanDistErr={eval_markov['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 1 (Structural XGB) : Top-1={eval_m1['overall_metrics']['top_1_accuracy']:.4f} | Top-3={eval_m1['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={eval_m1['overall_metrics']['macro_f1']:.4f} | LogLoss={eval_m1['overall_metrics']['log_loss']:.4f} | MeanDistErr={eval_m1['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 2 (Env XGBoost)    : Top-1={eval_m2['overall_metrics']['top_1_accuracy']:.4f} | Top-3={eval_m2['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={eval_m2['overall_metrics']['macro_f1']:.4f} | LogLoss={eval_m2['overall_metrics']['log_loss']:.4f} | MeanDistErr={eval_m2['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 3 (Full XGBoost)   : Top-1={eval_m3['overall_metrics']['top_1_accuracy']:.4f} | Top-3={eval_m3['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={eval_m3['overall_metrics']['macro_f1']:.4f} | LogLoss={eval_m3['overall_metrics']['log_loss']:.4f} | MeanDistErr={eval_m3['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print("-" * 90)
    print("2. TRAINING SET GENERALIZATION FIT (Pre-2024, N=2577):")
    print(f"  • Model 0 (Markov) : Top-1={train_eval_markov['overall_metrics']['top_1_accuracy']:.4f} | Top-3={train_eval_markov['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={train_eval_markov['overall_metrics']['macro_f1']:.4f} | LogLoss={train_eval_markov['overall_metrics']['log_loss']:.4f} | MeanDistErr={train_eval_markov['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 1 (Struct) : Top-1={train_eval_m1['overall_metrics']['top_1_accuracy']:.4f} | Top-3={train_eval_m1['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={train_eval_m1['overall_metrics']['macro_f1']:.4f} | LogLoss={train_eval_m1['overall_metrics']['log_loss']:.4f} | MeanDistErr={train_eval_m1['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 2 (Env)    : Top-1={train_eval_m2['overall_metrics']['top_1_accuracy']:.4f} | Top-3={train_eval_m2['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={train_eval_m2['overall_metrics']['macro_f1']:.4f} | LogLoss={train_eval_m2['overall_metrics']['log_loss']:.4f} | MeanDistErr={train_eval_m2['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print(f"  • Model 3 (Full)   : Top-1={train_eval_m3['overall_metrics']['top_1_accuracy']:.4f} | Top-3={train_eval_m3['overall_metrics']['top_3_accuracy']:.4f} | MacroF1={train_eval_m3['overall_metrics']['macro_f1']:.4f} | LogLoss={train_eval_m3['overall_metrics']['log_loss']:.4f} | MeanDistErr={train_eval_m3['overall_metrics']['mean_displacement_error_km']:.1f}km")
    print("-" * 90)
    print("3. TOP 5 FEATURE IMPORTANCES (MODEL 2 - ENVIRONMENTAL XGBOOST):")
    for row in imp_m2.head(5).itertuples():
        print(f"  • {row.feature:25s} : Gain={row.gain:8.2f} ({row.gain_pct:.1f}%) | Weight={row.weight:5.0f}")
    print("-" * 90)
    print("4. TOP 5 FEATURE IMPORTANCES (MODEL 3 - FULL XGBOOST):")
    for row in imp_m3.head(5).itertuples():
        print(f"  • {row.feature:25s} : Gain={row.gain:8.2f} ({row.gain_pct:.1f}%) | Weight={row.weight:5.0f}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    run_experiments()
