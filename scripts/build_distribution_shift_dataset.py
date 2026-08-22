"""
CLI Runner to build and export the Seasonal Species Distribution Shift transition dataset.
"""

import json
import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ml.distribution_shift.builder import SeasonalDistributionDatasetBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Initializing Seasonal Species Distribution Shift Dataset Builder...")
    builder = SeasonalDistributionDatasetBuilder(
        min_species_occurrences=3,  # Minimum occurrences in Arabian Sea
        grid_size_deg=1.0,          # Standard 1° x 1° grid cell
        env_fusion_radius_km=100.0, # 100 km spatial radius for CTD matching
        env_fusion_window_days=45.0 # Seasonal window
    )

    output_file = root_dir / "data_pipeline" / "output" / "species_seasonal_distribution_shifts.json"
    transitions, summary = builder.build_and_save(str(output_file))

    print("\n" + "=" * 80)
    print("SEASONAL SPECIES DISTRIBUTION SHIFT TRANSITION DATASET REPORT")
    print("=" * 80)
    print(json.dumps(summary, indent=2))
    print("=" * 80)
    print(f"Total Generated Transitions: {len(transitions)}")
    print(f"Dataset Successfully Saved To: {output_file}\n")


if __name__ == "__main__":
    main()
