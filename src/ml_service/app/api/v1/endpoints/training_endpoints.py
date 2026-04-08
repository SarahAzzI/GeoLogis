from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
import pandas as pd
import logging
from typing import List

from ....services.training_service import (
    TrainingService,
    get_training_service,
    convert_nan_to_none,
    convert_commune_row,
    convert_real_estate_row,
    convert_inflation_row,
)
from ....repositories.real_estate_repository import RealEstateMktRepository
from ....repositories.communes_repository import CommuneRepository
from ....repositories.inflation_rate_repository import InflationRateRepository
from ....schemas.training_schema import TrainingReadSchema, TrainingCreateSchema
from ....schemas.real_estate_schema import RealEstateMktCreateSchema
from ....schemas.communes_schema import CommuneCreateSchema
from ....schemas.inflation_rate_schema import InflationRateCreateSchema
from ....model.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/training", tags=["training"])

# Base data directory
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "data_pipeline" / "merge" / "raw"

@router.get("/", description="Get all training data")
async def get_training_data(db: Session = Depends(get_db)):
    """Get all training records."""
    service = get_training_service(db)
    return {"data": service.get_training_data()}


@router.get("/stats", description="Get training data statistics")
async def get_training_stats(db: Session = Depends(get_db)):
    """Get statistics about training data."""
    service = get_training_service(db)
    stats = service.repo.get_statistics()
    return stats


@router.get("/{record_id}", description="Get training record by ID")
async def get_training_by_id(record_id: int, db: Session = Depends(get_db)):
    """Get a specific training record by ID."""
    service = get_training_service(db)
    record = service.repo.get_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Training record {record_id} not found")
    return record


@router.get("/commune/{code_commune}", description="Get training records by commune")
async def get_training_by_commune(code_commune: int, db: Session = Depends(get_db)):
    """Get all training records for a specific commune."""
    service = get_training_service(db)
    records = service.repo.get_by_commune(code_commune)
    return {"count": len(records), "data": records}


@router.get("/year/{annee}", description="Get training records by year")
async def get_training_by_year(annee: int, db: Session = Depends(get_db)):
    """Get all training records for a specific year."""
    service = get_training_service(db)
    records = service.repo.get_by_year(annee)
    return {"count": len(records), "data": records}


@router.post("/batch", description="Add multiple training records")
async def add_training_batch(
    records: List[TrainingCreateSchema],
    db: Session = Depends(get_db)
):
    """Add multiple training records at once."""
    service = get_training_service(db)
    count = service.repo.feed_batch(records)
    return {"status": "success", "records_added": count}


@router.delete("/{record_id}", description="Delete training record")
async def delete_training_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a training record by ID."""
    service = get_training_service(db)
    success = service.repo.delete(record_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Training record {record_id} not found")
    return {"status": "success", "message": f"Record {record_id} deleted"}


@router.post("/load/real-estate")
async def load_real_estate_training_data(db: Session = Depends(get_db)):
    """Load real estate training data from CSVs (2020-2025)."""
    repo = RealEstateMktRepository(db=db)
    total_loaded = 0
    
    for year in range(2020, 2026):
        csv_file = BASE_DIR / f"csv_agg_{year}.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            continue
        
        logger.info(f"Processing {csv_file}")
        df = pd.read_csv(str(csv_file), sep=";", dtype={"code_commune": str})
        logger.info(f"Rows loaded: {len(df)}")
        
        df = df.dropna(subset=["code_commune", "annee"])
        logger.info(f"After dropna: {len(df)} rows")
        
        # Filter to only numeric code_commune values
        df["code_commune"] = pd.to_numeric(df["code_commune"], errors="coerce")
        df = df.dropna(subset=["code_commune"])
        logger.info(f"After numeric filtering: {len(df)} rows")
        
        try:
            records = [
                RealEstateMktCreateSchema(**convert_real_estate_row(row.to_dict()))
                for _, row in df.iterrows()
            ]
            logger.info(f"Records created: {len(records)}")
        except Exception as e:
            logger.error(f"Error creating records: {e}", exc_info=True)
            records = []
        
        if records:
            count = repo.create_bulk(records)
            logger.info(f"Records inserted: {count}")
            total_loaded += count
        else:
            logger.warning(f"No records created for {year}")
    
    return {"status": "success", "source": "real_estate", "total": total_loaded}


@router.post("/load/communes")
async def load_communes_training_data(db: Session = Depends(get_db)):
    """Load communes training data from CSV."""
    repo = CommuneRepository(db=db)
    csv_file = BASE_DIR / "csv_communes_all.csv"
    
    if not csv_file.exists():
        logger.error(f"File not found: {csv_file}")
        raise HTTPException(status_code=404, detail=f"File not found: {csv_file}")
    
    logger.info(f"Processing {csv_file}")
    df = pd.read_csv(
        str(csv_file),
        sep=";",
        dtype={
            "code_insee": str,
            "dep_code": str,
            "reg_code": str,
            "code_postal": str,
            "zone_emploi": str,
            "canton_code": str,
            "epci_code": str,
            "code_insee_centre_zone_emploi": str,
        },
    )
    logger.info(f"Rows loaded: {len(df)}")
    
    required_cols = [
        "code_insee", "nom_standard", "annee", "code_postal",
        "dep_code", "dep_nom", "reg_code", "reg_nom",
        "population", "densite", "superficie_km2",
        "latitude_centre", "longitude_centre", "zone_emploi"
    ]
    available_cols = [col for col in required_cols if col in df.columns]
    df = df[available_cols]
    df = df.dropna(subset=["code_insee", "nom_standard", "annee"])
    logger.info(f"After dropna: {len(df)} rows")
    
    try:
        records = [
            CommuneCreateSchema(**convert_commune_row(row.to_dict()))
            for _, row in df.iterrows()
        ]
        logger.info(f"Records created: {len(records)}")
    except Exception as e:
        logger.error(f"Error creating records: {e}", exc_info=True)
        records = []
    
    total_loaded = 0
    if records:
        total_loaded = repo.create_bulk(records)
        logger.info(f"Records inserted: {total_loaded}")
    else:
        logger.warning("No records created")

    return {"status": "success", "source": "communes", "total": total_loaded}


@router.post("/load/inflation")
async def load_inflation_training_data(db: Session = Depends(get_db)):
    """Load inflation rate training data from CSV."""
    repo = InflationRateRepository(db=db)
    csv_file = BASE_DIR / "taux_inflation.csv"
    
    if not csv_file.exists():
        csv_file = BASE_DIR.parent.parent / "flatfiles" / "taux_inflation.csv"
    
    if not csv_file.exists():
        logger.error("Inflation rates CSV not found in either location")
        raise HTTPException(status_code=404, detail="Inflation rates CSV not found")
    
    logger.info(f"Processing {csv_file}")
    df = pd.read_csv(str(csv_file), sep=";")
    logger.info(f"Rows loaded: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Handle Date column - extract year from date
    if "Date" in df.columns:
        logger.info("Parsing Date column to extract year")
        df["annee"] = pd.to_datetime(df["Date"], errors="coerce").dt.year
        logger.info(f"Extracted years: {df['annee'].unique()}")
    elif "annee" not in df.columns:
        logger.error(f"No date or year column found. Available columns: {list(df.columns)}")
        raise HTTPException(status_code=400, detail=f"No date or year column found in CSV. Available: {list(df.columns)}")
    
    # Rename inflation column if needed
    # Handle both ASCII apostrophe and Unicode right single quotation mark
    inflation_col = None
    for col in ["Taux d'inflation", "Taux d\u2019inflation", "taux_inflation", "inflation_rate", "taux"]:
        if col in df.columns:
            inflation_col = col
            logger.info(f"Found inflation column: {col}")
            break
    
    if not inflation_col:
        logger.error(f"No inflation rate column found. Available columns: {list(df.columns)}")
        raise HTTPException(status_code=400, detail=f"No inflation rate column found in CSV. Available: {list(df.columns)}")
    
    # Rename columns for consistency
    df = df.rename(columns={inflation_col: "taux_inflation"})
    
    df = df.dropna(subset=["annee", "taux_inflation"])
    logger.info(f"After dropna: {len(df)} rows")
    
    try:
        records = [
            InflationRateCreateSchema(**convert_inflation_row(row.to_dict()))
            for _, row in df.iterrows()
        ]
        logger.info(f"Records created: {len(records)}")
    except Exception as e:
        logger.error(f"Error creating records: {e}", exc_info=True)
        records = []
    
    total_loaded = 0
    if records:
        total_loaded = repo.create_bulk(records)
        logger.info(f"Records inserted: {total_loaded}")
    else:
        logger.warning("No records created")

    return {"status": "success", "source": "inflation", "total": total_loaded}


@router.post("/load/all")
async def load_all_training_data(db: Session = Depends(get_db)):
    """Load all training data from CSVs."""
    results = {}
    
    try:
        results["real_estate"] = await load_real_estate_training_data(db)
    except Exception as e:
        results["real_estate"] = {"status": "error", "error": str(e)}
    
    try:
        results["communes"] = await load_communes_training_data(db)
    except Exception as e:
        results["communes"] = {"status": "error", "error": str(e)}
    
    try:
        results["inflation"] = await load_inflation_training_data(db)
    except Exception as e:
        results["inflation"] = {"status": "error", "error": str(e)}
    
    return results


@router.post("/process/validate")
async def validate_training_data(db: Session = Depends(get_db)):
    """Validate and get quality report of training data."""
    from ....services.data_processor_service import DataProcessorService
    
    # Get all data from various sources
    service = get_training_service(db)
    real_estate_repo = RealEstateMktRepository(db=db)
    communes_repo = CommuneRepository(db=db)
    inflation_repo = InflationRateRepository(db=db)
    
    # Combine data for analysis
    re_data = real_estate_repo.get_all()
    comm_data = communes_repo.get_all()
    infl_data = inflation_repo.get_all()
    
    validation_results = {
        "real_estate_records": len(re_data),
        "communes_records": len(comm_data),
        "inflation_records": len(infl_data),
        "total_records": len(re_data) + len(comm_data) + len(infl_data)
    }
    
    logger.info(f"Data validation: {validation_results}")
    return validation_results


@router.get("/records/count")
async def get_training_record_count(db: Session = Depends(get_db)):
    """Get count of all training records."""
    service = get_training_service(db)
    count = service.repo.count_records()
    return {"total_records": count}


@router.post("/process/split")
async def create_training_splits(
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    db: Session = Depends(get_db)
):
    """
    Create training, validation, and test splits from training data.
    
    Args:
        train_ratio: Ratio for training set (default: 0.7)
        val_ratio: Ratio for validation set (default: 0.15)
        test_ratio: Ratio for test set (default: 0.15)
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
        raise HTTPException(status_code=400, detail="Ratios must sum to 1.0")
    
    from ....services.data_processor_service import DataProcessorService
    
    service = get_training_service(db)
    records = service.get_training_data()
    
    if not records:
        raise HTTPException(status_code=400, detail="No training data available")
    
    # Convert to dataframe
    df = pd.DataFrame([record.__dict__ for record in records])
    
    # Create splits
    processor = DataProcessorService()
    train_df, val_df, test_df = processor.create_training_splits(
        df,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio
    )
    
    return {
        "status": "success",
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "total_samples": len(df)
    }

