# Marine Species Identification - Integration Guide

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
