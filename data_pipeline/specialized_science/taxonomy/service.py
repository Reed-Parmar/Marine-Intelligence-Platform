"""
Phase 7 — Taxonomy Service.
Provides multi-criteria search, taxonomic hierarchy retrieval, synonym resolution,
and candidate taxon identification for eDNA and image workflows.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data_pipeline.specialized_science.common.models import (
    ConfidenceLevel,
    IdentificationStatus,
    ScientificEvidence,
    SpecializedResult,
)
from data_pipeline.specialized_science.common.result import (
    build_specialized_result,
    compute_confidence_level,
)
from data_pipeline.specialized_science.taxonomy.hierarchy import (
    TaxonHierarchy,
    TaxonomicRank,
    TaxonRecord,
)
from data_pipeline.specialized_science.taxonomy.search import TaxonomySearchEngine
from data_pipeline.specialized_science.taxonomy.synonyms import SynonymResolver


@dataclass
class TaxonResolutionResult:
    """Detailed outcome of resolving a candidate taxon name."""
    candidate_name: str
    is_resolved: bool
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    rank: Optional[str] = None
    is_synonym: bool = False
    original_input: Optional[str] = None
    status: IdentificationStatus = IdentificationStatus.PROVISIONAL
    confidence_score: float = 0.0
    hierarchy: Optional[TaxonHierarchy] = None
    synonyms: List[str] = field(default_factory=list)
    record: Optional[TaxonRecord] = None
    warnings: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_name": self.candidate_name,
            "is_resolved": self.is_resolved,
            "scientific_name": self.scientific_name,
            "common_name": self.common_name,
            "rank": self.rank,
            "is_synonym": self.is_synonym,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "confidence_score": self.confidence_score,
            "hierarchy": self.hierarchy.to_dict() if self.hierarchy else None,
            "synonyms": self.synonyms,
            "warnings": self.warnings,
            "provenance": self.provenance,
        }


# Curated baseline taxonomic reference dataset for Indian Ocean marine fauna & flora
DEFAULT_TAXONOMY_RECORDS: List[TaxonRecord] = [
    TaxonRecord(
        taxon_id="TAX-001",
        scientific_name="Rastrelliger kanagurta",
        common_names=["Indian Mackerel", "Ayala", "Bangda"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Scombriformes",
            family="Scombridae",
            genus="Rastrelliger",
            species="Rastrelliger kanagurta",
        ),
        synonyms=["Scomber kanagurta", "Scomber loo"],
        worms_id=219717,
        cmlre_tax_id="CMLRE-FISH-001",
    ),
    TaxonRecord(
        taxon_id="TAX-002",
        scientific_name="Sardinella longiceps",
        common_names=["Indian Oil Sardine", "Mathi", "Tarli"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Clupeiformes",
            family="Clupeidae",
            genus="Sardinella",
            species="Sardinella longiceps",
        ),
        synonyms=["Clupea longiceps", "Sardinella neohowii"],
        worms_id=217387,
        cmlre_tax_id="CMLRE-FISH-002",
    ),
    TaxonRecord(
        taxon_id="TAX-003",
        scientific_name="Nemipterus japonicus",
        common_names=["Japanese Threadfin Bream", "Pink Perch", "Kilimeen"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Perciformes",
            family="Nemipteridae",
            genus="Nemipterus",
            species="Nemipterus japonicus",
        ),
        synonyms=["Sparus japonicus", "Dentex blochii"],
        worms_id=218567,
        cmlre_tax_id="CMLRE-FISH-003",
    ),
    TaxonRecord(
        taxon_id="TAX-004",
        scientific_name="Epinephelus diacanthus",
        common_names=["Thornycheek Grouper", "Six-bar Grouper", "Kalava"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Perciformes",
            family="Serranidae",
            genus="Epinephelus",
            species="Epinephelus diacanthus",
        ),
        synonyms=["Serranus diacanthus"],
        worms_id=218206,
        cmlre_tax_id="CMLRE-FISH-004",
    ),
    TaxonRecord(
        taxon_id="TAX-005",
        scientific_name="Thunnus albacares",
        common_names=["Yellowfin Tuna", "Kera"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Scombriformes",
            family="Scombridae",
            genus="Thunnus",
            species="Thunnus albacares",
        ),
        synonyms=["Scomber albacares", "Neothunnus macropterus", "Thunnus macropterus"],
        worms_id=127027,
        cmlre_tax_id="CMLRE-FISH-005",
    ),
    TaxonRecord(
        taxon_id="TAX-006",
        scientific_name="Penaeus monodon",
        common_names=["Giant Tiger Prawn", "Black Tiger Shrimp", "Kara Chemmeen"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Arthropoda",
            class_name="Malacostraca",
            order="Decapoda",
            family="Penaeidae",
            genus="Penaeus",
            species="Penaeus monodon",
        ),
        synonyms=["Penaeus carinatus", "Palaemon carinatus"],
        worms_id=210379,
        cmlre_tax_id="CMLRE-CRUST-001",
    ),
    TaxonRecord(
        taxon_id="TAX-007",
        scientific_name="Acropora formosa",
        common_names=["Staghorn Coral"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Cnidaria",
            class_name="Anthozoa",
            order="Scleractinia",
            family="Acroporidae",
            genus="Acropora",
            species="Acropora formosa",
        ),
        synonyms=["Madrepora formosa", "Acropora muricata"],
        worms_id=207011,
        cmlre_tax_id="CMLRE-CORAL-001",
    ),
    TaxonRecord(
        taxon_id="TAX-008",
        scientific_name="Balaenoptera musculus",
        common_names=["Blue Whale"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Mammalia",
            order="Cetartiodactyla",
            family="Balaenopteridae",
            genus="Balaenoptera",
            species="Balaenoptera musculus",
        ),
        synonyms=["Physalus musculus"],
        worms_id=137088,
        cmlre_tax_id="CMLRE-MAM-001",
    ),
    TaxonRecord(
        taxon_id="TAX-009",
        scientific_name="Larus michahellis",
        common_names=["Yellow-legged Gull"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Aves",
            order="Charadriiformes",
            family="Laridae",
            genus="Larus",
            species="Larus michahellis",
        ),
        synonyms=["Larus argentatus michahellis"],
        worms_id=148783,
        cmlre_tax_id="CMLRE-BIRD-001",
    ),
    TaxonRecord(
        taxon_id="TAX-010",
        scientific_name="Oryzias latipes",
        common_names=["Japanese Rice Fish", "Medaka"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Beloniformes",
            family="Adrianichthyidae",
            genus="Oryzias",
            species="Oryzias latipes",
        ),
        synonyms=["Poecilia latipes"],
        worms_id=278065,
        cmlre_tax_id="CMLRE-FISH-010",
    ),
    TaxonRecord(
        taxon_id="TAX-011",
        scientific_name="Echinopora horrida",
        common_names=["Hedgehog Coral"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Cnidaria",
            class_name="Anthozoa",
            order="Scleractinia",
            family="Merulinidae",
            genus="Echinopora",
            species="Echinopora horrida",
        ),
        synonyms=[],
        worms_id=207432,
        cmlre_tax_id="CMLRE-CORAL-002",
    ),
    TaxonRecord(
        taxon_id="TAX-012",
        scientific_name="Pungitius pungitius",
        common_names=["Ninespine Stickleback"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Chordata",
            class_name="Actinopterygii",
            order="Gasterosteiformes",
            family="Gasterosteidae",
            genus="Pungitius",
            species="Pungitius pungitius",
        ),
        synonyms=["Gasterosteus pungitius"],
        worms_id=126508,
        cmlre_tax_id="CMLRE-FISH-012",
    ),
    TaxonRecord(
        taxon_id="TAX-013",
        scientific_name="Cyprideis torosa",
        common_names=["Lagoon Ostracod"],
        rank=TaxonomicRank.SPECIES,
        hierarchy=TaxonHierarchy(
            kingdom="Animalia",
            phylum="Arthropoda",
            class_name="Ostracoda",
            order="Podocopida",
            family="Cytherideidae",
            genus="Cyprideis",
            species="Cyprideis torosa",
        ),
        synonyms=[],
        worms_id=128286,
        cmlre_tax_id="CMLRE-CRUST-002",
    ),
]


class TaxonomyService:
    """
    Main Taxonomy Service orchestrator.
    Handles multi-rank hierarchy retrieval, synonym mapping, and taxon resolution.
    """

    def __init__(self, records: Optional[List[TaxonRecord]] = None) -> None:
        initial_records = records or DEFAULT_TAXONOMY_RECORDS
        self._search_engine = TaxonomySearchEngine(initial_records)
        self._synonym_resolver = SynonymResolver()

        # Populate synonym resolver from records
        for r in initial_records:
            for syn in r.synonyms:
                self._synonym_resolver.register_synonym(syn, r.scientific_name)

    def add_taxon(self, record: TaxonRecord) -> None:
        """Dynamically registers a new taxon record."""
        self._search_engine.index_record(record)
        for syn in record.synonyms:
            self._synonym_resolver.register_synonym(syn, record.scientific_name)

    def search(self, query: str, mode: str = "auto", limit: int = 10) -> List[TaxonRecord]:
        """
        Searches taxonomic records by scientific name, common name, or partial query.

        Args:
            query: Name query string.
            mode: 'exact', 'common', 'partial', or 'auto'.
            limit: Maximum result items.
        """
        if not query:
            return []

        q = query.strip()
        if mode == "exact":
            rec = self._search_engine.search_exact(q)
            return [rec] if rec else []
        elif mode == "common":
            return self._search_engine.search_common_name(q)
        elif mode == "partial":
            return self._search_engine.search_partial(q, limit=limit)
        else: # auto
            exact = self._search_engine.search_exact(q)
            if exact:
                return [exact]
            common_matches = self._search_engine.search_common_name(q)
            if common_matches:
                return common_matches
            # Check synonym
            resolved_name, is_syn, _ = self._synonym_resolver.resolve(q)
            if is_syn:
                syn_match = self._search_engine.search_exact(resolved_name)
                if syn_match:
                    return [syn_match]
            return self._search_engine.search_partial(q, limit=limit)

    def get_hierarchy(self, taxon_name: str) -> Optional[TaxonHierarchy]:
        """Retrieves full taxonomic hierarchy for a given taxon name."""
        records = self.search(taxon_name, mode="auto")
        if records and records[0].hierarchy:
            return records[0].hierarchy
        return None

    def resolve_taxon(self, candidate_name: str) -> TaxonResolutionResult:
        """
        Resolves a candidate taxon string into a validated canonical taxon record.

        Returns structured TaxonResolutionResult with confidence, accepted name, and hierarchy.
        """
        if not candidate_name or not candidate_name.strip():
            return TaxonResolutionResult(
                candidate_name=str(candidate_name),
                is_resolved=False,
                status=IdentificationStatus.UNRESOLVED,
                confidence_score=0.0,
                warnings=["Empty or blank taxon candidate provided."],
            )

        cleaned = candidate_name.strip()
        warnings: List[str] = []

        # Step 1: Check synonyms
        target_name, is_syn, orig_syn = self._synonym_resolver.resolve(cleaned)
        if is_syn:
            warnings.append(f"Input '{cleaned}' is a synonym for accepted name '{target_name}'.")

        # Step 2: Search exact record
        record = self._search_engine.search_exact(target_name)

        if record:
            c_name = record.common_names[0] if record.common_names else None
            conf = 0.95 if not is_syn else 0.90
            status = IdentificationStatus.CONFIRMED

            return TaxonResolutionResult(
                candidate_name=cleaned,
                is_resolved=True,
                scientific_name=record.scientific_name,
                common_name=c_name,
                rank=record.rank.value if hasattr(record.rank, "value") else str(record.rank),
                is_synonym=is_syn,
                original_input=cleaned if is_syn else None,
                status=status,
                confidence_score=conf,
                hierarchy=record.hierarchy,
                synonyms=record.synonyms,
                record=record,
                warnings=warnings,
                provenance={"source_authority": "CMLRE Reference Taxonomy", "worms_id": record.worms_id},
            )

        # Step 3: Partial search fallback
        partial_matches = self._search_engine.search_partial(cleaned, limit=3)
        if partial_matches:
            top = partial_matches[0]
            warnings.append(f"Exact match not found; resolved via partial match to '{top.scientific_name}'.")
            return TaxonResolutionResult(
                candidate_name=cleaned,
                is_resolved=True,
                scientific_name=top.scientific_name,
                common_name=top.common_names[0] if top.common_names else None,
                rank=top.rank.value if hasattr(top.rank, "value") else str(top.rank),
                is_synonym=False,
                status=IdentificationStatus.PROVISIONAL,
                confidence_score=0.75,
                hierarchy=top.hierarchy,
                synonyms=top.synonyms,
                record=top,
                warnings=warnings,
                provenance={"source_authority": "CMLRE Partial Match", "candidate_count": len(partial_matches)},
            )

        # Unresolved
        return TaxonResolutionResult(
            candidate_name=cleaned,
            is_resolved=False,
            status=IdentificationStatus.UNRESOLVED,
            confidence_score=0.0,
            warnings=[f"Taxon '{cleaned}' could not be resolved in the reference database."],
        )
