"""
Phase 5 — Data Fusion & Unified Marine Data.
Provides cross-domain observation querying, spatial/temporal/depth alignment,
and unified marine data services for the CMLRE Marine Intelligence Platform.
"""

from data_pipeline.fusion.models import (
    CrossDomainAssociation,
    DomainType,
    MarineObservation,
    UnifiedQueryParams,
    UnifiedSummary,
)
from data_pipeline.fusion.query_service import (
    get_cross_domain_context,
    get_domain_observations,
    get_unified_summary,
    query_unified_observations,
)

__all__ = [
    "DomainType",
    "MarineObservation",
    "UnifiedQueryParams",
    "CrossDomainAssociation",
    "UnifiedSummary",
    "query_unified_observations",
    "get_domain_observations",
    "get_unified_summary",
    "get_cross_domain_context",
]
