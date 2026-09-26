"""
Data Quality Audit and Manifest Generator for Marine Species Identification.
Performs verification for corruptions, duplicates, image dimensions, color spaces,
class distributions, and generates the canonical dataset manifest.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.data.download import SPECIES_CATALOG


def compute_file_md5(file_path: Path) -> str:
    """Compute MD5 hash for exact duplicate detection."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def audit_dataset(
    raw_images_dir: Path,
    output_manifest_path: Path,
    output_report_path: Path,
    output_plot_path: Path,
    min_dimension: int = 16
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Scans all extracted images, validates readability, aspect ratio,
    exact duplicates, and extracts metadata.
    """
    records = []
    seen_hashes: Dict[str, str] = {}
    duplicates: List[Dict[str, str]] = []
    corrupt_files: List[str] = []
    small_images: List[str] = []
    grayscale_count = 0

    species_folders = sorted([d for d in raw_images_dir.iterdir() if d.is_dir() and d.name.startswith("species_")])

    for s_dir in species_folders:
        match = re.search(r"species_(\d+)", s_dir.name)
        if not match:
            continue
        species_id = int(match.group(1))
        species_info = SPECIES_CATALOG.get(species_id, {
            "name": f"Unknown_Species_{species_id}",
            "common": "Unknown",
            "family": "Unknown"
        })

        image_files = sorted(list(s_dir.glob("*.png")) + list(s_dir.glob("*.jpg")))
        for img_path in image_files:
            file_size = img_path.stat().st_size
            if file_size == 0:
                corrupt_files.append(str(img_path))
                continue

            # Compute MD5
            md5 = compute_file_md5(img_path)
            if md5 in seen_hashes:
                duplicates.append({
                    "original": seen_hashes[md5],
                    "duplicate": str(img_path),
                    "md5": md5
                })
                # We record duplicates but keep track of them
            else:
                seen_hashes[md5] = str(img_path)

            # Validate readability with PIL
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    mode = img.mode
                    img_format = img.format or "PNG"

                    if width < min_dimension or height < min_dimension:
                        small_images.append(str(img_path))

                    if mode in ("L", "1"):
                        grayscale_count += 1

                    # Parse trajectory id from filename (e.g., fish_000010919599_08281.png)
                    traj_match = re.search(r"fish_(\d+)_(\d+)", img_path.stem)
                    if traj_match:
                        tracking_id = traj_match.group(1)
                        fish_id = traj_match.group(2)
                    else:
                        tracking_id = "unknown"
                        fish_id = img_path.stem

                    records.append({
                        "image_path": str(img_path.resolve()),
                        "relative_path": str(img_path.relative_to(raw_images_dir.parent.parent)),
                        "filename": img_path.name,
                        "species_id": species_id,
                        "species_name": species_info["name"],
                        "common_name": species_info["common"],
                        "family": species_info["family"],
                        "tracking_id": tracking_id,
                        "fish_id": fish_id,
                        "width": width,
                        "height": height,
                        "aspect_ratio": round(width / max(height, 1), 3),
                        "channels": len(img.getbands()),
                        "mode": mode,
                        "format": img_format,
                        "file_size_bytes": file_size,
                        "md5": md5,
                        "is_duplicate": md5 in [d["md5"] for d in duplicates]
                    })
            except Exception as e:
                corrupt_files.append(f"{img_path}: {e}")

    df = pd.DataFrame(records)

    # Save manifest
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_manifest_path, index=False)
    print(f"Dataset manifest saved to {output_manifest_path} ({len(df)} images)")

    # Compute audit metrics
    class_distribution = df["species_name"].value_counts().to_dict()
    family_distribution = df["family"].value_counts().to_dict()
    unique_trajectories = df.groupby("species_name")["tracking_id"].nunique().to_dict()

    audit_summary = {
        "dataset_name": "Fish4Knowledge (F4K) Marine Species Ground-Truth Benchmark",
        "total_images_scanned": len(df) + len(corrupt_files),
        "valid_images": len(df),
        "corrupted_images_count": len(corrupt_files),
        "corrupted_files": corrupt_files,
        "exact_duplicates_count": len(duplicates),
        "duplicates_sample": duplicates[:5],
        "grayscale_images_count": grayscale_count,
        "small_images_below_threshold_count": len(small_images),
        "min_dimension_threshold_px": min_dimension,
        "width_stats": {
            "min": int(df["width"].min()),
            "max": int(df["width"].max()),
            "mean": float(round(df["width"].mean(), 1)),
            "median": float(df["width"].median())
        },
        "height_stats": {
            "min": int(df["height"].min()),
            "max": int(df["height"].max()),
            "mean": float(round(df["height"].mean(), 1)),
            "median": float(df["height"].median())
        },
        "number_of_species": int(df["species_name"].nunique()),
        "number_of_families": int(df["family"].nunique()),
        "class_distribution": class_distribution,
        "family_distribution": family_distribution,
        "trajectories_per_class": unique_trajectories,
        "imbalance_ratio": float(round(df["species_name"].value_counts().max() / df["species_name"].value_counts().min(), 2)),
    }

    # Save report JSON
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"Audit report saved to {output_report_path}")

    # Plot class distribution
    try:
        plt.figure(figsize=(12, 6))
        sns.set_theme(style="whitegrid")
        order = df["species_name"].value_counts().index
        ax = sns.countplot(data=df, y="species_name", order=order, palette="viridis")
        plt.title("Fish4Knowledge Marine Species Class Distribution", fontsize=14, weight="bold")
        plt.xlabel("Number of Verified Underwater Images", fontsize=12)
        plt.ylabel("Marine Species (Scientific Name)", fontsize=12)
        for p in ax.patches:
            width = p.get_width()
            ax.annotate(f"{int(width)}", (width + 5, p.get_y() + p.get_height() / 2.),
                        ha="left", va="center", fontsize=10, color="black")
        plt.tight_layout()
        output_plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_plot_path, dpi=300)
        plt.close()
        print(f"Class distribution chart saved to {output_plot_path}")
    except Exception as e:
        print(f"Plot generation note: {e}")

    return df, audit_summary
