"""
Standalone FastAPI Service for Marine Species Identification.
Loads production model once at startup and provides /predict and /health endpoints.
"""

import io
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from PIL import Image

from src.inference.predict import MarineSpeciesIdentifier

app = FastAPI(
    title="Marine Species Identification Service",
    description="Deep Learning API for Automated Marine Fish Species Recognition (Phase 14.2)",
    version="1.0.0"
)

# Singleton model instance loaded once at startup
_identifier: Optional[MarineSpeciesIdentifier] = None


@app.on_event("startup")
def startup_event():
    """Load model weights and taxonomy into memory at server startup."""
    global _identifier
    try:
        _identifier = MarineSpeciesIdentifier()
        print("MarineSpeciesIdentifier successfully loaded at startup.")
    except Exception as e:
        print(f"Startup model load warning: {e}")


def get_identifier() -> MarineSpeciesIdentifier:
    global _identifier
    if _identifier is None:
        _identifier = MarineSpeciesIdentifier()
    return _identifier


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint: verifies service status and model metadata."""
    identifier = get_identifier()
    return {
        "status": "ok",
        "model": "marine_species_identifier",
        "version": identifier.model_version,
        "device": str(identifier.device),
        "num_classes": identifier.num_classes
    }


@app.post("/predict", tags=["Inference"])
async def predict_species(
    file: UploadFile = File(...),
    top_k: int = Query(3, ge=1, le=10, description="Number of top candidate species to return")
):
    """
    Identifies marine species from uploaded underwater image.
    Supports PNG, JPEG, WEBP formats.
    """
    identifier = get_identifier()

    # Validate content type
    valid_content_types = ["image/jpeg", "image/png", "image/webp", "image/bmp"]
    if file.content_type and file.content_type.lower() not in valid_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file.content_type}. Please upload a JPEG, PNG, or WEBP image."
        )

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file received."
            )

        # Max file size safeguard (20MB)
        if len(contents) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image file exceeds maximum permitted size of 20MB."
            )

        with Image.open(io.BytesIO(contents)) as pil_img:
            result = identifier.predict(pil_img, top_k=top_k)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.inference.api:app", host="127.0.0.1", port=8001, reload=False)
