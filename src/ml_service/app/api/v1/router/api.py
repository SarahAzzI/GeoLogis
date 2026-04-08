from fastapi import APIRouter
from ..endpoints.training_endpoints import router as training_router
from ..endpoints.taxe_fonciere_endpoints import router as taxe_fonciere_router
from ..endpoints.real_estate_endpoints import router as real_estate_router
from ..endpoints.communes_endpoints import router as communes_router
from ..endpoints.inflation_rate_endpoints import router as inflation_router
from ..endpoints.prediction_endpoints import router as prediction_router

api_router = APIRouter()

api_router.include_router(training_router)
api_router.include_router(taxe_fonciere_router)
api_router.include_router(real_estate_router)
api_router.include_router(communes_router)
api_router.include_router(inflation_router)
api_router.include_router(prediction_router)