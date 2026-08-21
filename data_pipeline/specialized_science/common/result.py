"""
Phase 7 — Result Builder & Normalization Helpers.
Provides utility functions to construct standardized SpecializedResult objects,
determine confidence categories, and format evidence summaries.
"""

from typing import Any, Dict, List, Optional
import uuid

from data_pipeline.specialized_science.common.models import (
    ConfidenceLevel,
    EvidenceType,
    IdentificationStatus,
    ScientificEvidence,
    SpecializedResult,
)


def compute_confidence_level(score: Optional[float]) -> ConfidenceLevel:
    """Classifies a numeric confidence score [0.0, 1.0] into standard categorical levels."""
    if score is None:
        return ConfidenceLevel.UNKNOWN
    if score >= 0.90:
        return ConfidenceLevel.HIGH
    elif score >= 0.70:
        return ConfidenceLevel.MEDIUM
    elif score > 0.0:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.UNKNOWN


def build_specialized_result(
    domain: str,
    target_entity: Optional[str] = None,
    common_name: Optional[str] = None,
    status: IdentificationStatus = IdentificationStatus.PROVISIONAL,
    confidence_score: Optional[float] = None,
    confidence_method: str = "deterministic_baseline",
    is_ml_prediction: bool = False,
    evidence: Optional[ScientificEvidence] = None,
    alternative_candidates: Optional[List[Dict[str, Any]]] = None,
    taxonomic_hierarchy: Optional[Dict[str, str]] = None,
    provenance: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    result_id: Optional[str] = None,
) -> SpecializedResult:
    """Builds a standardized SpecializedResult instance with auto-computed confidence level."""
    res_id = result_id or str(uuid.uuid4())
    conf_lvl = compute_confidence_level(confidence_score)

    return SpecializedResult(
        result_id=res_id,
        domain=domain,
        target_entity=target_entity,
        common_name=common_name,
        status=status,
        confidence_score=round(confidence_score, 4) if confidence_score is not None else None,
        confidence_level=conf_lvl,
        confidence_method=confidence_method,
        is_ml_prediction=is_ml_prediction,
        evidence=evidence,
        alternative_candidates=alternative_candidates or [],
        taxonomic_hierarchy=taxonomic_hierarchy,
        provenance=provenance or {},
        warnings=warnings or [],
        metadata=metadata or {},
    )
