"""
Phase 7 — eDNA Reference Matching.
Provides deterministic baseline reference matching (exact and k-mer similarity)
with extensible Protocol interfaces for Phase 8 AI/BLAST integration.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple


@dataclass
class SequenceMatch:
    """Represents an alignment or similarity match against a reference sequence."""
    reference_id: str
    scientific_name: str
    similarity_score: float # [0.0, 1.0]
    aligned_length: int
    match_type: str         # 'exact', 'kmer_similarity', 'blast_local', 'embedding'
    matched_kmer_count: int = 0
    target_gene: Optional[str] = "Cytochrome oxidase"
    reference_source: str = "CMLRE Reference Library"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "scientific_name": self.scientific_name,
            "similarity_score": round(self.similarity_score, 4),
            "aligned_length": self.aligned_length,
            "match_type": self.match_type,
            "target_gene": self.target_gene,
            "reference_source": self.reference_source,
        }


class ReferenceMatcher(Protocol):
    """
    Protocol contract for eDNA reference sequence matching.
    Phase 8 can implement this interface with BLAST or neural sequence embeddings.
    """
    def match(self, sequence: str, top_k: int = 5) -> List[SequenceMatch]:
        ...


# Curated marker reference sequences (COI / Cytochrome oxidase barcoding sequences)
DEFAULT_EDNA_REFERENCE_DATABASE: Dict[str, Dict[str, Any]] = {
    "REF_COI_001": {
        "scientific_name": "Rastrelliger kanagurta",
        "target_gene": "Cytochrome oxidase",
        "reference_source": "CMLRE / NBFGR DNA Barcode Library",
        # Canonical COI fragment for Rastrelliger kanagurta
        "sequence": (
            "CCAATCTATCATATGACTTCTGTGCGTCAGACCGGCATGGAAGGGCACCGCCCTGAGCCTCCTGATTCGTGCTGAACTCAGCCAGCCAGGGGCCCTTCTCGGGGACGACCAGATCTACAATGTGATCGTTACCGCACATGCCTTCGTGATAATTTTCTTTATAGTAATGCCAATTATAATTGGCGGCTTCGGAAACTGACTTATTCCCCTTATGATTGGGGCCCCCGACATGGCATTTCCCCGTATGAATAACATAAGTTTCTGACTTCTTCCCCCCTCCTTTCTTCTTCTCCTAGCCTCCTCTGGCGTTGAAGCCGGAGCTGGAACCGGATGAACGGTGTATCCCCCTCTAGCAGGCAATCTCGCTCACGCCGGGGCATCCGTGGACTTAACCATCTTTTCCCTCCACCTAGCGGGAATTTCCTCCATTCTTGGAGCCATTAATTTTATTACTACAATTATTAATATGAAGCCACCTGCTATTTCACAATACCAAACCCCCCTCTTTGTTTGGGCGGTCCTAATTACTGCCGTTCTCCTTCTGCTCTCTCTTCCCGTCCTTGCAGCCGGAATCACAATACTTCTTACAGATCGAAATCTAAACACAACCTTTTTTGACCCTGCGGGAGGAGGAGACCCAATCCTCTATCAACACCTATTCTGATTCTTTGGCCACCCAGAAAGTCTAAAGA"
        ),
    },
    "REF_COI_002": {
        "scientific_name": "Sardinella longiceps",
        "target_gene": "Cytochrome oxidase",
        "reference_source": "CMLRE / NBFGR DNA Barcode Library",
        "sequence": (
            "CCGGTTAATTAGTATTTGGTGCTGAGCCGGATAGTCGGCACCGCCCTGAGCCTACTCATCCGAGCTGAACTAAGCCAACCCGGGGCTCTTCTGGGGGACGATCAAATTTATAACGTAATCGTTACGGCACACGCATTTGTAATAATTTTCTTTATAGTAATACCAATTATGATTGGCGGTTTCGGAAACTGACTAGTACCTCTGATAATCGGCGCCCCCGACATAGCATTCCCCCGAATAAATAACATAAGCTTCTGACTACTCCCTCCATCTTTCCTCCTTTTATTAGCCTCTTCTGGGGTAGAGGCGGGGGCCGGGACGGGGTGAACAGTGTACCCGCCCCTGGCGGGAAACCTGGCTCACGCAGGAGCCTCCGTTGATTTAACTATTTTCTCACTCCACTTAGCAGGTATCTCTTCAATCCTGGGGGCCATTAATTTTATTACAACAATCATTAATATAAAACCCCCAGCTATTTCTCAATACCAAACACCCCTGTTTGTTTGAGCCGTCCTAATCACGGCTGTTCTGCTTCTCCTCTCCCTCCCCGTCCTTGCCGCCGGCATCACTATACTCTTGACAGACCGAAATCTAAACACCACCTTCTTTGACCCATCTGGGGGGCGGAGACCCCATTCTCTACCAACACCTCTTCTGATTCTTTGGCCACCCAGAAAGTCTAAA"
        ),
    },
    "REF_COI_003": {
        "scientific_name": "Nemipterus japonicus",
        "target_gene": "Cytochrome oxidase",
        "reference_source": "CMLRE / NBFGR DNA Barcode Library",
        "sequence": (
            "CCAGCGATCTGTATTGGTGCTTGGGCCGGATAGTGGGCACCGCCTTAAGCCTACTCATTCGGGCAGAACTTAGCCAGCCCGGCGCCCTCTTGGGGGACGACCAGATTTATAATGTAATTGTTACAGCACATGCATTTGTAATAATTTTCTTTATAGTAATACCAATTATGATCGGAGGATTTGGAAACTGACTTCTTCCCCTAATAATCGGCGCCCCCGACATGGCATTTCCCCGAATAAATAACATGAGCTTTTGACTTCTCCCCCCATCATTCCTCCTCCTCCTTGCTTCCTCTGGGGTTGAAGCTGGTGCAGGTACCGGGTGAACCGTCTACCCTCCCCTAGCTGGTAACCTAGCCCACGCAGGAGCATCCGTTGACCTCACAATTTTTTCTCTACACTTAGCAGGCATCTCCTCAATCCTTGGAGCCATCAACTTCATTACAACCATCATTAACATAAAACCTCCCGCTATTTCCCAGTATCAGACCCCCCTCTTTGTGTGAGCCGTATTAATTACTGCCGTCCTTCTTCTCCTCTCCCTTCCGGTCCTCGCTGCTGGCATTACAATGCTTCTCACAGATCGAAACCTCAACACCACCTTCTTTGACCCCGCAGGAGGAGGAGACCCAATCCTTTACCAGCACCTGTTCTGATTCTTTGGCCACCCAGAAGTCTAA"
        ),
    },
    "REF_COI_004": {
        "scientific_name": "Epinephelus diacanthus",
        "target_gene": "Cytochrome oxidase",
        "reference_source": "CMLRE / NBFGR DNA Barcode Library",
        "sequence": (
            "CCATTAGACTGGTATTGGTGCTGAGCCGGTATAGTAGGCACAGCCTTGAGTCTGCTTATCCGAGCAGAACTCAGTCAACCAGGCGCCCTATTGGGAGACGACCAAATCTATAATGTAATTGTTACAGCCCATGCTTTCGTAATAATTTTCTTTATAGTAATGCCAATTATGATTGGAGGTTTCGGAAACTGACTGATCCCTCTTATGATTGGCGCACCAGACATAGCGTTCCCTCGTATAAATAATATAAGCTTCTGACTTCTCCCACCCTCTTTTCTACTTCTTCTCGCCTCTTCCGGGGTTGAGGCGGGGGCTGGAACAGGTTGAACGGTTTACCCTCCCTTGGCTGGCAATCTTGCTCATGCAGGAGCATCCGTAGACCTAACAATTTTCTCTTTACACTTAGCCGGTATTTCATCGATCCTAGGGGCAATCAATTTTATTACTACGATTATCAATATAAAGCCTCCAGCAATCTCTCAATACCAGACTCCTTTGTTTGTATGGGCTGTACTAATTACTGCAGTTCTTCTACTTCTTTCACTGCCAGTTCTTGCCGCTGGCATTACTATGCTACTCACTGATCGAAATCTTAACACCACATTCTTCGATCCAGCGGGAGGAGGGGATCCAATTCTTTACCAACATCTTTTCTGATTCTTTGGCCACCCAGAAAGTCTAA"
        ),
    },
    "REF_COI_005": {
        "scientific_name": "Thunnus albacares",
        "target_gene": "Cytochrome oxidase",
        "reference_source": "CMLRE / NBFGR DNA Barcode Library",
        "sequence": (
            "AAAGGTTAACATAGGTGTTCGGTGCTGTGCCGGATAGTCGCGGACAGCTCTTAGCCTTCTCATCCGAGCGGAACTAAGTCAACCCGGCGCCCTCCTGGGTGATGACCAAATTTATAATGTAATTGTTACAGCACACGCGTTCGTAATAATTTTCTTTATAGTAATACCAATCATGATTGGAGGCTTCGGTAACTGACTGATCCCACTTATGATTGGAGCACCTGATATAGCATTTCCTCGAATAAATAACATGAGTTTCTGACTACTTCCACCTTCATTTCTTCTTCTACTTGCTTCTTCGGGCGTAGAAGCGGGGGCCGGGACCGGATGAACAGTTTATCCCCCACTTGCGGGAAACCTAGCCCACGCAGGAGCCTCCGTTGATTTAACAATTTTCTCCCTTCACCTAGCAGGTATTTCATCTATTCTTGGGGCTATTAATTTTATCACAACCATCACCAATATGAAACCCCCAGGTATTACCCAGTACCAAACCCCATTATTTGTATGAGCAGTACTGATTACTGCTGTTCTTCTACTCCTTTCACTCCCTGTGCTGGCTGCTGGTATCACAATACTTCTTACAGACCGAAACTTAAACACAACCTTCTTTGATCCCGCCGGGGGAGGTGATCCAATCTTGTACCAACACCTATTCTGATTCTTTGGCCACCCAGAAAGTCTAAA"
        ),
    },
}


def _extract_kmers(sequence: str, k: int = 6) -> Set[str]:
    """Generates set of k-mers from a nucleotide sequence."""
    if len(sequence) < k:
        return {sequence} if sequence else set()
    return {sequence[i : i + k] for i in range(len(sequence) - k + 1)}


class ExactReferenceMatcher:
    """Exact substring and full match baseline matcher."""

    def __init__(self, reference_db: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self.ref_db = reference_db or DEFAULT_EDNA_REFERENCE_DATABASE

    def match(self, sequence: str, top_k: int = 5) -> List[SequenceMatch]:
        if not sequence:
            return []

        seq_u = sequence.strip().upper()
        matches: List[SequenceMatch] = []

        for ref_id, data in self.ref_db.items():
            ref_seq = data["sequence"].strip().upper()
            if seq_u == ref_seq:
                matches.append(
                    SequenceMatch(
                        reference_id=ref_id,
                        scientific_name=data["scientific_name"],
                        similarity_score=1.0,
                        aligned_length=len(seq_u),
                        match_type="exact_identity",
                        target_gene=data.get("target_gene", "Cytochrome oxidase"),
                        reference_source=data.get("reference_source", "CMLRE Reference Library"),
                    )
                )
            elif seq_u in ref_seq or ref_seq in seq_u:
                overlap = min(len(seq_u), len(ref_seq))
                sim = overlap / max(len(seq_u), len(ref_seq))
                matches.append(
                    SequenceMatch(
                        reference_id=ref_id,
                        scientific_name=data["scientific_name"],
                        similarity_score=round(sim, 4),
                        aligned_length=overlap,
                        match_type="exact_substring",
                        target_gene=data.get("target_gene", "Cytochrome oxidase"),
                        reference_source=data.get("reference_source", "CMLRE Reference Library"),
                    )
                )

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches[:top_k]


class KmerSimilarityMatcher:
    """
    Fast k-mer containment and Jaccard similarity matcher.
    Computes deterministic overlap score against reference library.
    """

    def __init__(
        self,
        reference_db: Optional[Dict[str, Dict[str, Any]]] = None,
        k: int = 6,
    ) -> None:
        self.ref_db = reference_db or DEFAULT_EDNA_REFERENCE_DATABASE
        self.k = k
        # Pre-compute reference k-mers
        self._ref_kmers: Dict[str, Set[str]] = {
            ref_id: _extract_kmers(d["sequence"].strip().upper(), k=self.k)
            for ref_id, d in self.ref_db.items()
        }

    def match(self, sequence: str, top_k: int = 5) -> List[SequenceMatch]:
        if not sequence:
            return []

        seq_u = sequence.strip().upper()
        query_kmers = _extract_kmers(seq_u, k=self.k)
        if not query_kmers:
            return []

        matches: List[SequenceMatch] = []

        for ref_id, ref_kmers in self._ref_kmers.items():
            if not ref_kmers:
                continue

            intersection = query_kmers.intersection(ref_kmers)
            common_count = len(intersection)
            if common_count == 0:
                continue

            # Query containment similarity: proportion of query k-mers found in reference
            containment = common_count / len(query_kmers)
            # Jaccard similarity
            jaccard = common_count / len(query_kmers.union(ref_kmers))

            # Composite similarity score (weighted towards query containment for subfragments)
            sim_score = round(0.85 * containment + 0.15 * jaccard, 4)

            data = self.ref_db[ref_id]
            matches.append(
                SequenceMatch(
                    reference_id=ref_id,
                    scientific_name=data["scientific_name"],
                    similarity_score=sim_score,
                    aligned_length=len(seq_u),
                    match_type=f"kmer_{self.k}_similarity",
                    matched_kmer_count=common_count,
                    target_gene=data.get("target_gene", "Cytochrome oxidase"),
                    reference_source=data.get("reference_source", "CMLRE Reference Library"),
                )
            )

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        return matches[:top_k]
