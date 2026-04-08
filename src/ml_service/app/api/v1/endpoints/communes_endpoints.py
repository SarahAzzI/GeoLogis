from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ....repositories.communes_repository import CommuneRepository
from ....schemas.communes_schema import (
    CommuneCreateSchema,
    CommuneReadSchema,
    CommuneFilterSchema,
)

router = APIRouter(prefix="/api/v1/communes", tags=["communes"])

@router.get("", response_model=List[CommuneReadSchema])
async def get_all_communes(repo: CommuneRepository = Depends()):
    """Get all commune records."""
    return repo.get_all()

@router.get("/{record_id}", response_model=CommuneReadSchema)
async def get_commune(record_id: int, repo: CommuneRepository = Depends()):
    """Get a specific commune record."""
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.get("/by-insee/{code_insee}", response_model=List[CommuneReadSchema])
async def get_by_insee(code_insee: str, repo: CommuneRepository = Depends()):
    """Get all records for a specific INSEE code."""
    return repo.get_by_insee(code_insee)


@router.get("/by-postal/{code_postal}", response_model=List[CommuneReadSchema])
async def get_by_postal_code(code_postal: str, repo: CommuneRepository = Depends()):
    """Get all communes for a specific postal code."""
    return repo.get_by_postal_code(code_postal)


@router.get("/by-department/{dep_code}", response_model=List[CommuneReadSchema])
async def get_by_department(dep_code: str, repo: CommuneRepository = Depends()):
    """Get all communes in a department."""
    return repo.get_by_department(dep_code)


@router.get("/by-region/{reg_code}", response_model=List[CommuneReadSchema])
async def get_by_region(reg_code: str, repo: CommuneRepository = Depends()):
    """Get all communes in a region."""
    return repo.get_by_region(reg_code)


@router.post("/filter/advanced", response_model=List[CommuneReadSchema])
async def filter_communes(
    filters: CommuneFilterSchema,
    repo: CommuneRepository = Depends()
):
    """Filter communes using multiple criteria."""
    return repo.filter_records(filters)
    