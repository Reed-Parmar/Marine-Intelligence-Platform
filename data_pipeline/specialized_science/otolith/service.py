"""
Phase 7 — Otolith / Marine Image Analysis Service.
Main orchestrator for otolith and marine image processing: validation, preprocessing,
morphological feature extraction, classification, and persistence.
"""

from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union
from PIL import Image

from data_pipeline.specialized_science.common.models import (
    ConfidenceLevel,
    EvidenceType,
    IdentificationStatus,
    InMemoryStorageRepository,
    ScientificEvidence,
    SpecializedResult,
    StorageRepository,
    TaxonResolverProtocol,
)
from data_pipeline.specialized_science.common.result import build_specialized_result
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
        taxonomy_service: Optional[TaxonResolverProtocol] = None,
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
        feature_extractor: Optional[ImageFeatureExtractor] = None,
    ) -> OtolithFeatureVector:
        """Extracts morphological and statistical feature vector."""
        extractor = feature_extractor or self.feature_extractor
        if isinstance(image_input, PreprocessedImage):
            prep = image_input
        else:
            prep = self.preprocess(image_input)
        return extractor.extract(prep)

    def analyze_image(
        self,
        image_input: Union[str, Path, bytes, BinaryIO, Image.Image],
        image_id: str = "otolith_01",
        target_size: Tuple[int, int] = (224, 224),
        classifier: Optional[OtolithClassifier] = None,
        feature_extractor: Optional[ImageFeatureExtractor] = None,
        taxonomy_service: Optional[TaxonResolverProtocol] = None,
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
        active_classifier = classifier or self.classifier
        active_extractor = feature_extractor or self.feature_extractor
        active_tax = taxonomy_service or self.taxonomy_service

        # Step 1: Validation
        val_report = self.validate_image(image_input)
        if not val_report.is_valid:
            ev = ScientificEvidence(
                evidence_id=f"ev-otolith-{image_id}",
                evidence_type=EvidenceType.OTOLITH_IMAGE,
                source_identifier=image_id,
                provenance={"validation_status": "failed"},
            )
            res = build_specialized_result(
                result_id=f"otolith-{image_id}",
                domain="otolith",
                status=IdentificationStatus.REJECTED,
                confidence_score=0.0,
                confidence_method="validation_failure",
                is_ml_prediction=False,
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
        feature_vec = active_extractor.extract(prep)

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
        class_res = active_classifier.classify(feature_vec)

        # Step 6: Standardization & Taxonomy Integration
        specialized_res = class_res.to_specialized_result(
            image_id=image_id,
            evidence=evidence,
            taxonomy_service=active_tax,
        )

        if persist and self.storage_repo:
            self.storage_repo.save_evidence(evidence)
            self.storage_repo.save_result(specialized_res)

        return specialized_res
