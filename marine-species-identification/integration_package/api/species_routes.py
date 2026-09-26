"""
Marine Species Identification FastAPI Router.
Ready for inclusion into backend/app/api/v1/species.py
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from PIL import Image
import io

from .predict import MarineSpeciesIdentifier

router = APIRouter(prefix="/species", tags=["Species Identification"])

_identifier: Optional[MarineSpeciesIdentifier] = None

def get_species_identifier() -> MarineSpeciesIdentifier:
    global _identifier
    if _identifier is None:
        _identifier = MarineSpeciesIdentifier()
    return _identifier

@router.get("/health")
def species_health():
    """Verifies species classification model status."""
    ident = get_species_identifier()
    return {
        "status": "ready",
        "model": "MarineSpeciesClassifier-ResNet18",
        "version": ident.model_version,
        "classes": ident.num_classes
    }

@router.post("/identify")
async def identify_marine_species(
    file: UploadFile = File(...),
    top_k: int = Query(3, ge=1, le=10)
):
    """Identifies marine fish species from uploaded photograph or underwater frame."""
    ident = get_species_identifier()
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image uploaded.")
    try:
        with Image.open(io.BytesIO(contents)) as pil_img:
            result = ident.predict(pil_img, top_k=top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")
