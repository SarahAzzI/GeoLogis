import pandas as pd
from fastapi import Depends
from sqlalchemy.orm import Session

from ..model.database import get_db
from ..repositories.training_repository import TrainingRepository
from ..schemas.training_schema import TrainingReadSchema, TrainingCreateSchema


def convert_nan_to_none(row_dict: dict) -> dict:
    """Convert NaN values in a dictionary to None."""
    return {k: None if pd.isna(v) else v for k, v in row_dict.items()}


def convert_commune_row(row_dict: dict) -> dict:
    """Convert commune row data, handling type conversions."""
    row_dict = convert_nan_to_none(row_dict)
    
    # Convert code_insee to string (handles both numeric and alphanumeric codes)
    if "code_insee" in row_dict and row_dict["code_insee"] is not None:
        row_dict["code_insee"] = str(int(row_dict["code_insee"])) if isinstance(row_dict["code_insee"], float) else str(row_dict["code_insee"])
    
    # Convert numeric string fields to strings
    string_fields = ["code_postal", "dep_code", "reg_code", "zone_emploi"]
    for field in string_fields:
        if field in row_dict and row_dict[field] is not None:
            row_dict[field] = str(int(row_dict[field])) if isinstance(row_dict[field], float) else str(row_dict[field])
    
    # Ensure numeric fields are proper types
    if "annee" in row_dict and row_dict["annee"] is not None:
        row_dict["annee"] = int(row_dict["annee"])
    if "population" in row_dict and row_dict["population"] is not None:
        row_dict["population"] = int(row_dict["population"]) if row_dict["population"] else None
    
    return row_dict


def convert_real_estate_row(row_dict: dict) -> dict:
    """Convert real estate row data, handling type conversions."""
    row_dict = convert_nan_to_none(row_dict)
    
    # Ensure numeric fields are proper types
    if "code_commune" in row_dict and row_dict["code_commune"] is not None:
        row_dict["code_commune"] = int(row_dict["code_commune"])
    if "annee" in row_dict and row_dict["annee"] is not None:
        row_dict["annee"] = int(row_dict["annee"])
    if "prix_m2" in row_dict and row_dict["prix_m2"] is not None:
        row_dict["prix_m2"] = float(row_dict["prix_m2"]) if row_dict["prix_m2"] else None
    if "surface_reelle_bati" in row_dict and row_dict["surface_reelle_bati"] is not None:
        row_dict["surface_reelle_bati"] = float(row_dict["surface_reelle_bati"]) if row_dict["surface_reelle_bati"] else None
    if "nb_ventes" in row_dict and row_dict["nb_ventes"] is not None:
        row_dict["nb_ventes"] = int(row_dict["nb_ventes"]) if row_dict["nb_ventes"] else None
    
    return row_dict


def convert_inflation_row(row_dict: dict) -> dict:
    """Convert inflation rate row data, handling type conversions."""
    row_dict = convert_nan_to_none(row_dict)
    
    # Extract only required fields for InflationRateCreateSchema
    result = {}
    
    # Extract year
    if "annee" in row_dict and row_dict["annee"] is not None:
        result["annee"] = int(row_dict["annee"])
    
    # Extract inflation rate
    if "taux_inflation" in row_dict and row_dict["taux_inflation"] is not None:
        result["taux_inflation"] = float(row_dict["taux_inflation"])
    
    # Optional sources field
    if "sources" in row_dict and row_dict["sources"] is not None:
        result["sources"] = str(row_dict["sources"])
    
    return result


def get_training_service(db: Session = Depends(get_db)) -> "TrainingService":
    """Dependency function to get training service instance."""
    return TrainingService(repo=TrainingRepository(db=db))


class TrainingService:
    def __init__(self, repo = TrainingRepository):
        self.repo = repo
    
    def get_training_data(self):
        return self.repo.get_training_data()
    
    def add_data(self, training = TrainingCreateSchema):
        return self.repo.feed_data(training)