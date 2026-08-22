"""
Seasonal Species Distribution Shift & Population-State Transitions Module.
"""

from ml.distribution_shift.builder import (
    ARABIAN_SEA_BBOX,
    MONTH_TO_SEASON,
    SeasonalDistributionDatasetBuilder,
    classify_arabian_sea_sector,
    compute_geodesic_bearing,
    get_grid_cell_id,
)
from ml.distribution_shift.models import (
    PopulationStateObservation,
    SeasonalDistributionTransition,
)
from ml.distribution_shift.summary import generate_transition_summary
from ml.distribution_shift.markov_baseline import CANONICAL_SECTORS, MarkovDistributionBaseline
from ml.distribution_shift.movement_model import (
    DistributionFeatureExtractor,
    SECTOR_CENTROIDS,
    XGBoostMovementClassifier,
)
from ml.distribution_shift.inference import (
    DistributionShiftInferenceEngine,
    get_inference_engine,
    predict_distribution_shift,
)

__all__ = [
    "ARABIAN_SEA_BBOX",
    "MONTH_TO_SEASON",
    "CANONICAL_SECTORS",
    "SECTOR_CENTROIDS",
    "SeasonalDistributionDatasetBuilder",
    "classify_arabian_sea_sector",
    "compute_geodesic_bearing",
    "get_grid_cell_id",
    "PopulationStateObservation",
    "SeasonalDistributionTransition",
    "generate_transition_summary",
    "MarkovDistributionBaseline",
    "DistributionFeatureExtractor",
    "XGBoostMovementClassifier",
    "DistributionShiftInferenceEngine",
    "get_inference_engine",
    "predict_distribution_shift",
]
