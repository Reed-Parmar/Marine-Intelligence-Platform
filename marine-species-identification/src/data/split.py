"""
Trajectory-Grouped Stratified Dataset Splitting for Marine Species Identification.
Guarantees 100% data leakage prevention by ensuring all video frames from the same
underwater tracking sequence (tracking_id) belong strictly to either Train, Val, or Test.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


def create_leakage_free_splits(
    manifest_path: Path,
    splits_dir: Path,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42,
    deduplicate: bool = True
) -> Dict[str, any]:
    """
    Performs trajectory-grouped stratified train/val/test splitting.
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0"
    random.seed(random_seed)
    np.random.seed(random_seed)

    df = pd.read_csv(manifest_path)
    total_raw = len(df)

    # 1. Deduplication: remove exact duplicate image hashes
    if deduplicate:
        df = df.drop_duplicates(subset=["md5"]).copy()
    total_clean = len(df)
    removed_duplicates = total_raw - total_clean

    splits_dir.mkdir(parents=True, exist_ok=True)

    train_indices = []
    val_indices = []
    test_indices = []

    # Process each species independently for perfect stratification
    for species_name, group in df.groupby("species_name"):
        traj_groups = group.groupby("tracking_id")
        traj_items = []
        for traj_id, traj_df in traj_groups:
            traj_items.append((traj_id, traj_df.index.tolist(), len(traj_df)))

        # Shuffle trajectories deterministically
        random.shuffle(traj_items)

        total_species_images = len(group)
        target_train = int(round(total_species_images * train_ratio))
        target_val = int(round(total_species_images * val_ratio))

        cur_train_cnt = 0
        cur_val_cnt = 0

        sp_train_idx = []
        sp_val_idx = []
        sp_test_idx = []

        n_trajs = len(traj_items)

        for i, (traj_id, indices, count) in enumerate(traj_items):
            # If we have at least 3 trajectories, guarantee at least 1 in val and 1 in test
            if n_trajs >= 3:
                if i == 0:
                    sp_val_idx.extend(indices)
                    cur_val_cnt += count
                    continue
                elif i == 1:
                    sp_test_idx.extend(indices)
                    continue

            # Standard proportional filling
            if cur_train_cnt < target_train:
                sp_train_idx.extend(indices)
                cur_train_cnt += count
            elif cur_val_cnt < target_val:
                sp_val_idx.extend(indices)
                cur_val_cnt += count
            else:
                sp_test_idx.extend(indices)

        train_indices.extend(sp_train_idx)
        val_indices.extend(sp_val_idx)
        test_indices.extend(sp_test_idx)

    train_df = df.loc[train_indices].copy().reset_index(drop=True)
    val_df = df.loc[val_indices].copy().reset_index(drop=True)
    test_df = df.loc[test_indices].copy().reset_index(drop=True)

    train_df["split"] = "train"
    val_df["split"] = "validation"
    test_df["split"] = "test"

    # Verify ZERO index overlap
    train_idx_set = set(train_indices)
    val_idx_set = set(val_indices)
    test_idx_set = set(test_indices)
    assert len(train_idx_set.intersection(val_idx_set)) == 0, "Index overlap train-val"
    assert len(train_idx_set.intersection(test_idx_set)) == 0, "Index overlap train-test"
    assert len(val_idx_set.intersection(test_idx_set)) == 0, "Index overlap val-test"

    # Verify ZERO trajectory leakage between splits
    train_trajs = set(train_df["tracking_id"].unique())
    val_trajs = set(val_df["tracking_id"].unique())
    test_trajs = set(test_df["tracking_id"].unique())

    leak_train_val = train_trajs.intersection(val_trajs)
    leak_train_test = train_trajs.intersection(test_trajs)
    leak_val_test = val_trajs.intersection(test_trajs)

    assert len(leak_train_val) == 0, f"Trajectory leakage between train and val: {leak_train_val}"
    assert len(leak_train_test) == 0, f"Trajectory leakage between train and test: {leak_train_test}"
    assert len(leak_val_test) == 0, f"Trajectory leakage between val and test: {leak_val_test}"

    # Verify all 10 classes are present in train, val, and test
    assert train_df["species_name"].nunique() == df["species_name"].nunique(), "Missing classes in train"
    assert val_df["species_name"].nunique() == df["species_name"].nunique(), "Missing classes in val"
    assert test_df["species_name"].nunique() == df["species_name"].nunique(), "Missing classes in test"

    # Save split CSVs
    train_csv = splits_dir / "train.csv"
    val_csv = splits_dir / "val.csv"
    test_csv = splits_dir / "test.csv"

    train_df.to_csv(train_csv, index=False)
    val_df.to_csv(val_csv, index=False)
    test_df.to_csv(test_csv, index=False)

    train_dist = train_df["species_name"].value_counts().to_dict()
    val_dist = val_df["species_name"].value_counts().to_dict()
    test_dist = test_df["species_name"].value_counts().to_dict()

    summary = {
        "random_seed": random_seed,
        "leakage_prevention_method": "Trajectory-Grouped Stratified Splitting (grouped by video tracking_id)",
        "exact_duplicates_removed": removed_duplicates,
        "total_clean_images": total_clean,
        "train": {
            "count": len(train_df),
            "percentage": round(len(train_df) / total_clean * 100, 2),
            "unique_trajectories": len(train_trajs),
            "class_distribution": train_dist
        },
        "validation": {
            "count": len(val_df),
            "percentage": round(len(val_df) / total_clean * 100, 2),
            "unique_trajectories": len(val_trajs),
            "class_distribution": val_dist
        },
        "test": {
            "count": len(test_df),
            "percentage": round(len(test_df) / total_clean * 100, 2),
            "unique_trajectories": len(test_trajs),
            "class_distribution": test_dist
        },
        "leakage_verification": {
            "train_val_overlap_trajectories": len(leak_train_val),
            "train_test_overlap_trajectories": len(leak_train_test),
            "val_test_overlap_trajectories": len(leak_val_test),
            "status": "PASSED - ZERO TRAJECTORY LEAKAGE"
        }
    }

    summary_path = splits_dir / "split_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Splits created successfully with ZERO leakage!")
    print(f"Train: {len(train_df)} ({summary['train']['percentage']}%), {len(train_trajs)} trajectories")
    print(f"Val:   {len(val_df)} ({summary['validation']['percentage']}%), {len(val_trajs)} trajectories")
    print(f"Test:  {len(test_df)} ({summary['test']['percentage']}%), {len(test_trajs)} trajectories")
    print(f"Leakage check: {summary['leakage_verification']['status']}")
    print(f"All {df['species_name'].nunique()} species represented across Train, Val, and Test.")

    return summary
