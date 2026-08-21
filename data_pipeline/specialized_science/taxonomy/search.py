"""
Phase 7 — Taxonomic Search Engine.
Provides exact, common-name, and partial/prefix search over registered marine taxonomy records.
"""

from typing import Dict, List, Optional
from data_pipeline.specialized_science.taxonomy.hierarchy import TaxonRecord


class TaxonomySearchEngine:
    """
    In-memory indexed search engine for marine taxonomic records.
    Supports exact scientific name matching, common name lookups, and partial queries.
    """

    def __init__(self, records: Optional[List[TaxonRecord]] = None) -> None:
        self._records_by_id: Dict[str, TaxonRecord] = {}
        self._records_by_sci_name: Dict[str, TaxonRecord] = {}
        self._records_by_common_name: Dict[str, List[TaxonRecord]] = {}

        if records:
            for r in records:
                self.index_record(r)

    def index_record(self, record: TaxonRecord) -> None:
        """Indexes a TaxonRecord into search lookups."""
        self._records_by_id[record.taxon_id] = record
        self._records_by_sci_name[record.scientific_name.strip().lower()] = record

        for c_name in record.common_names:
            c_clean = c_name.strip().lower()
            if c_clean not in self._records_by_common_name:
                self._records_by_common_name[c_clean] = []
            self._records_by_common_name[c_clean].append(record)

    def search_exact(self, scientific_name: str) -> Optional[TaxonRecord]:
        """Searches by exact scientific name (case-insensitive)."""
        if not scientific_name:
            return None
        return self._records_by_sci_name.get(scientific_name.strip().lower())

    def search_common_name(self, common_name: str) -> List[TaxonRecord]:
        """Searches by exact common name (case-insensitive)."""
        if not common_name:
            return []
        return self._records_by_common_name.get(common_name.strip().lower(), [])

    def search_partial(self, query: str, limit: int = 10) -> List[TaxonRecord]:
        """Searches across scientific and common names using substring containment."""
        if not query:
            return []
        q = query.strip().lower()
        results: List[TaxonRecord] = []
        seen_ids = set()

        # 1. Scientific name starts with / contains query
        for sci_lower, rec in self._records_by_sci_name.items():
            if q in sci_lower:
                results.append(rec)
                seen_ids.add(rec.taxon_id)
                if len(results) >= limit:
                    return results

        # 2. Common names contain query
        for com_lower, recs in self._records_by_common_name.items():
            if q in com_lower:
                for r in recs:
                    if r.taxon_id not in seen_ids:
                        results.append(r)
                        seen_ids.add(r.taxon_id)
                        if len(results) >= limit:
                            return results

        return results
