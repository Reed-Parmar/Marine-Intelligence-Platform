"""
Script to Execute Phase M (Final Untouched Test Evaluation)
and Phase N/O (Error Analysis & Confidence Calibration).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.error_analysis import perform_error_analysis
from src.evaluation.evaluate import evaluate_model_on_test_set


def main():
    print("=" * 60)
    print("PHASE M & N: FINAL TEST EVALUATION & ERROR ANALYSIS")
    print("=" * 60)

    # Prefer final tuned model, fallback to baseline if final not yet available
    final_weights = PROJECT_ROOT / "models" / "final_model" / "final_model.pth"
    baseline_weights = PROJECT_ROOT / "models" / "baseline" / "baseline_model.pth"

    if final_weights.exists():
        model_weights = final_weights
        print(f"Evaluating FINAL TUNED model: {model_weights}")
    elif baseline_weights.exists():
        model_weights = baseline_weights
        print(f"Evaluating BASELINE model: {model_weights}")
    else:
        raise FileNotFoundError("No trained model weights found in models/final_model or models/baseline.")

    test_csv = PROJECT_ROOT / "data" / "splits" / "test.csv"
    class_mapping = PROJECT_ROOT / "models" / "class_mapping.json"
    results_dir = PROJECT_ROOT / "results"
    reports_dir = PROJECT_ROOT / "reports"

    # 1. Untouched Test Set Evaluation (Phase M)
    metrics, cm, all_probs, y_true, y_pred = evaluate_model_on_test_set(
        model_weights_path=model_weights,
        test_csv_path=test_csv,
        class_mapping_path=class_mapping,
        results_dir=results_dir,
        architecture="resnet18",
        batch_size=32
    )

    # 2. Error Analysis & Confidence Calibration (Phase N & O)
    error_report_path = reports_dir / "error_analysis_report.json"
    error_analysis = perform_error_analysis(
        test_csv_path=test_csv,
        class_mapping_path=class_mapping,
        y_true=y_true,
        y_pred=y_pred,
        all_probs=all_probs,
        output_report_path=error_report_path
    )

    print("\nPhase M & N completed successfully!")


if __name__ == "__main__":
    main()
