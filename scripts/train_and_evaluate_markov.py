"""
Runner script to train, evaluate, and export the Scientific Markov Transition Baseline.
Evaluates Persistence Baseline vs Global Seasonal Markov (Baseline B) vs Species-Conditioned Markov (Baseline A).
"""

from collections import Counter
import json
import logging
from pathlib import Path
import sys
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATASET_PATH = root_dir / "data_pipeline" / "output" / "species_seasonal_distribution_shifts.json"
OUTPUT_DIR = root_dir / "data_pipeline" / "output" / "baseline"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset_with_temporal_splits():
    """
    Loads transitions and splits into Train (<=2023), Val (2024), and Test (2024-2026).
    """
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    transitions = data["transitions"]

    # Query record id -> timestamp/year mapping from database
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
        max_yr = max(yrs) if yrs else 2020  # default historical if unlinked

        t_copy = dict(t)
        t_copy["observation_year"] = max_yr

        if max_yr <= 2023:
            train_trans.append(t_copy)
        elif max_yr == 2024:
            val_trans.append(t_copy)
            test_trans.append(t_copy)
        else:  # 2025-2026
            test_trans.append(t_copy)

    logger.info(f"Split completed: Train={len(train_trans)} (<=2023), Val={len(val_trans)} (2024), Test/Holdout={len(test_trans)} (2024-2026)")
    return train_trans, val_trans, test_trans, transitions


def run_training_and_evaluation():
    train_trans, val_trans, test_trans, all_trans = load_dataset_with_temporal_splits()

    # Fit Markov Baseline on Training data (<= 2023)
    logger.info("Fitting Markov Distribution Baseline on historical train set (<= 2023)...")
    markov = MarkovDistributionBaseline(min_support=3)
    markov.fit(train_trans)

    # 1. Full Dataset Baseline Matrix Export
    full_markov = MarkovDistributionBaseline(min_support=3)
    full_markov.fit(all_trans)
    matrix_df = full_markov.export_transition_matrix()
    matrix_csv_path = OUTPUT_DIR / "markov_transition_matrix.csv"
    matrix_df.to_csv(matrix_csv_path)
    logger.info(f"Exported full empirical transition matrix to {matrix_csv_path}")

    # 2. Evaluate Models across Splits
    splits = {
        "validation_2024": val_trans,
        "test_holdout_2024_2026": test_trans,
        "train_historical_pre_2024": train_trans,
    }

    eval_results = {}

    for split_name, dataset in splits.items():
        if not dataset:
            continue

        y_true = [t["target_sector"] for t in dataset]

        # Persistence Baseline
        pers_preds = [markov.predict_persistence(t["current_sector"]) for t in dataset]
        pers_probs = [p["probabilities"] for p in pers_preds]
        pers_metrics = evaluate_predictions(y_true, pers_probs)

        # Baseline B: Global Seasonal Markov
        glob_preds = [
            markov.predict_distribution(
                species=t["scientific_name"],
                source_sector=t["current_sector"],
                season_code=t["season_code"],
                delta_t=(int(t.get("target_month", t["month"])) - int(t["month"])) % 12 or 1,
                mode="global_seasonal"
            )
            for t in dataset
        ]
        glob_probs = [p["probabilities"] for p in glob_preds]
        glob_metrics = evaluate_predictions(y_true, glob_probs)

        # Baseline A: Species-Conditioned Markov (with Hierarchical Fallback)
        spec_preds = [
            markov.predict_distribution(
                species=t["scientific_name"],
                source_sector=t["current_sector"],
                season_code=t["season_code"],
                delta_t=(int(t.get("target_month", t["month"])) - int(t["month"])) % 12 or 1,
                mode="species_conditioned"
            )
            for t in dataset
        ]
        spec_probs = [p["probabilities"] for p in spec_preds]
        spec_metrics = evaluate_predictions(y_true, spec_probs)

        # Fallback level distribution for Baseline A
        fallback_counts = Counter(p["fallback_level"] for p in spec_preds)
        fallback_summary = {
            f"Level {lvl}": {
                "count": cnt,
                "pct": round((cnt / len(dataset)) * 100, 2)
            }
            for lvl, cnt in sorted(fallback_counts.items())
        }

        eval_results[split_name] = {
            "sample_size": len(dataset),
            "persistence_baseline": pers_metrics,
            "global_seasonal_markov_baseline_b": glob_metrics,
            "species_conditioned_markov_baseline_a": spec_metrics,
            "species_markov_fallback_levels": fallback_summary,
        }

    # 3. Model Metadata & Transition Probabilities for Top 5 MVP Species
    top_mvp_species = [
        "Sardinella longiceps",      # Indian Oil Sardine
        "Rastrelliger kanagurta",    # Indian Mackerel
        "Stolephorus indicus",       # Indian Anchovy
        "Thunnus albacares",         # Yellowfin Tuna
        "Katsuwonus pelamis",        # Skipjack Tuna
    ]

    mvp_examples = {}
    for sp in top_mvp_species:
        # Example 1: Pre-Monsoon (Season 1) -> SW Monsoon in Malabar Shelf
        pred_monsoon = full_markov.predict_distribution(
            species=sp,
            source_sector="Malabar Upwelling Shelf",
            season_code=1,
            delta_t=2,
            mode="species_conditioned"
        )
        # Example 2: SW Monsoon (Season 2) -> Post-Monsoon
        pred_post = full_markov.predict_distribution(
            species=sp,
            source_sector="Malabar Upwelling Shelf",
            season_code=2,
            delta_t=3,
            mode="species_conditioned"
        )
        mvp_examples[sp] = {
            "pre_to_sw_monsoon_shift": pred_monsoon,
            "sw_to_post_monsoon_shift": pred_post,
        }

    # 4. Export Model Artifact
    model_payload = {
        "metadata": {
            "model_type": "Hierarchical Empirical Markov Distribution Baseline",
            "sectors": CANONICAL_SECTORS,
            "num_sectors": len(CANONICAL_SECTORS),
            "min_support_threshold": markov.min_support,
            "total_training_transitions": markov.total_training_transitions,
            "total_full_dataset_transitions": len(all_trans),
            "hierarchical_levels": [
                "Level 1: P(target | species, source_sector, season, delta_t)",
                "Level 2: P(target | species, source_sector, season)",
                "Level 3: P(target | source_sector, season, delta_t)",
                "Level 4: P(target | source_sector, season)",
                "Level 5: Global Target Sector Distribution Prior",
            ],
            "zero_environmental_leakage": True,
        },
        "evaluation_summary": eval_results,
        "mvp_species_transition_profiles": mvp_examples,
    }

    model_json_path = OUTPUT_DIR / "markov_model.json"
    with open(model_json_path, "w", encoding="utf-8") as f:
        json.dump(model_payload, f, indent=2)
    logger.info(f"Saved Markov model artifact to {model_json_path}")

    eval_json_path = OUTPUT_DIR / "markov_evaluation.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)
    logger.info(f"Saved evaluation metrics to {eval_json_path}")

    # Print Formatted Report
    print("\n" + "=" * 85)
    print("SCIENTIFIC MARKOV BASELINE EVALUATION REPORT (STEP 2B)")
    print("=" * 85)
    print(f"Total Transitions: {len(all_trans)}")
    print(f"Training Set (<= 2023): {len(train_trans)} | Holdout Test Set (2024-2026): {len(test_trans)}")
    print("-" * 85)
    print("EVALUATION ON TEMPORAL HOLDOUT (2024-2026):")
    holdout_eval = eval_results["test_holdout_2024_2026"]
    print(f"1. Persistence Baseline : Top-1 Acc={holdout_eval['persistence_baseline']['top_1_accuracy']:.4f} | Macro F1={holdout_eval['persistence_baseline']['macro_f1']:.4f} | LogLoss={holdout_eval['persistence_baseline']['log_loss']:.4f} | Brier={holdout_eval['persistence_baseline']['brier_score']:.4f}")
    print(f"2. Global Markov (B)    : Top-1 Acc={holdout_eval['global_seasonal_markov_baseline_b']['top_1_accuracy']:.4f} | Top-3 Acc={holdout_eval['global_seasonal_markov_baseline_b']['top_3_accuracy']:.4f} | Macro F1={holdout_eval['global_seasonal_markov_baseline_b']['macro_f1']:.4f} | LogLoss={holdout_eval['global_seasonal_markov_baseline_b']['log_loss']:.4f} | Brier={holdout_eval['global_seasonal_markov_baseline_b']['brier_score']:.4f}")
    print(f"3. Species Markov (A)   : Top-1 Acc={holdout_eval['species_conditioned_markov_baseline_a']['top_1_accuracy']:.4f} | Top-3 Acc={holdout_eval['species_conditioned_markov_baseline_a']['top_3_accuracy']:.4f} | Macro F1={holdout_eval['species_conditioned_markov_baseline_a']['macro_f1']:.4f} | LogLoss={holdout_eval['species_conditioned_markov_baseline_a']['log_loss']:.4f} | Brier={holdout_eval['species_conditioned_markov_baseline_a']['brier_score']:.4f}")
    print("-" * 85)
    print("SARDINELLA LONGICEPS (INDIAN OIL SARDINE) PRE-MONSOON -> SW MONSOON TRANSITION PROFILE:")
    print(json.dumps(mvp_examples["Sardinella longiceps"]["pre_to_sw_monsoon_shift"], indent=2))
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_training_and_evaluation()
