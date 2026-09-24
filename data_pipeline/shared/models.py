"""
Shared domain models and enumerations for CMLRE Marine Intelligence Platform.
Used across ingestion, quality control, data fusion, and API layers.
"""

from enum import Enum


class DomainType(str, Enum):
    """Marine science domains supported by the platform."""
    OCEANOGRAPHY = "oceanography"
    FISHERIES = "fisheries"
    BIODIVERSITY = "biodiversity"
    EDNA = "edna"
    MOLECULAR_EDNA = "molecular_edna"
    OTOLITH = "otolith"
    GENERAL = "general"

