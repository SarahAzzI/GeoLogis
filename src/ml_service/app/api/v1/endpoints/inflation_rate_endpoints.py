from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ....repositories.inflation_rate_repository import InflationRateRepository
from ....schemas.inflation_rate_schema import (
    InflationRateCreateSchema,
    InflationRateReadSchema,
)

router = APIRouter(prefix="/api/v1/inflation", tags=["inflation-rates"])

@router.get("", response_model=List[InflationRateReadSchema])
async def get_all_rates(repo: InflationRateRepository = Depends()):
    """Get all inflation rate records."""
    return repo.get_all()


@router.get("/{record_id}", response_model=InflationRateReadSchema)
async def get_rate(record_id: int, repo: InflationRateRepository = Depends()):
    """Get a specific inflation rate record."""
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.get("/by-year/{annee}", response_model=InflationRateReadSchema)
async def get_by_year(annee: int, repo: InflationRateRepository = Depends()):
    """Get inflation rate for a specific year."""
    record = repo.get_by_year(annee)
    if not record:
        raise HTTPException(status_code=404, detail="No data for this year")
    return record


@router.get("/range/{annee_start}/{annee_end}", response_model=List[InflationRateReadSchema])
async def get_year_range(
    annee_start: int,
    annee_end: int,
    repo: InflationRateRepository = Depends()
):
    """Get inflation rates for a range of years."""
    return repo.get_year_range(annee_start, annee_end)


@router.get("/analytics/average/{annee_start}/{annee_end}", response_model=dict)
async def get_average_inflation(
    annee_start: int,
    annee_end: int,
    repo: InflationRateRepository = Depends()
):
    """Get average inflation rate for a period."""
    average = repo.get_average_inflation(annee_start, annee_end)
    return {
        "period_start": annee_start,
        "period_end": annee_end,
        "average_inflation": average,
    }
