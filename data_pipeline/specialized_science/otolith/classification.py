"""
Phase 7 — Otolith Classification & Baseline Heuristic Engine.
Provides a clean classifier Protocol and an explicit baseline implementation,
designed for seamless drop-in replacement by Phase 8 CNN/ML models.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from data_pipeline.specialized_science.common.models import (
    ConfidenceLevel,
    EvidenceType,
    IdentificationStatus,
    ScientificEvidence,
    SpecializedResult,
    TaxonResolverProtocol,
)
from data_pipeline.specialized_science.common.result import (
    build_specialized_result,
    compute_confidence_level,
)
from data_pipeline.specialized_science.otolith.features import OtolithFeatureVector


@dataclass
class OtolithClassificationResult:
    """Structured prediction output from an otolith classifier."""
    predicted_species: Optional[str] = None
    predicted_age_years: Optional[int] = None
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    status: IdentificationStatus = IdentificationStatus.PROVISIONAL
    classifier_name: str = "heuristic_baseline_v1"
    is_ml_model: bool = False
    candidate_scores: Dict[str, float] = field(default_factory=dict)
    features_used: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_specialized_result(
        self,
        image_id: str,
        evidence: Optional[ScientificEvidence] = None,
        taxonomy_service: Optional[TaxonResolverProtocol] = None,
    ) -> SpecializedResult:
        """Converts classification output into the standard platform SpecializedResult."""
        common_name = None
        hierarchy = None
        warnings = list(self.warnings)

        if self.predicted_species and taxonomy_service:
            tax_res = taxonomy_service.resolve_taxon(self.predicted_species)
            if tax_res.is_resolved:
                common_name = tax_res.common_name
                if tax_res.hierarchy:
                    hierarchy = tax_res.hierarchy.to_dict()
                if tax_res.warnings:
                    warnings.extend(tax_res.warnings)

        alt_candidates = [
            {"candidate": k, "score": v}
            for k, v in sorted(self.candidate_scores.items(), key=lambda x: x[1], reverse=True)
            if k != self.predicted_species
        ]

        return build_specialized_result(
            result_id=f"otolith-{image_id}",
            domain="otolith",
            target_entity=self.predicted_species,
            common_name=common_name,
            status=self.status,
            confidence_score=self.confidence_score,
            confidence_method=f"morphological_{self.classifier_name}",
            is_ml_prediction=self.is_ml_model,
            evidence=evidence,
            alternative_candidates=alt_candidates,
            taxonomic_hierarchy=hierarchy,
            provenance={"classifier": self.classifier_name, "is_ml_model": self.is_ml_model},
            warnings=warnings,
            metadata={
                "predicted_age_years": self.predicted_age_years,
                "candidate_scores": self.candidate_scores,
                "notice": "Baseline heuristic classification; Phase 8 can inject trained CNN model.",
            },
        )


class OtolithClassifier(Protocol):
    """
    Standard classifier protocol for otolith images.
    Phase 8 can implement this protocol to run trained PyTorch/ONNX/TensorFlow models.
    """
    def classify(self, feature_vector: OtolithFeatureVector) -> OtolithClassificationResult:
        ...


class BaselineOtolithClassifier:
    """
    Deterministic rule-based baseline classifier.
    
    IMPORTANT: This is a placeholder heuristic establishing the interface contract.
    It does not claim to be a trained machine learning model.
    """

    def __init__(self) -> None:
        self.classifier_name = "heuristic_baseline_v1"
        self.is_ml_model = False

    def classify(self, feature_vector: OtolithFeatureVector) -> OtolithClassificationResult:
        feats = feature_vector.features
        ar = feats.get("aspect_ratio", 1.0)
        mean_int = feats.get("mean_intensity", 0.5)
        contrast = feats.get("contrast_ratio", 0.5)

        warnings = [
            "Classification generated using heuristic morphological baseline (non-ML). "
            "Production otolith age/species estimation requires trained Phase 8 CNN weights."
        ]

        # Heuristic rules based on teleost otolith morphometrics:
        # Elongated sagittae (high AR > 1.8) -> Scombridae / Pelagics (Rastrelliger / Thunnus)
        # Oval/Elliptical sagittae (1.3 <= AR <= 1.8) -> Nemipteridae (Nemipterus japonicus)
        # Compact/Rounded sagittae (AR < 1.3) -> Serranidae / Clupeidae (Epinephelus / Sardinella)
        scores: Dict[str, float] = {}

        if ar > 1.8:
            scores["Rastrelliger kanagurta"] = 0.72
            scores["Thunnus albacares"] = 0.65
            scores["Nemipterus japonicus"] = 0.40
            top_species = "Rastrelliger kanagurta"
            top_score = 0.72
            est_age = 2
        elif ar >= 1.3:
            scores["Nemipterus japonicus"] = 0.75
            scores["Epinephelus diacanthus"] = 0.60
            scores["Rastrelliger kanagurta"] = 0.45
            top_species = "Nemipterus japonicus"
            top_score = 0.75
            est_age = 3
        else:
            scores["Epinephelus diacanthus"] = 0.70
            scores["Sardinella longiceps"] = 0.62
            scores["Nemipterus japonicus"] = 0.40
            top_species = "Epinephelus diacanthus"
            top_score = 0.70
            est_age = 4

        conf_lvl = compute_confidence_level(top_score)

        return OtolithClassificationResult(
            predicted_species=top_species,
            predicted_age_years=est_age,
            confidence_score=top_score,
            confidence_level=conf_lvl,
            status=IdentificationStatus.PROVISIONAL,
            classifier_name=self.classifier_name,
            is_ml_model=False,
            candidate_scores=scores,
            features_used=list(feats.keys()),
            warnings=warnings,
            metadata={"rule_applied": f"aspect_ratio_{ar:.2f}_intensity_{mean_int:.2f}"},
        )
