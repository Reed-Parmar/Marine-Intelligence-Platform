"""
Script to Assemble and Verify the Integration Package (Phase W).
Packages only the lightweight artifacts and modules required for downstream integration
into the main Marine Intelligence Platform.
"""

import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=" * 60)
    print("PHASE W: CREATE INTEGRATION PACKAGE")
    print("=" * 60)

    pkg_dir = PROJECT_ROOT / "integration_package"
    pkg_model = pkg_dir / "model"
    pkg_inf = pkg_dir / "inference"
    pkg_api = pkg_dir / "api"

    pkg_model.mkdir(parents=True, exist_ok=True)
    pkg_inf.mkdir(parents=True, exist_ok=True)
    pkg_api.mkdir(parents=True, exist_ok=True)

    # 1. Copy model artifacts
    src_model = PROJECT_ROOT / "models" / "species_identifier" / "species_model.pth"
    if not src_model.exists():
        src_model = PROJECT_ROOT / "models" / "final_model" / "final_model.pth"
    if not src_model.exists():
        src_model = PROJECT_ROOT / "models" / "baseline" / "baseline_model.pth"

    shutil.copy2(src_model, pkg_model / "species_model.pth")
    shutil.copy2(PROJECT_ROOT / "models" / "class_mapping.json", pkg_model / "class_mapping.json")

    meta_src = PROJECT_ROOT / "models" / "species_identifier" / "model_metadata.json"
    if meta_src.exists():
        shutil.copy2(meta_src, pkg_model / "model_metadata.json")

    # 2. Copy inference and preprocessing modules
    shutil.copy2(PROJECT_ROOT / "src" / "inference" / "predict.py", pkg_inf / "predict.py")
    shutil.copy2(PROJECT_ROOT / "src" / "preprocessing" / "dataset.py", pkg_inf / "preprocessing.py")

    # 3. Create clean FastAPI route module for backend integration
    species_routes_code = '''"""
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
'''
    (pkg_api / "species_routes.py").write_text(species_routes_code, encoding="utf-8")

    # 4. Minimal requirements.txt for deployment
    pkg_reqs = '''# Standalone / Integration Inference Dependencies
torch>=2.0.0
torchvision>=0.15.0
pillow>=10.0.0
numpy>=1.24.0
fastapi>=0.100.0
python-multipart>=0.0.6
'''
    (pkg_dir / "requirements.txt").write_text(pkg_reqs, encoding="utf-8")

    # 5. Create INTEGRATION_GUIDE.md
    guide_content = '''# Marine Species Identification - Integration Guide

This guide details how to integrate the trained deep learning model into the main Marine Intelligence Platform.

## 1. Directory Placement
Copy files into the main repository as follows:
- `integration_package/model/` -> `ml/species_identification/artifacts/`
- `integration_package/inference/predict.py` -> `ml/species_identification/inference.py`
- `integration_package/api/species_routes.py` -> `backend/app/api/v1/species.py`

## 2. Dependencies
Ensure `torch`, `torchvision`, and `pillow` are installed in the backend environment.

## 3. Registering the FastAPI Endpoint
In `backend/app/api/v1/__init__.py`:
```python
from backend.app.api.v1.species import router as species_router
api_v1_router.include_router(species_router)
```

## 4. Expected Request Format
- Method: `POST`
- Path: `/api/v1/species/identify`
- Content-Type: `multipart/form-data`
- Field: `file` (binary image file)
- Query param: `top_k=3` (default 3)

## 5. Expected Response Format
```json
{
  "species": "Amphiprion clarkii",
  "common_name": "Yellowtail clownfish",
  "family": "Pomacentridae",
  "confidence": 0.9412,
  "confidence_tier": "HIGH",
  "top_predictions": [
    {"species": "Amphiprion clarkii", "common_name": "Yellowtail clownfish", "family": "Pomacentridae", "confidence": 0.9412},
    {"species": "Plectroglyphidodon dickii", "common_name": "Blackbar damselfish", "family": "Pomacentridae", "confidence": 0.0381},
    {"species": "Chromis chrysura", "common_name": "Japanese damselfish", "family": "Pomacentridae", "confidence": 0.0125}
  ],
  "model_version": "1.0.0",
  "inference_time_ms": 14.5
}
```

## 6. Verification
Run:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/species/identify" -F "file=@sample.png"
```
'''
    (pkg_dir / "INTEGRATION_GUIDE.md").write_text(guide_content, encoding="utf-8")

    print(f"Integration package successfully created at: {pkg_dir}")
    print(f"Artifacts packaged:")
    for f in pkg_dir.rglob("*"):
        if f.is_file():
            print(f"  - {f.relative_to(pkg_dir)} ({f.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
