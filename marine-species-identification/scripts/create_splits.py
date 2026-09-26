"""
Execute Trajectory-Grouped Stratified Dataset Splitting.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.split import create_leakage_free_splits


def main():
    manifest_path = PROJECT_ROOT / "data" / "dataset_manifest.csv"
    splits_dir = PROJECT_ROOT / "data" / "splits"

    print("=" * 60)
    print("PHASE F: DATA LEAKAGE PREVENTION & SPLIT CREATION")
    print("=" * 60)

    summary = create_leakage_free_splits(
        manifest_path=manifest_path,
        splits_dir=splits_dir,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=42,
        deduplicate=True
    )

    print("\nSummary saved to data/splits/split_summary.json")


if __name__ == "__main__":
    main()
