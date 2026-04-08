from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ....repositories.real_estate_repository import RealEstateMktRepository
from ....schemas.real_estate_schema import (
    RealEstateMktCreateSchema,
    RealEstateMktReadSchema,
)

router = APIRouter(prefix="/api/v1/real-estate", tags=["real-estate-market"])

@router.get("", response_model=List[RealEstateMktReadSchema])
async def get_all_listings(repo: RealEstateMktRepository = Depends()):
    """Get all real estate market records."""
    return repo.get_all()


@router.get("/{record_id}", response_model=RealEstateMktReadSchema)
async def get_listing(record_id: int, repo: RealEstateMktRepository = Depends()):
    """Get a specific real estate market record."""
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.get("/by-commune/{code_commune}", response_model=List[RealEstateMktReadSchema])
async def get_by_commune(code_commune: int, repo: RealEstateMktRepository = Depends()):
    """Get all records for a specific commune."""
    return repo.get_by_commune(code_commune)


@router.get("/by-year/{annee}", response_model=List[RealEstateMktReadSchema])
async def get_by_year(annee: int, repo: RealEstateMktRepository = Depends()):
    """Get all records for a specific year."""
    return repo.get_by_year(annee)


@router.get("/trend/{code_commune}", response_model=List[RealEstateMktReadSchema])
async def get_price_trend(code_commune: int, repo: RealEstateMktRepository = Depends()):
    """Get price trend for a commune over years."""
    return repo.get_trend_by_commune(code_commune)


@router.get("/analytics/average-by-year/{annee}", response_model=dict)
async def get_average_price(annee: int, repo: RealEstateMktRepository = Depends()):
    """Get average price per m2 for all communes in a year."""
    result = repo.get_average_price_by_year(annee)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
