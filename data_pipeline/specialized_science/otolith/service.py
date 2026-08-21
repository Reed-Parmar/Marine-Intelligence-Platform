"""
Phase 7 — Otolith / Marine Image Analysis Service.
Main orchestrator for otolith and marine image processing: validation, preprocessing,
morphological feature extraction, classification, and persistence.
"""

from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union
from PIL import Image

from data_pipeline.specialized_science.common.models import (
    EvidenceType,
    InMemoryStorageRepository,
    ScientificEvidence,
    SpecializedResult,
    StorageRepository,
)
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
from data_pipeline.specialized_science.taxonomy.service import TaxonomyService


class OtolithAnalysisService:
    """
    Unified Otolith and Marine Image Analysis Service.

    Connects image preprocessing, feature extraction, classification, and taxonomy.
    Features and Classifier are decoupled via Protocols for Phase 8 CNN integration.
    """

    def __init__(
        self,
        feature_extractor: Optional[ImageFeatureExtractor] = None,
        classifier: Optional[OtolithClassifier] = None,
        taxonomy_service: Optional[TaxonomyService] = None,
        storage_repo: Optional[StorageRepository] = None,
    ) -> None:
        self.feature_extractor = feature_extractor or BaselineMorphologicalFeatureExtractor()
        self.classifier = classifier or BaselineOtolithClassifier()
        self.taxonomy_service = taxonomy_service or TaxonomyService()
        self.storage_repo = storage_repo or InMemoryStorageRepository()

    def validate_image(
        self,
        image_input: Union[str, Path, bytes, BinaryIO, Image.Image],
        min_dimension: int = 32,
    ) -> ImageValidationResult:
        """Validates image readability, format, and dimensions."""
        return validate_image_input(image_input, min_dimension=min_dimension)

    def preprocess(
        self,
        image_input: Union[str, Path, bytes, BinaryIO, Image.Image],
        target_size: Tuple[int, int] = (224, 224),
        to_grayscale: bool = True,
    ) -> PreprocessedImage:
        """Preprocesses image into normalized array representation."""
        return preprocess_image(image_input, target_size=target_size, to_grayscale=to_grayscale)

    def extract_features(
        self,
        image_input: Union[str, Path, bytes, BinaryIO, Image.Image, PreprocessedImage],
    ) -> OtolithFeatureVector:
        """Extracts morphological and statistical feature vector."""
        if isinstance(image_input, PreprocessedImage):
            prep = image_input
        else:
            prep = self.preprocess(image_input)
        return self.feature_extractor.extract(prep)

    def analyze_image(
        self,
        image_input: Union[str, Path, bytes, BinaryIO, Image.Image],
        image_id: str = "otolith_01",
        target_size: Tuple[int, int] = (224, 224),
        persist: bool = True,
    ) -> SpecializedResult:
        """
        Executes end-to-end otolith image analysis:
        1. Validation
        2. Normalization & Preprocessing
        3. Morphological feature extraction
        4. Classification (baseline heuristic or Phase 8 CNN model)
        5. Taxonomy resolution
        6. Storage persistence (if enabled)
        """
        # Step 1: Validation
        val_report = self.validate_image(image_input)
        if not val_report.is_valid:
            ev = ScientificEvidence(
                evidence_id=f"ev-otolith-{image_id}",
                evidence_type=EvidenceType.OTOLITH_IMAGE,
                source_identifier=image_id,
                provenance={"validation_status": "failed"},
            )
            res = SpecializedResult(
                result_id=f"otolith-{image_id}",
                domain="otolith",
                evidence=ev,
                warnings=val_report.errors,
                provenance={"image_id": image_id},
            )
            if persist and self.storage_repo:
                self.storage_repo.save_result(res)
            return res

        # Step 2: Preprocessing
        prep = self.preprocess(image_input, target_size=target_size)

        # Step 3: Feature Extraction
        feature_vec = self.feature_extractor.extract(prep)

        # Step 4: Build Evidence Container
        evidence = ScientificEvidence(
            evidence_id=f"ev-otolith-{image_id}",
            evidence_type=EvidenceType.OTOLITH_IMAGE,
            source_identifier=image_id,
            features=feature_vec.features,
            metrics={
                "aspect_ratio": feature_vec.features.get("aspect_ratio", 0.0),
                "mean_intensity": feature_vec.features.get("mean_intensity", 0.0),
                "contrast_ratio": feature_vec.features.get("contrast_ratio", 0.0),
                "gradient_magnitude": feature_vec.features.get("gradient_magnitude_mean", 0.0),
            },
            provenance={
                "original_dimensions": prep.original_dimensions,
                "target_dimensions": (prep.width, prep.height),
                "format": val_report.format,
            },
        )

        # Step 5: Classification
        class_res = self.classifier.classify(feature_vec)

        # Step 6: Standardization & Taxonomy Integration
        specialized_res = class_res.to_specialized_result(
            image_id=image_id,
            evidence=evidence,
            taxonomy_service=self.taxonomy_service,
        )

        if persist and self.storage_repo:
            self.storage_repo.save_evidence(evidence)
            self.storage_repo.save_result(specialized_res)

        return specialized_res
