from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from ....services.taxe_fonciere_service import TaxeFonciereService
from ....repositories.taxe_fonciere_repository import TaxeFonciereRepository
from ....schemas.taxe_fonciere_schema import (
    TaxeFonciereCreateSchema,
    TaxeFonciereReadSchema,
    TaxeFonciereFilterSchema,
)
from ....model.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/taxe_fonciere", tags=["taxe_fonciere"])

class SyncResponse(BaseModel):
    """Response model for sync operations."""
    success: bool
    message: str
    records_fetched: Optional[int] = None
    records_saved: Optional[int] = None
    fallback_count: Optional[int] = None
    duration_seconds: float

@router.post("/sync", response_model=SyncResponse)
async def sync_taxe_fonciere():
    """
    Trigger a synchronization of taxe foncière data.
    
    This endpoint fetches the latest taxe foncière data from the API
    and updates the database. The operation runs synchronously.
    
    Returns:
        SyncResponse: Status and summary of the synchronization operation
    """
    service = TaxeFonciereService()
    result = service.sync_taxe_fonciere_data()

    if result["success"]:
        return SyncResponse(
            success=True,
            message=result.get("message", "Sync completed successfully"),
            records_fetched=result.get("records_fetched"),
            records_saved=result.get("records_saved"),
            fallback_count=result.get("fallback_count"),
            duration_seconds=result.get("duration_seconds", 0),
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Sync failed for unknown reason"),
        )

@router.get("", response_model=List[TaxeFonciereReadSchema])
async def get_all_records(db: Session = Depends(get_db)):
    """Get all taxe foncière records."""
    repo = TaxeFonciereRepository(db=db)
    return repo.get_all()

@router.get("/postal/{code_postal}", response_model=List[TaxeFonciereReadSchema])
async def get_by_postal_code(code_postal: str, db: Session = Depends(get_db)):
    """
    Get all taxe foncière records for a specific postal code.
    
    This is the primary endpoint for filtering taxe foncière data by geographic location.
    Returns all tax rates and information for municipalities in this postal code across all years.
    
    Parameters:
    - code_postal: The postal code (e.g., "75001", "69001")
    
    Returns:
    - List of taxe foncière records for this postal code
    """
    repo = TaxeFonciereRepository(db=db)
    records = repo.get_by_postal_code(code_postal)
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for postal code {code_postal}")
    return records

@router.get("/postal/{code_postal}/year/{annee_cible}", response_model=List[TaxeFonciereReadSchema])
async def get_by_postal_code_and_year(
    code_postal: str,
    annee_cible: int,
    db: Session = Depends(get_db)
):
    """
    Get taxe foncière records for a specific postal code and year.
    
    Filters records by postal code and target year to get precise tax rates
    for a specific geographic area and time period.
    
    Parameters:
    - code_postal: The postal code (e.g., "75001", "69001")
    - annee_cible: The target year (e.g., 2024, 2025)
    
    Returns:
    - List of taxe foncière records matching both postal code and year
    """
    repo = TaxeFonciereRepository(db=db)
    records = repo.get_by_postal_code(code_postal)
    filtered = [r for r in records if r.annee_cible == annee_cible]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No records found for postal code {code_postal} in year {annee_cible}"
        )
    return filtered

@router.get("/{record_id}", response_model=TaxeFonciereReadSchema)
async def get_record(record_id: int, db: Session = Depends(get_db)):
    """Get a specific taxe foncière record by ID."""
    repo = TaxeFonciereRepository(db=db)
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.get("/filter/by-department/{dept}", response_model=List[TaxeFonciereReadSchema])
async def get_by_department(dept: str, db: Session = Depends(get_db)):
    """Get all records for a specific department code."""
    repo = TaxeFonciereRepository(db=db)
    records = repo.get_by_dept(dept)
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for department {dept}")
    return records

@router.get("/filter/by-insee/{insee_com}", response_model=List[TaxeFonciereReadSchema])
async def get_by_insee_code(insee_com: str, db: Session = Depends(get_db)):
    """Get all records for a specific INSEE commune code."""
    repo = TaxeFonciereRepository(db=db)
    records = repo.get_by_insee(insee_com)
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for INSEE code {insee_com}")
    return records

@router.get("/filter/by-year/{annee_cible}", response_model=List[TaxeFonciereReadSchema])
async def get_by_year(annee_cible: int, db: Session = Depends(get_db)):
    """Get all records for a specific year."""
    repo = TaxeFonciereRepository(db=db)
    records = repo.get_by_year(annee_cible)
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for year {annee_cible}")
    return records

@router.get("/filter/by-dept-year/{dept}/{annee_cible}", response_model=List[TaxeFonciereReadSchema])
async def get_by_dept_and_year(
    dept: str,
    annee_cible: int,
    db: Session = Depends(get_db)
):
    """Get records for a specific department and year."""
    repo = TaxeFonciereRepository(db=db)
    records = repo.get_by_dept(dept)
    filtered = [r for r in records if r.annee_cible == annee_cible]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No records found for department {dept} in year {annee_cible}"
        )
    return filtered

@router.get("/analytics/fallback-count", response_model=int)
async def get_fallback_count(
    db: Session = Depends(get_db),
    postal_code: Optional[str] = None
):
    """
    Get count of records that used fallback years.
    
    Optional Parameters:
    - postal_code: Filter by specific postal code
    """
    repo = TaxeFonciereRepository(db=db)
    return repo.count_fallback(postal_code=postal_code)

@router.get("/analytics/average-rates/{annee_cible}", response_model=dict)
async def get_average_rates(
    annee_cible: int,
    db: Session = Depends(get_db),
    postal_code: Optional[str] = None
):
    """
    Get average tax rates for a specific year.
    
    Optional Parameters:
    - postal_code: Filter by specific postal code
    
    Returns average values for:
    - taux_global_tfb: Built property tax
    - taux_global_tfnb: Land/unbuilt property tax
    - taux_plein_teom: Waste management tax
    - taux_global_th: Residence tax
    """
    repo = TaxeFonciereRepository(db=db)
    result = repo.get_average_rates_by_year(annee_cible, postal_code=postal_code)
    if not result or all(v is None for v in result.values() if k != 'postal_code' for k, v in result.items()):
        raise HTTPException(
            status_code=404,
            detail=f"No data available for year {annee_cible}" + (f" in postal code {postal_code}" if postal_code else "")
        )
    return result
