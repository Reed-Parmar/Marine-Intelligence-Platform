"""
API v1 Router registry.
"""

from fastapi import APIRouter
from backend.app.api.v1 import (
    alerts,
    analysis,
    auth,
    datasets,
    edna,
    fisheries,
    marine,
    ml,
    ocean,
    otolith,
    species,
    uploads,
    users
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["Users"])
api_v1_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads & Ingestion"])
api_v1_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_v1_router.include_router(marine.router, prefix="/marine", tags=["Unified Marine"])
api_v1_router.include_router(ocean.router, prefix="/ocean", tags=["Oceanography"])
api_v1_router.include_router(fisheries.router, prefix="/fisheries", tags=["Fisheries"])
api_v1_router.include_router(species.router, prefix="/species", tags=["Species & Taxonomy"])
api_v1_router.include_router(edna.router, prefix="/edna", tags=["eDNA"])
api_v1_router.include_router(otolith.router, prefix="/otolith", tags=["Otolith"])
api_v1_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_v1_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
api_v1_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
