"""
Otolith and marine image analysis package exports.
"""

from data_pipeline.specialized_science.otolith.classification import (
    BaselineOtolithClassifier,
    OtolithClassificationResult,
    OtolithClassifier,
)
from data_pipeline.specialized_science.otolith.features import (
    BaselineMorphologicalFeatureExtractor,
    ImageFeatureExtractor,
    OtolithFeatureVector,
)
from data_pipeline.specialized_science.otolith.preprocessing import (
    ImageValidationResult,
    PreprocessedImage,
    preprocess_image,
    validate_image_input,
)
from data_pipeline.specialized_science.otolith.service import OtolithAnalysisService

__all__ = [
    "validate_image_input",
    "preprocess_image",
    "ImageValidationResult",
    "PreprocessedImage",
    "ImageFeatureExtractor",
    "BaselineMorphologicalFeatureExtractor",
    "OtolithFeatureVector",
    "OtolithClassifier",
    "BaselineOtolithClassifier",
    "OtolithClassificationResult",
    "OtolithAnalysisService",
]
