"""
Execute Data Quality Audit for Marine Species Identification.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.audit import audit_dataset


def main():
    raw_images_dir = PROJECT_ROOT / "data" / "raw" / "images"
    manifest_path = PROJECT_ROOT / "data" / "dataset_manifest.csv"
    report_path = PROJECT_ROOT / "reports" / "data_quality_report.json"
    plot_path = PROJECT_ROOT / "reports" / "class_distribution.png"

    print("=" * 60)
    print("PHASE E: DATA QUALITY AUDIT & MANIFEST GENERATION")
    print("=" * 60)

    df, report = audit_dataset(
        raw_images_dir=raw_images_dir,
        output_manifest_path=manifest_path,
        output_report_path=report_path,
        output_plot_path=plot_path,
        min_dimension=16
    )

    print("\n--- AUDIT SUMMARY ---")
    print(f"Total Valid Images: {report['valid_images']}")
    print(f"Corrupted Images: {report['corrupted_images_count']}")
    print(f"Exact Duplicates: {report['exact_duplicates_count']}")
    print(f"Distinct Species: {report['number_of_species']}")
    print(f"Distinct Families: {report['number_of_families']}")
    print(f"Width Range: {report['width_stats']['min']}px to {report['width_stats']['max']}px (Mean: {report['width_stats']['mean']}px)")
    print(f"Height Range: {report['height_stats']['min']}px to {report['height_stats']['max']}px (Mean: {report['height_stats']['mean']}px)")
    print(f"Imbalance Ratio (Max/Min): {report['imbalance_ratio']}x")
    print("\nSpecies Counts:")
    for sp, cnt in report['class_distribution'].items():
        trajs = report['trajectories_per_class'].get(sp, 'N/A')
        print(f"  - {sp:30s}: {cnt:4d} images ({trajs:3d} unique trajectories)")


if __name__ == "__main__":
    main()
