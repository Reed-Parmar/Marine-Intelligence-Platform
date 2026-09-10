"""
Marine Service: Cross-domain unified marine observation aggregation and spatial querying.
Uses SQLAlchemy parameterized queries.
"""

from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.database import execute_query, execute_single
from backend.app.db.queries import (
    COUNT_UNIFIED_MARINE_OBSERVATIONS,
    GET_MARINE_SUMMARY,
    GET_UNIFIED_MARINE_OBSERVATIONS
)
from backend.app.schemas.marine import (
    CrossDomainLocationDetailResponse,
    MarineObservationItem,
    MarineQueryRequest,
    MarineSummaryResponse
)


class MarineService:

    @staticmethod
    def get_unified_observations(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        dataset_id: Optional[str] = None,
        species_id: Optional[str] = None,
        depth_min: Optional[float] = None,
        depth_max: Optional[float] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[MarineObservationItem], int]:
        """
        Retrieves unified observations across oceanography, fisheries, and biodiversity domains.
        Executes a matching COUNT query to return the true total.
        """
        offset = (page - 1) * page_size
        params = {
            "date_from": date_from,
            "date_to": date_to,
            "dataset_id": dataset_id,
            "species_id": species_id,
            "depth_min": depth_min,
            "depth_max": depth_max,
            "limit": page_size,
            "offset": offset
        }
        
        count_res = execute_single(COUNT_UNIFIED_MARINE_OBSERVATIONS, params)
        total = count_res["total"] if count_res else 0

        rows = execute_query(GET_UNIFIED_MARINE_OBSERVATIONS, params)
        
        items = [
            MarineObservationItem(
                id=str(r["id"]),
                domain=r["domain"],
                dataset_id=str(r["dataset_id"]) if r.get("dataset_id") else None,
                latitude=float(r["latitude"]),
                longitude=float(r["longitude"]),
                depth=float(r["depth"]) if r.get("depth") is not None else None,
                time=str(r["time"]) if r.get("time") else None,
                species_id=str(r["species_id"]) if r.get("species_id") else None,
                species_name=r.get("species_name"),
                measurements=r.get("measurements") or {}
            )
            for r in rows
        ]
        return items, total

    @staticmethod
    def get_marine_summary() -> MarineSummaryResponse:
        """Retrieves aggregate platform summary across all domains."""
        r = execute_single(GET_MARINE_SUMMARY)
        if not r:
            return MarineSummaryResponse(
                total_datasets=0,
                oceanography_count=0,
                fisheries_count=0,
                biodiversity_count=0,
                edna_count=0,
                total_species=0
            )
        return MarineSummaryResponse(
            total_datasets=r.get("total_datasets", 0),
            oceanography_count=r.get("oceanography_count", 0),
            fisheries_count=r.get("fisheries_count", 0),
            biodiversity_count=r.get("biodiversity_count", 0),
            edna_count=r.get("edna_count", 0),
            total_species=r.get("total_species", 0)
        )

    @staticmethod
    def query_marine(req: MarineQueryRequest) -> Tuple[List[MarineObservationItem], int]:
        """
        Executes structured multi-dimensional query across oceanography, fisheries, and occurrences.
        Applies date, dataset, species, and depth constraints.
        """
        return MarineService.get_unified_observations(
            date_from=req.date_from,
            date_to=req.date_to,
            dataset_id=req.dataset_id,
            species_id=req.species_id,
            depth_min=req.depth_min,
            depth_max=req.depth_max,
            page=req.page,
            page_size=req.page_size
        )

    @staticmethod
    def get_location_detail(
        lat: float,
        lon: float,
        radius_km: float = 50.0,
        temporal_window_hours: float = 72.0,
        depth_tolerance_m: float = 50.0
    ) -> CrossDomainLocationDetailResponse:
        """Discovers cross-domain observations and aggregates indicators near coordinates."""
        from data_pipeline.fusion.models import MarineObservation
        from data_pipeline.fusion.query_service import get_cross_domain_context
        from datetime import datetime, timezone

        anchor = MarineObservation(
            latitude=lat,
            longitude=lon,
            observation_time=datetime.now(timezone.utc).isoformat()
        )

        assoc = get_cross_domain_context(
            anchor=anchor,
            spatial_radius_km=radius_km,
            temporal_window_hours=temporal_window_hours,
            depth_tolerance_m=depth_tolerance_m,
            use_db=True
        )

        domain_buckets: Dict[str, list] = {}
        for o in assoc.associated:
            dom_key = o.domain.value if hasattr(o.domain, "value") else str(o.domain)
            domain_buckets.setdefault(dom_key, []).append(o)

        ocean_obs = domain_buckets.get("oceanography", [])
        fish_obs = domain_buckets.get("fisheries", [])
        bio_obs = domain_buckets.get("biodiversity", [])
        edna_obs = domain_buckets.get("edna", [])

        warnings: List[str] = []

        # Oceanography aggregates
        temps = [o.value for o in ocean_obs if o.variable and "temp" in o.variable and o.value is not None]
        salins = [o.value for o in ocean_obs if o.variable and "salin" in o.variable and o.value is not None]
        dos = [o.value for o in ocean_obs if o.variable and "oxygen" in o.variable and o.value is not None]
        chls = [o.value for o in ocean_obs if o.variable and "chlorophyll" in o.variable and o.value is not None]
        depths = [o.depth for o in ocean_obs if o.depth is not None]

        if not ocean_obs:
            warnings.append(f"No oceanography observations found within {radius_km} km.")
            oceanography = {}
        else:
            oceanography = {
                "seaSurfaceTemperature": round(sum(temps) / len(temps), 2) if temps else None,
                "salinity": round(sum(salins) / len(salins), 2) if salins else None,
                "dissolvedOxygen": round(sum(dos) / len(dos), 2) if dos else None,
                "chlorophyllA": round(sum(chls) / len(chls), 2) if chls else None,
                "thermoclineDepth": round(max(depths) * 0.4, 1) if depths else None,
                "mixedLayerDepth": round(min(depths) * 1.5, 1) if depths else None,
                "lastUpdated": datetime.now(timezone.utc).isoformat()
            }

        # Fisheries aggregates
        catches = [o.value for o in fish_obs if o.variable and "catch" in o.variable and o.value is not None]
        fish_species = [o.species_name for o in fish_obs if o.species_name]
        if not fish_obs:
            warnings.append(f"No fisheries records found within {radius_km} km.")
            fisheries = {}
        else:
            fisheries = {
                "dominantCatch": fish_species[0] if fish_species else None,
                "totalLandingsTons": round(sum(catches) / 1000.0, 2) if catches else None,
                "cpueKgPerHour": round(sum(catches) / max(1, len(catches)), 1) if catches else None,
                "dominantGear": None,
                "fishingPressureLevel": None
            }

        # Biodiversity aggregates
        bio_species = list({o.species_name for o in bio_obs if o.species_name})
        if not bio_obs:
            warnings.append(f"No biodiversity occurrences found within {radius_km} km.")
            biodiversity = {}
        else:
            biodiversity = {
                "speciesRecordedCount": len(bio_species) if bio_species else len(bio_obs),
                "keySpeciesPresent": bio_species[:5],
                "shannonWienerIndex": None,
                "endemicSpeciesFlag": None
            }

        # eDNA aggregates
        edna_species = list({o.species_name for o in edna_obs if o.species_name})
        if not edna_obs:
            warnings.append(f"No eDNA samples found within {radius_km} km.")
            molecular_edna = {}
        else:
            molecular_edna = {
                "samplesAnalyzed": len(edna_obs),
                "taxaIdentified": len(edna_species),
                "topDetections": [
                    {"species": sp, "confidence": None, "marker": None} for sp in edna_species[:3]
                ]
            }

        region_name = "Arabian Sea" if lon < 78.0 else ("Bay of Bengal" if lat > 8.0 else "Indian Ocean")

        return CrossDomainLocationDetailResponse(
            coordinates={"latitude": lat, "longitude": lon},
            region=region_name,
            bathymetryDepth=round(max(depths), 1) if depths else None,
            oceanography=oceanography,
            fisheries=fisheries,
            biodiversity=biodiversity,
            molecularEdna=molecular_edna,
            aiPrediction=None,
            associations_summary={dom: len(obs_list) for dom, obs_list in domain_buckets.items()},
            warnings=warnings
        )
