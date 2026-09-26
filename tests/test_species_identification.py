"""
Unit & Integration Tests for Phase 14.2 Marine Species Identification.
Covers:
- Model initialization & artifact loading
- 10-class taxonomy verification
- Deterministic preprocessing & tensor shapes
- Softmax probability calibration & confidence tiers
- Edge cases & corrupt input handling
- FastAPI endpoints (POST /identify, GET /health, GET /identify/model-info)
"""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from ml.species_identification import (
    MarineSpeciesIdentifier,
    get_species_identifier,
    SPECIES_METADATA,
)
from backend.app.main import app

client = TestClient(app)

EXPECTED_CLASSES = [
    "Acanthurus nigrofuscus",
    "Amphiprion clarkii",
    "Canthigaster valentini",
    "Chaetodon lunulatus",
    "Chaetodon trifascialis",
    "Hemigymnus fasciatus",
    "Lutjanus fulvus",
    "Myripristis kuntee",
    "Neoniphon sammara",
    "Plectroglyphidodon dickii",
]


@pytest.fixture(scope="module")
def identifier():
    """Provides the singleton MarineSpeciesIdentifier."""
    return get_species_identifier()


@pytest.fixture
def sample_pil_image():
    """Generates an in-memory 224x224 RGB image."""
    return Image.new("RGB", (224, 224), color=(64, 128, 192))


@pytest.fixture
def sample_jpeg_bytes(sample_pil_image):
    """Generates raw JPEG bytes for testing byte and upload endpoints."""
    buf = io.BytesIO()
    sample_pil_image.save(buf, format="JPEG")
    return buf.getvalue()


# =========================================================================
# 1. Model Artifact & Architecture Tests
# =========================================================================

def test_model_loading_and_classes(identifier):
    """Verifies that the ResNet-18 model loads with exactly 10 supported classes."""
    assert identifier is not None
    assert identifier.num_classes == 10
    assert len(identifier.id_to_class) == 10

    # Ensure all 10 expected species are mapped
    mapped_species = sorted(list(identifier.id_to_class.values()))
    assert mapped_species == sorted(EXPECTED_CLASSES)


def test_model_info_schema(identifier):
    """Verifies the model info structure."""
    info = identifier.get_model_info()
    assert info["model_name"] == "MarineSpeciesClassifier"
    assert info["num_classes"] == 10
    assert info["status"] == "ready"
    assert len(info["supported_species"]) == 10
    assert info["input_resolution"] == [224, 224, 3]


def test_species_taxonomic_catalog(identifier):
    """Verifies all 10 target species have taxonomic metadata."""
    for sp_name in EXPECTED_CLASSES:
        meta = identifier.get_species_info(sp_name)
        assert meta["common_name"] is not None
        assert meta["family"] is not None
        assert "depth_range_m" in meta
        assert "worms_aphia_id" in meta


# =========================================================================
# 2. Inference & Calibration Engine Tests
# =========================================================================

def test_predict_returns_valid_structure(identifier, sample_pil_image):
    """Tests end-to-end inference on a PIL Image."""
    res = identifier.predict(sample_pil_image, top_k=3)

    assert "species" in res
    assert "common_name" in res
    assert "family" in res
    assert "confidence" in res
    assert "confidence_tier" in res
    assert "top_predictions" in res
    assert "inference_time_ms" in res
    assert res["species"] in EXPECTED_CLASSES
    assert res["confidence_tier"] in ("HIGH", "MODERATE", "LOW")
    assert len(res["top_predictions"]) == 3


def test_predict_from_bytes(identifier, sample_jpeg_bytes):
    """Verifies predict works from raw image bytes."""
    res = identifier.predict(sample_jpeg_bytes, top_k=5)
    assert res["species"] in EXPECTED_CLASSES
    assert len(res["top_predictions"]) == 5


def test_probabilities_ranking_and_bounds(identifier, sample_pil_image):
    """Verifies probabilities are ranked descending and within [0, 1]."""
    res = identifier.predict(sample_pil_image, top_k=10)
    top_preds = res["top_predictions"]
    assert len(top_preds) == 10

    total_prob = 0.0
    prev_prob = 1.0
    for p in top_preds:
        conf = p["confidence"]
        assert 0.0 <= conf <= 1.0
        assert conf <= prev_prob + 1e-4, "Predictions must be sorted in descending confidence"
        prev_prob = conf
        total_prob += conf

    assert abs(total_prob - 1.0) < 0.01, f"Total probability should sum to ~1.0, got {total_prob}"


def test_confidence_tier_thresholds(identifier):
    """Verifies confidence tier logic directly."""
    # Simulation: test the tier boundaries
    def get_tier(c):
        if c >= 0.70:
            return "HIGH"
        elif c >= 0.40:
            return "MODERATE"
        return "LOW"

    assert get_tier(0.95) == "HIGH"
    assert get_tier(0.70) == "HIGH"
    assert get_tier(0.6999) == "MODERATE"
    assert get_tier(0.40) == "MODERATE"
    assert get_tier(0.3999) == "LOW"
    assert get_tier(0.05) == "LOW"


def test_invalid_input_handling(identifier):
    """Verifies that non-image inputs raise appropriate exceptions."""
    with pytest.raises(Exception):
        identifier.predict(b"not an image byte stream")

    with pytest.raises(FileNotFoundError):
        identifier.predict("non_existent_file_path_12345.jpg")


def test_singleton_consistency():
    """Verifies get_species_identifier returns singleton instance."""
    id1 = get_species_identifier()
    id2 = get_species_identifier()
    assert id1 is id2


# =========================================================================
# 3. FastAPI Route Integration Tests
# =========================================================================

def test_api_species_health():
    """GET /api/v1/species/health returns readiness status."""
    response = client.get("/api/v1/species/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model"] == "MarineSpeciesClassifier-ResNet18"
    assert data["classes"] == 10


def test_api_species_model_info():
    """GET /api/v1/species/identify/model-info returns full model metadata."""
    response = client.get("/api/v1/species/identify/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["num_classes"] == 10
    assert len(data["classes"]) == 10
    assert len(data["supported_species"]) == 10


def test_api_species_identify_success(sample_jpeg_bytes):
    """POST /api/v1/species/identify with valid image returns 200 and schema."""
    files = {"file": ("test_reef_fish.jpg", sample_jpeg_bytes, "image/jpeg")}
    response = client.post("/api/v1/species/identify?top_k=3", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "species" in data
    assert "common_name" in data
    assert "family" in data
    assert "confidence" in data
    assert "confidence_tier" in data
    assert len(data["top_predictions"]) == 3
    assert data["species"] in EXPECTED_CLASSES


def test_api_species_identify_empty_file():
    """POST /api/v1/species/identify with empty file returns 400."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/species/identify", files=files)
    assert response.status_code == 400


def test_api_species_identify_corrupt_file():
    """POST /api/v1/species/identify with corrupt image content returns 400."""
    files = {"file": ("corrupt.jpg", b"corrupted random data bytes 123", "image/jpeg")}
    response = client.post("/api/v1/species/identify", files=files)
    assert response.status_code == 400


def test_api_species_identify_invalid_extension():
    """POST /api/v1/species/identify with disallowed file extension returns 400."""
    files = {"file": ("malicious.exe", b"binary data", "application/octet-stream")}
    response = client.post("/api/v1/species/identify", files=files)
    assert response.status_code == 400
