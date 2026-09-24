"""
Species, taxonomy, occurrence, and distribution schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TaxonomyInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = Field(default=None, alias="class")
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None


class SpeciesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    taxonomy_id: Optional[str] = None
    scientific_name: str
    common_name: Optional[str] = None
    worms_aphia_id: Optional[int] = None
    iucn_red_list_status: Optional[str] = None
    commercial_importance: Optional[str] = None
    habitat_type: Optional[str] = None
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = Field(default=None, alias="class")
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SpeciesOccurrenceResponse(BaseModel):
    id: str
    dataset_id: Optional[str] = None
    species_id: str
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    latitude: float
    longitude: float
    depth: Optional[float] = None
    observed_at: Optional[str] = None
    individual_count: Optional[int] = None
    basis_of_record: Optional[str] = None
    recorded_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SpeciesDistributionResponse(BaseModel):
    species_id: str
    occurrence_count: int
    min_latitude: Optional[float] = None
    max_latitude: Optional[float] = None
    min_longitude: Optional[float] = None
    max_longitude: Optional[float] = None
    min_depth: Optional[float] = None
    max_depth: Optional[float] = None
