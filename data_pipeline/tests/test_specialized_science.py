"""
Comprehensive Test Suite for Phase 7: Specialized Scientific Modules.
Tests eDNA sequence processing, Otolith image analysis, Taxonomy service,
evidence generation, confidence derivations, storage boundaries, and Phase 8 extension contracts.
"""

import io
from pathlib import Path
import sys
import unittest
from typing import Any, Dict, List

import numpy as np
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_pipeline.ingestion.txt_parser import parse_cmlre_txt
from data_pipeline.specialized_science import (
    BaselineMorphologicalFeatureExtractor,
    BaselineOtolithClassifier,
    ConfidenceLevel,
    DEFAULT_EDNA_REFERENCE_DATABASE,
    DEFAULT_TAXONOMY_RECORDS,
    EDNAService,
    EDNAValidationResult,
    EvidenceType,
    ExactReferenceMatcher,
    IdentificationStatus,
    ImageValidationResult,
    InMemoryStorageRepository,
    KmerSimilarityMatcher,
    OtolithAnalysisService,
    OtolithClassificationResult,
    OtolithFeatureVector,
    PreprocessedImage,
    PreprocessedSequence,
    ReferenceMatcher,
    ScientificEvidence,
    SequenceMatch,
    SpecializedResult,
    SpeciesDetection,
    SynonymResolver,
    TaxonHierarchy,
    TaxonomicRank,
    TaxonRecord,
    TaxonResolutionResult,
    TaxonomyService,
    calculate_baseline_edna_confidence,
    calculate_gc_content,
    detect_species_from_matches,
    preprocess_fastq_records,
    preprocess_image,
    preprocess_sequence,
    validate_fasta,
    validate_fastq,
    validate_image_input,
    validate_sequence_string,
)


class TestPhase7SpecializedScience(unittest.TestCase):
    """Test suite covering all specialized scientific domain modules."""

    def setUp(self) -> None:
        self.taxonomy_service = TaxonomyService()
        self.edna_service = EDNAService(taxonomy_service=self.taxonomy_service)
        self.otolith_service = OtolithAnalysisService(taxonomy_service=self.taxonomy_service)

    # =========================================================================
    # A. eDNA Validation Tests
    # =========================================================================

    def test_A1_valid_fasta_validation(self):
        """A1. FASTA Validation: Valid multi-line and single-line FASTA records."""
        fasta_content = (
            ">seq1 Rastrelliger kanagurta sample\n"
            "CCAATCTATCATATGACTTCTGTGCGTCAGACCGGCATGGAAGGGCACCGCCCTGAGCCT\n"
            "CCTGATTCGTGCTGAACTCAGCCAGCCAGGGGCCCTTCTCGGGGACGACCAGATCTACAA\n"
            ">seq2 Sardinella longiceps sample\n"
            "CCGGTTAATTAGTATTTGGTGCTGAGCCGGATAGTCGGCACCGCCCTGAGCCTACTCATC\n"
        )
        res = validate_fasta(fasta_content)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.valid_records_count, 2)
        self.assertEqual(res.fasta_records[0].id, "seq1")
        self.assertEqual(len(res.fasta_records[0].sequence), 120)
        self.assertEqual(res.fasta_records[1].id, "seq2")

    def test_A2_invalid_fasta_validation(self):
        """A2. FASTA Validation: Empty content, invalid characters, and missing headers."""
        # 1. Empty content
        res_empty = validate_fasta("")
        self.assertFalse(res_empty.is_valid)
        self.assertIn("empty", res_empty.errors[0].lower())

        # 2. Content before header
        res_no_header = validate_fasta("ATGCGATCGATCGATC\n>header\nATGC")
        self.assertFalse(res_no_header.is_valid)
        self.assertIn("before any FASTA '>' header", res_no_header.errors[0])

        # 3. Invalid nucleotide characters (e.g. 'Z', '1', '@')
        res_invalid_chars = validate_fasta(">seq_bad\nATGCZ123@#")
        self.assertFalse(res_invalid_chars.is_valid)
        self.assertIn("invalid nucleotide characters", res_invalid_chars.errors[0].lower())

    def test_A3_valid_fastq_validation(self):
        """A3. FASTQ Validation: Standard 4-line FASTQ structure and Phred scores."""
        fastq_content = (
            "@read_01/1\n"
            "ATGCGATCGATCGATCGATC\n"
            "+\n"
            "IIIIIIIIIIIIIIIIIIII\n"
            "@read_02/1\n"
            "GCTAGCTAGCTAGCTA\n"
            "+read_02/1\n"
            "FFFFFFFFFFFFFFFF\n"
        )
        res = validate_fastq(fastq_content)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.valid_records_count, 2)
        self.assertEqual(res.fastq_records[0].id, "read_01/1")
        self.assertEqual(len(res.fastq_records[0].sequence), 20)

    def test_A4_invalid_fastq_validation(self):
        """A4. FASTQ Validation: Length mismatches and broken headers."""
        # Length mismatch between sequence (10bp) and quality (8 chars)
        bad_fastq = (
            "@read_bad\n"
            "ATGCGATCGA\n"
            "+\n"
            "IIIIIIII\n"
        )
        res = validate_fastq(bad_fastq)
        self.assertFalse(res.is_valid)
        self.assertIn("length", res.errors[0].lower())

    # =========================================================================
    # B. eDNA Preprocessing & Quality Filtering
    # =========================================================================

    def test_B1_sequence_preprocessing_and_gc(self):
        """B1. Preprocessing: Case normalization, gap stripping, and GC computation."""
        raw = "  atg-c.g-at c g\n  "
        prep = preprocess_sequence(raw, seq_id="test_seq", min_length=5)
        self.assertTrue(prep.passed_filter)
        self.assertEqual(prep.cleaned_sequence, "ATGCGATCG")
        self.assertEqual(prep.length, 9)
        # GC count in ATGCGATCG: 5 out of 9 -> ~0.5556
        self.assertAlmostEqual(prep.gc_content, 5.0 / 9.0, places=3)

    def test_B2_ambiguous_and_short_sequence_filtering(self):
        """B2. Preprocessing: Rejection of excessive ambiguous bases and short reads."""
        # Excessive Ns (50% ambiguous)
        ambig_seq = "ATGCNNNNNNATGC"
        prep_ambig = preprocess_sequence(ambig_seq, min_length=10, max_ambiguous_ratio=0.10)
        self.assertFalse(prep_ambig.passed_filter)
        self.assertIn("Ambiguous base ratio", prep_ambig.filter_notes[0])

        # Short read
        short_seq = "ATGC"
        prep_short = preprocess_sequence(short_seq, min_length=20)
        self.assertFalse(prep_short.passed_filter)
        self.assertIn("below minimum threshold", prep_short.filter_notes[0])

    def test_B3_fastq_quality_filtering(self):
        """B3. Preprocessing: FASTQ Phred quality conversion and 3' end-trimming."""
        # Quality string: 'I' (Phred 40), '#' (Phred 2) -> should trim '#' off the end
        records = [
            validate_fastq(
                "@read_trim\n"
                "ATGCGATCGATCGATC\n"
                "+\n"
                "IIIIIIIIIIII####\n"
            ).fastq_records[0]
        ]
        prepped = preprocess_fastq_records(records, min_phred=20, min_length=10)
        self.assertEqual(len(prepped), 1)
        self.assertEqual(prepped[0].length, 12)
        self.assertEqual(prepped[0].cleaned_sequence, "ATGCGATCGATC")
        self.assertEqual(prepped[0].metadata.get("bases_trimmed"), 4)

    # =========================================================================
    # C. eDNA Matching, Detection & Baseline Confidence
    # =========================================================================

    def test_C1_exact_and_kmer_reference_matching(self):
        """C1. Reference Matching: Exact and k-mer similarity against marine reference library."""
        # Exact sequence of Rastrelliger kanagurta from reference database
        ref_seq = DEFAULT_EDNA_REFERENCE_DATABASE["REF_COI_001"]["sequence"]
        
        # 1. Exact Matcher
        exact_matcher = ExactReferenceMatcher()
        matches_exact = exact_matcher.match(ref_seq)
        self.assertGreater(len(matches_exact), 0)
        self.assertEqual(matches_exact[0].scientific_name, "Rastrelliger kanagurta")
        self.assertEqual(matches_exact[0].similarity_score, 1.0)

        # 2. K-mer Matcher on a subfragment (100bp window)
        subfragment = ref_seq[50:180]
        kmer_matcher = KmerSimilarityMatcher(k=6)
        matches_kmer = kmer_matcher.match(subfragment)
        self.assertGreater(len(matches_kmer), 0)
        self.assertEqual(matches_kmer[0].scientific_name, "Rastrelliger kanagurta")
        self.assertGreater(matches_kmer[0].similarity_score, 0.80)

    def test_C2_species_detection_and_confidence_scoring(self):
        """C2. Species Detection: High confidence detection and unresolved fallback."""
        ref_seq = DEFAULT_EDNA_REFERENCE_DATABASE["REF_COI_002"]["sequence"] # Sardinella longiceps

        # High confidence detection
        res = self.edna_service.analyze_sequence(ref_seq, seq_id="sardine_test")
        self.assertEqual(res.domain, "edna")
        self.assertEqual(res.target_entity, "Sardinella longiceps")
        self.assertEqual(res.common_name, "Indian Oil Sardine")
        self.assertEqual(res.status, IdentificationStatus.CONFIRMED)
        self.assertGreaterEqual(res.confidence_score, 0.90)
        self.assertEqual(res.confidence_level, ConfidenceLevel.HIGH)
        self.assertFalse(res.is_ml_prediction) # Baseline indicator

        # Unresolved sequence (random/novel sequence with no reference match)
        novel_seq = "AAAAAAAAAAAAAAAAAAAATTTTTTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCCCCCGGGGGGGGGGGGGGGGGGGG"
        res_novel = self.edna_service.analyze_sequence(novel_seq, seq_id="novel_test", confidence_threshold=0.80)
        self.assertEqual(res_novel.status, IdentificationStatus.UNRESOLVED)
        self.assertIsNone(res_novel.target_entity)
        self.assertGreater(len(res_novel.warnings), 0)

    def test_C3_real_cmlre_edna_dataset_row_analysis(self):
        """C3. CMLRE Ingestion Integration: Analyzes real record from dataset/dnaderiveddata1.txt."""
        dataset_path = ROOT_DIR / "dataset" / "dnaderiveddata1.txt"
        if not dataset_path.exists():
            self.skipTest(f"Dataset file {dataset_path} not found.")

        df, meta, _ = parse_cmlre_txt(str(dataset_path))
        first_row = df.iloc[0].to_dict()

        result = self.edna_service.analyze_cmlre_edna_record(first_row)
        self.assertEqual(result.domain, "edna")
        self.assertIsNotNone(result.confidence_score)
        self.assertIn("cmlre_sample_id", result.provenance)
        self.assertEqual(result.provenance["cmlre_sample_id"], first_row.get("samp_name"))

    # =========================================================================
    # D. Otolith / Image Analysis Tests
    # =========================================================================

    def test_D1_image_validation(self):
        """D1. Image Validation: Format checking, readability, and corrupted/empty inputs."""
        # 1. Create valid synthetic PNG image
        img_valid = Image.new("L", (100, 60), color=128)
        bio = io.BytesIO()
        img_valid.save(bio, format="PNG")
        valid_bytes = bio.getvalue()

        v_res = validate_image_input(valid_bytes)
        self.assertTrue(v_res.is_valid)
        self.assertEqual(v_res.width, 100)
        self.assertEqual(v_res.height, 60)

        # 2. Empty byte stream
        v_empty = validate_image_input(b"")
        self.assertFalse(v_empty.is_valid)
        self.assertIn("empty", v_empty.errors[0].lower())

        # 3. Too small dimension (< 32px)
        img_tiny = Image.new("L", (16, 16), color=128)
        v_tiny = validate_image_input(img_tiny, min_dimension=32)
        self.assertFalse(v_tiny.is_valid)
        self.assertIn("smaller than minimum", v_tiny.errors[0].lower())

    def test_D2_image_preprocessing_and_array_normalization(self):
        """D2. Preprocessing: Resizing to target resolution and pixel normalization [0.0, 1.0]."""
        img = Image.new("RGB", (300, 150), color=(200, 100, 50))
        prepped = preprocess_image(img, target_size=(224, 224), to_grayscale=True, normalize=True)

        self.assertEqual(prepped.width, 224)
        self.assertEqual(prepped.height, 224)
        self.assertEqual(prepped.original_dimensions, (300, 150))
        self.assertTrue(prepped.is_grayscale)
        self.assertEqual(prepped.normalized_array.shape, (224, 224))
        self.assertTrue(0.0 <= prepped.normalized_array.min() <= 1.0)
        self.assertTrue(0.0 <= prepped.normalized_array.max() <= 1.0)

    def test_D3_morphological_feature_extraction(self):
        """D3. Features: Extracts aspect ratio, intensity moments, gradients, and entropy."""
        # Create an elliptical pattern
        arr = np.zeros((224, 224), dtype=np.uint8)
        y, x = np.ogrid[:224, :224]
        mask = ((x - 112) / 60) ** 2 + ((y - 112) / 30) ** 2 <= 1.0 # 2:1 aspect ratio ellipse
        arr[mask] = 220
        img = Image.fromarray(arr, mode="L")

        extractor = BaselineMorphologicalFeatureExtractor()
        prepped = preprocess_image(img, target_size=(224, 224), to_grayscale=True)
        feats = extractor.extract(prepped)

        self.assertIn("aspect_ratio", feats.features)
        self.assertIn("mean_intensity", feats.features)
        self.assertIn("gradient_magnitude_mean", feats.features)
        self.assertIn("contrast_ratio", feats.features)
        self.assertGreater(feats.dimension, 8)
        self.assertIsInstance(feats.to_numpy(), np.ndarray)

    def test_D4_baseline_otolith_classification_and_service(self):
        """D4. Classification: Heuristic baseline with non-ML disclaimer and taxonomy resolution."""
        # Create synthetic otolith image with high aspect ratio (~2.0)
        img = Image.new("L", (200, 100), color=150)
        result = self.otolith_service.analyze_image(img, image_id="otolith_sample_01")

        self.assertEqual(result.domain, "otolith")
        self.assertIsNotNone(result.target_entity)
        self.assertFalse(result.is_ml_prediction) # Baseline indicator
        self.assertIn("heuristic", result.confidence_method)
        self.assertIsNotNone(result.evidence)
        self.assertEqual(result.evidence.evidence_type, EvidenceType.OTOLITH_IMAGE)
        self.assertIn("Baseline heuristic classification", result.metadata.get("notice", ""))

    # =========================================================================
    # E. Taxonomy Service Tests
    # =========================================================================

    def test_E1_exact_and_partial_species_search(self):
        """E1. Taxonomy Search: Exact, common-name, and partial substring searches."""
        # 1. Exact search
        exact_results = self.taxonomy_service.search("Rastrelliger kanagurta", mode="exact")
        self.assertEqual(len(exact_results), 1)
        self.assertEqual(exact_results[0].scientific_name, "Rastrelliger kanagurta")
        self.assertEqual(exact_results[0].rank, TaxonomicRank.SPECIES)

        # 2. Common name search
        common_results = self.taxonomy_service.search("Indian Oil Sardine", mode="common")
        self.assertEqual(len(common_results), 1)
        self.assertEqual(common_results[0].scientific_name, "Sardinella longiceps")

        # 3. Partial query search
        partial_results = self.taxonomy_service.search("Nemipterus", mode="partial")
        self.assertGreater(len(partial_results), 0)
        self.assertEqual(partial_results[0].scientific_name, "Nemipterus japonicus")

    def test_E2_taxonomic_hierarchy_retrieval(self):
        """E2. Taxonomic Hierarchy: Kingdom through Species full lineage retrieval."""
        hier = self.taxonomy_service.get_hierarchy("Thunnus albacares")
        self.assertIsNotNone(hier)
        self.assertEqual(hier.kingdom, "Animalia")
        self.assertEqual(hier.phylum, "Chordata")
        self.assertEqual(hier.class_name, "Actinopterygii")
        self.assertEqual(hier.order, "Scombriformes")
        self.assertEqual(hier.family, "Scombridae")
        self.assertEqual(hier.genus, "Thunnus")
        self.assertEqual(hier.species, "Thunnus albacares")

    def test_E3_synonym_resolution(self):
        """E3. Synonym Resolution: Resolves deprecated/alternative names to accepted canonical names."""
        # Scomber kanagurta is a junior synonym for Rastrelliger kanagurta
        res = self.taxonomy_service.resolve_taxon("Scomber kanagurta")
        self.assertTrue(res.is_resolved)
        self.assertTrue(res.is_synonym)
        self.assertEqual(res.scientific_name, "Rastrelliger kanagurta")
        self.assertEqual(res.common_name, "Indian Mackerel")
        self.assertIn("synonym for accepted name", res.warnings[0])

    def test_E4_unresolved_taxon_handling(self):
        """E4. Unresolved Taxon: Graceful handling of unknown organism strings."""
        res = self.taxonomy_service.resolve_taxon("Unknown fictional organism 123")
        self.assertFalse(res.is_resolved)
        self.assertEqual(res.status, IdentificationStatus.UNRESOLVED)
        self.assertEqual(res.confidence_score, 0.0)
        self.assertIn("could not be resolved", res.warnings[0])

    # =========================================================================
    # F. Cross-Module Integration & Phase 8 ML Decoupling
    # =========================================================================

    def test_F1_storage_repository_persistence(self):
        """F1. Storage Boundary: Persists and retrieves evidence and results via StorageRepository."""
        repo = InMemoryStorageRepository()
        edna_svc = EDNAService(storage_repo=repo, taxonomy_service=self.taxonomy_service)

        ref_seq = DEFAULT_EDNA_REFERENCE_DATABASE["REF_COI_003"]["sequence"]
        result = edna_svc.analyze_sequence(ref_seq, seq_id="persist_test", persist=True)

        # Retrieve saved result and evidence
        saved_res = repo.get_result(result.result_id)
        self.assertIsNotNone(saved_res)
        self.assertEqual(saved_res.result_id, result.result_id)
        self.assertEqual(saved_res.target_entity, "Nemipterus japonicus")

        saved_ev = repo.get_evidence(result.evidence.evidence_id)
        self.assertIsNotNone(saved_ev)
        self.assertEqual(saved_ev.evidence_type, EvidenceType.EDNA_SEQUENCE)

    def test_F2_phase8_custom_ml_classifier_injection(self):
        """F2. Phase 8 Extension: Verifies drop-in ML classifier implementation without API rewrite."""
        # Simulated Phase 8 PyTorch / ONNX CNN classifier
        class MockPhase8CNNClassifier:
            def classify(self, feature_vector: OtolithFeatureVector) -> OtolithClassificationResult:
                return OtolithClassificationResult(
                    predicted_species="Thunnus albacares",
                    predicted_age_years=5,
                    confidence_score=0.96,
                    confidence_level=ConfidenceLevel.HIGH,
                    status=IdentificationStatus.CONFIRMED,
                    classifier_name="otolith_resnet50_v2",
                    is_ml_model=True,
                    candidate_scores={"Thunnus albacares": 0.96, "Rastrelliger kanagurta": 0.04},
                    features_used=["cnn_embedding_dim_512"],
                )

        # Inject Phase 8 model into Phase 7 service
        ml_service = OtolithAnalysisService(
            classifier=MockPhase8CNNClassifier(),
            taxonomy_service=self.taxonomy_service,
        )

        img = Image.new("L", (200, 100), color=150)
        res = ml_service.analyze_image(img, image_id="ml_test_01")

        self.assertEqual(res.target_entity, "Thunnus albacares")
        self.assertEqual(res.common_name, "Yellowfin Tuna")
        self.assertTrue(res.is_ml_prediction) # True for Phase 8 model
        self.assertEqual(res.confidence_level, ConfidenceLevel.HIGH)
        self.assertEqual(res.provenance["classifier"], "otolith_resnet50_v2")
        self.assertEqual(res.taxonomic_hierarchy.get("family"), "Scombridae")

    def test_F3_phase8_custom_blast_matcher_injection(self):
        """F3. Phase 8 Extension: Verifies drop-in BLAST / Neural sequence matcher."""
        # Simulated Phase 8 BLAST / Embedding sequence matcher
        class MockPhase8BLASTMatcher:
            def match(self, sequence: str, top_k: int = 5) -> List[SequenceMatch]:
                return [
                    SequenceMatch(
                        reference_id="NCBI_BLAST_9988",
                        scientific_name="Epinephelus diacanthus",
                        similarity_score=0.99,
                        aligned_length=len(sequence),
                        match_type="ncbi_blast_local",
                        target_gene="Cytochrome oxidase",
                        reference_source="NCBI GenBank Marine Index",
                    )
                ]

        edna_ml_service = EDNAService(
            matcher=MockPhase8BLASTMatcher(),
            taxonomy_service=self.taxonomy_service,
        )

        query_seq = DEFAULT_EDNA_REFERENCE_DATABASE["REF_COI_004"]["sequence"]
        res = edna_ml_service.analyze_sequence(query_seq, seq_id="blast_test")
        self.assertEqual(res.target_entity, "Epinephelus diacanthus")
        self.assertEqual(res.common_name, "Thornycheek Grouper")
        self.assertEqual(res.status, IdentificationStatus.CONFIRMED)
        self.assertEqual(res.evidence.provenance["match_type"], "ncbi_blast_local")


if __name__ == "__main__":
    unittest.main()
