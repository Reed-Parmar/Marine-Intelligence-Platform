"""
Automated Pytest Suite for Marine Species Identification (Phase T).
Validates model loading, preprocessing, inference output schema,
error handling (empty/invalid images), and FastAPI endpoints.
"""

import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.api import app, get_identifier
from src.inference.predict import MarineSpeciesIdentifier


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def sample_test_image_path() -> Path:
    """Provides path to real test image from dataset splits."""
    test_csv = PROJECT_ROOT / "data" / "splits" / "test.csv"
    import pandas as pd
    df = pd.read_csv(test_csv)
    sample_path = Path(df.iloc[0]["image_path"])
    assert sample_path.exists(), f"Sample image {sample_path} must exist"
    return sample_path


def test_health_endpoint(client):
    """Verifies GET /health returns valid metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "marine_species_identifier"
    assert "version" in data
    assert data["num_classes"] == 10


def test_standalone_python_prediction(sample_test_image_path):
    """Verifies direct Python inference pipeline without API."""
    identifier = MarineSpeciesIdentifier()
    result = identifier.predict(sample_test_image_path, top_k=3)

    assert "species" in result
    assert "confidence" in result
    assert "top_predictions" in result
    assert "confidence_tier" in result
    assert result["confidence_tier"] in ("HIGH", "MODERATE", "LOW")
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["top_predictions"]) == 3
    assert result["top_predictions"][0]["species"] == result["species"]
    assert result["inference_time_ms"] > 0.0


def test_api_predict_success(client, sample_test_image_path):
    """Verifies POST /predict with a genuine marine test image."""
    with open(sample_test_image_path, "rb") as f:
        img_bytes = f.read()

    response = client.post(
        "/predict?top_k=3",
        files={"file": ("fish_test.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    data = response.json()

    assert "species" in data
    assert "common_name" in data
    assert "family" in data
    assert "confidence" in data
    assert "top_predictions" in data
    assert len(data["top_predictions"]) == 3


def test_api_predict_invalid_format(client):
    """Verifies rejection of unsupported file types."""
    fake_txt = b"This is a text file, not an image."
    response = client.post(
        "/predict",
        files={"file": ("document.txt", fake_txt, "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_api_predict_empty_file(client):
    """Verifies rejection of empty file payloads."""
    response = client.post(
        "/predict",
        files={"file": ("empty.png", b"", "image/png")}
    )
    assert response.status_code == 400
    assert "Empty image file" in response.json()["detail"]


def test_api_predict_corrupt_image(client):
    """Verifies rejection of corrupt binary data with image header."""
    corrupt_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRcorrupt_content_random"
    response = client.post(
        "/predict",
        files={"file": ("corrupt.png", corrupt_bytes, "image/png")}
    )
    assert response.status_code == 500
    assert "Inference execution failed" in response.json()["detail"]
