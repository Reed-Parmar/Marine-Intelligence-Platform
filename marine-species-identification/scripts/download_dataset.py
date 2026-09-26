"""
Script to download and verify the Fish4Knowledge marine species dataset.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.download import (
    SPECIES_CATALOG,
    fetch_class_mapping,
    download_species_archives,
)

SELECTED_SPECIES_IDS = [2, 4, 5, 6, 7, 8, 9, 10, 12, 16]

def main():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("PHASE D: DATASET ACQUISITION - FISH4KNOWLEDGE")
    print("=" * 60)
    print(f"Target directory: {raw_dir}")
    print(f"Selected species count: {len(SELECTED_SPECIES_IDS)}")
    for sid in SELECTED_SPECIES_IDS:
        info = SPECIES_CATALOG[sid]
        print(f"  - [{sid:02d}] {info['name']} ({info['common']}, Family: {info['family']})")

    # 1. Fetch class mapping
    class_csv_path = fetch_class_mapping(raw_dir)
    print(f"Official class mapping saved to: {class_csv_path}")

    # 2. Download and extract species archives
    # To ensure balance while preserving real-world natural distribution,
    # cap maximum images per class at 600 while retaining all images for rare classes.
    downloaded = download_species_archives(
        raw_dir=raw_dir,
        species_ids=SELECTED_SPECIES_IDS,
        max_images_per_class=600
    )

    print("\nDataset acquisition completed!")
    print(f"Total species downloaded: {len(downloaded)}")


if __name__ == "__main__":
    main()
