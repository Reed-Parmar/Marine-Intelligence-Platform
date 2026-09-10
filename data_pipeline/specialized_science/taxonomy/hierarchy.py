"""
Phase 7 — Taxonomic Hierarchy and Data Representation.
Models multi-level biological classifications from Kingdom down to Species.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaxonomicRank(str, Enum):
    """Standard biological classification ranks."""
    KINGDOM = "kingdom"
    PHYLUM = "phylum"
    CLASS = "class"
    ORDER = "order"
    FAMILY = "family"
    GENUS = "genus"
    SPECIES = "species"
    SUBSPECIES = "subspecies"
    UNRANKED = "unranked"


@dataclass
class TaxonHierarchy:
    """Encapsulates the 7-level Linnaean taxonomic lineage."""
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    class_name: Optional[str] = None # Using class_name to avoid Python keyword collision
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "kingdom": self.kingdom,
            "phylum": self.phylum,
            "class": self.class_name,
            "order": self.order,
            "family": self.family,
            "genus": self.genus,
            "species": self.species,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaxonHierarchy":
        return cls(
            kingdom=data.get("kingdom"),
            phylum=data.get("phylum"),
            class_name=data.get("class_name") or data.get("class"),
            order=data.get("order"),
            family=data.get("family"),
            genus=data.get("genus"),
            species=data.get("species"),
        )


@dataclass
class TaxonRecord:
    """Comprehensive representation of a validated marine taxonomic entity."""
    taxon_id: str
    scientific_name: str
    common_names: List[str] = field(default_factory=list)
    rank: TaxonomicRank = TaxonomicRank.SPECIES
    hierarchy: Optional[TaxonHierarchy] = None
    is_accepted: bool = True
    accepted_name: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    worms_id: Optional[int] = None
    cmlre_tax_id: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["rank"] = self.rank.value if hasattr(self.rank, "value") else str(self.rank)
        if self.hierarchy:
            res["hierarchy"] = self.hierarchy.to_dict()
        return res
