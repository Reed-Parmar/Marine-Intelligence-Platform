"""
Phase 14.2 Marine Species Identification Module.
Computer Vision classifier based on fine-tuned ResNet-18 for 10 reef and pelagic marine species.
"""

from .inference import (
    MarineSpeciesIdentifier,
    get_species_identifier,
    SPECIES_METADATA,
    DEFAULT_MODEL_DIR,
)

__all__ = [
    "MarineSpeciesIdentifier",
    "get_species_identifier",
    "SPECIES_METADATA",
    "DEFAULT_MODEL_DIR",
]
