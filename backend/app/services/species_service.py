"""
Species Service: Taxonomy search, species profiles, occurrences, and spatial distribution.
Uses SQLAlchemy parameterized queries.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.database import execute_query, execute_single
from backend.app.db.queries import (
    COUNT_SEARCH_SPECIES,
    COUNT_SPECIES_OCCURRENCES,
    GET_SPECIES_BY_ID,
    GET_SPECIES_DISTRIBUTION,
    GET_SPECIES_OCCURRENCES,
    SEARCH_SPECIES
)
from backend.app.schemas.species import (
    SpeciesDistributionResponse,
    SpeciesOccurrenceResponse,
    SpeciesResponse
)


class SpeciesService:

    @staticmethod
    def search_species(
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SpeciesResponse], int]:
        """Searches or lists species from taxonomy and species catalog."""
        search_param = search if search else None
        search_like = f"%{search}%" if search else None
        offset = (page - 1) * page_size
        
        params = {
            "search": search_param,
            "search_like": search_like,
            "limit": page_size,
            "offset": offset
        }
        count_res = execute_single(COUNT_SEARCH_SPECIES, {"search": search_param, "search_like": search_like})
        total = count_res["total"] if count_res else 0

        rows = execute_query(SEARCH_SPECIES, params)

        species_list = [
            SpeciesResponse(
                id=str(r["id"]),
                taxonomy_id=str(r["taxonomy_id"]) if r.get("taxonomy_id") else None,
                scientific_name=r["scientific_name"],
                common_name=r.get("common_name"),
                worms_aphia_id=r.get("worms_aphia_id"),
                iucn_red_list_status=r.get("iucn_red_list_status"),
                commercial_importance=r.get("commercial_importance"),
                habitat_type=r.get("habitat_type"),
                kingdom=r.get("kingdom"),
                phylum=r.get("phylum"),
                class_name=r.get("class"),
                order=r.get("order"),
                family=r.get("family"),
                genus=r.get("genus"),
                metadata=r.get("metadata")
            )
            for r in rows
        ]
        return species_list, total

    @staticmethod
    def get_species_by_id(species_id: str) -> Optional[SpeciesResponse]:
        """Retrieves full taxonomy and biological profile for one species."""
        r = execute_single(GET_SPECIES_BY_ID, {"species_id": species_id})
        if not r:
            return None
        return SpeciesResponse(
            id=str(r["id"]),
            taxonomy_id=str(r["taxonomy_id"]) if r.get("taxonomy_id") else None,
            scientific_name=r["scientific_name"],
            common_name=r.get("common_name"),
            worms_aphia_id=r.get("worms_aphia_id"),
            iucn_red_list_status=r.get("iucn_red_list_status"),
            commercial_importance=r.get("commercial_importance"),
            habitat_type=r.get("habitat_type"),
            kingdom=r.get("kingdom"),
            phylum=r.get("phylum"),
            class_name=r.get("class"),
            order=r.get("order"),
            family=r.get("family"),
            genus=r.get("genus"),
            metadata=r.get("metadata")
        )

    @staticmethod
    def get_species_occurrences(
        species_id: str,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[SpeciesOccurrenceResponse], int]:
        """Lists spatial/temporal occurrences for a species."""
        offset = (page - 1) * page_size
        count_res = execute_single(COUNT_SPECIES_OCCURRENCES, {"species_id": species_id})
        total = count_res["total"] if count_res else 0

        params = {"species_id": species_id, "limit": page_size, "offset": offset}
        rows = execute_query(GET_SPECIES_OCCURRENCES, params)

        occurrences = [
            SpeciesOccurrenceResponse(
                id=str(r["id"]),
                dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
                species_id=str(r["species_id"]),
                scientific_name=r.get("scientific_name"),
                common_name=r.get("common_name"),
                latitude=float(r["latitude"]),
                longitude=float(r["longitude"]),
                depth=float(r["depth"]) if r.get("depth") is not None else None,
                observed_at=str(r["observed_at"]) if r.get("observed_at") else None,
                individual_count=r.get("individual_count"),
                basis_of_record=r.get("basis_of_record"),
                recorded_by=r.get("recorded_by"),
                metadata=r.get("metadata")
            )
            for r in rows
        ]
        return occurrences, total

    @staticmethod
    def get_species_distribution(species_id: str) -> Optional[SpeciesDistributionResponse]:
        """Calculates bounding box and occurrence stats for map visualization."""
        r = execute_single(GET_SPECIES_DISTRIBUTION, {"species_id": species_id})
        if not r:
            return None
        return SpeciesDistributionResponse(
            species_id=str(r["species_id"]),
            occurrence_count=r.get("occurrence_count", 0),
            min_latitude=float(r["min_latitude"]) if r.get("min_latitude") is not None else None,
            max_latitude=float(r["max_latitude"]) if r.get("max_latitude") is not None else None,
            min_longitude=float(r["min_longitude"]) if r.get("min_longitude") is not None else None,
            max_longitude=float(r["max_longitude"]) if r.get("max_longitude") is not None else None,
            min_depth=float(r["min_depth"]) if r.get("min_depth") is not None else None,
            max_depth=float(r["max_depth"]) if r.get("max_depth") is not None else None
        )
