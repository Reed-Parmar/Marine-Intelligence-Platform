"""
Phase 7 — Taxonomic Synonym Resolution.
Maps historical, alternative, and deprecated taxon names to their accepted canonical names.
"""

from typing import Dict, List, Optional, Tuple


class SynonymResolver:
    """
    Resolves taxonomic synonyms and aliases into canonical accepted names.
    Supports reverse lookups and maintains synonym mapping tables.
    """

    def __init__(self, synonym_map: Optional[Dict[str, str]] = None) -> None:
        # Key: lowercase synonym -> Value: accepted canonical scientific name
        self._synonym_map: Dict[str, str] = {}
        if synonym_map:
            for syn, acc in synonym_map.items():
                self.register_synonym(syn, acc)

    def register_synonym(self, synonym: str, accepted_name: str) -> None:
        """Registers a synonym mapping."""
        if synonym and accepted_name:
            self._synonym_map[synonym.strip().lower()] = accepted_name.strip()

    def resolve(self, candidate_name: str) -> Tuple[str, bool, Optional[str]]:
        """
        Resolves candidate name to accepted name.
        Returns:
            (resolved_accepted_name, is_synonym_flag, original_synonym_if_mapped)
        """
        if not candidate_name:
            return "", False, None

        cleaned = candidate_name.strip()
        cleaned_lower = cleaned.lower()

        if cleaned_lower in self._synonym_map:
            accepted = self._synonym_map[cleaned_lower]
            return accepted, True, cleaned

        return cleaned, False, None

    def get_synonyms_for_accepted(self, accepted_name: str) -> List[str]:
        """Returns all registered synonyms for a given accepted name."""
        acc_clean = accepted_name.strip().lower()
        return [
            syn for syn, acc in self._synonym_map.items()
            if acc.strip().lower() == acc_clean
        ]
