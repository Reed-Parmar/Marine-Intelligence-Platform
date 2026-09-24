import math
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
    if score is None or not isinstance(score, (int, float)) or not math.isfinite(score):
        return ConfidenceLevel.UNKNOWN
    if score < 0.0 or score > 1.0:
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
    """Builds a standardized SpecializedResult instance with validated and rounded confidence level."""
    res_id = result_id or str(uuid.uuid4())
    valid_warnings = list(warnings or [])

    stored_score: Optional[float] = None
    if confidence_score is not None:
        if isinstance(confidence_score, (int, float)) and math.isfinite(confidence_score) and 0.0 <= confidence_score <= 1.0:
            stored_score = round(float(confidence_score), 4)
        else:
            valid_warnings.append(f"Invalid confidence score ({confidence_score}) rejected; reset to None.")

    conf_lvl = compute_confidence_level(stored_score)

    return SpecializedResult(
        result_id=res_id,
        domain=domain,
        target_entity=target_entity,
        common_name=common_name,
        status=status,
        confidence_score=stored_score,
        confidence_level=conf_lvl,
        confidence_method=confidence_method,
        is_ml_prediction=is_ml_prediction,
        evidence=evidence,
        alternative_candidates=alternative_candidates or [],
        taxonomic_hierarchy=taxonomic_hierarchy,
        provenance=provenance or {},
        warnings=valid_warnings,
        metadata=metadata or {},
    )
