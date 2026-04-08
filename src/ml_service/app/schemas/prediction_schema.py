from pydantic import BaseModel, Field
from typing import Optional, List


class PredictionInputSchema(BaseModel):
    """Schema for prediction input features."""
    
    annee: int = Field(ge=2020, le=2025)
    population: int = Field(ge=0)
    superficie_km2: float = Field(ge=0)
    zone_emploi: str
    taux_global_tfb: float = Field(ge=0)
    taux_global_tfnb: float = Field(ge=0)
    taux_plein_teom: float = Field(ge=0)
    taux_global_th: float = Field(ge=0)
    nb_ventes: int = Field(ge=0)
    densite: Optional[float] = Field(default=None, ge=0)
    ratio_taxe: Optional[float] = Field(default=None, ge=0)
    ventes_par_habitant: Optional[float] = Field(default=None, ge=0)
    taxe_x_population: Optional[float] = Field(default=None, ge=0)
    evolution_ventes: Optional[float] = None
    evolution_taxe: Optional[float] = None
    taxe_vs_moyenne_dep: Optional[float] = Field(default=None, ge=0)
    ventes_moyennes_dep: Optional[float] = Field(default=None, ge=0)
    dep_code: str
    reg_code: str
    code_postal: str

    class Config:
        from_attributes = True


class PredictionOutputSchema(BaseModel):
    """Schema for prediction output."""
    
    prediction: str = Field(description="Predicted class: 'hausse', 'baisse', or 'stable'")
    confidence: Optional[float] = Field(default=None, description="Prediction confidence score")
    features_used: int = Field(description="Number of features used in prediction")

    class Config:
        from_attributes = True


class Prediction2026Schema(BaseModel):
    """Schema for 2026 bulk predictions."""
    
    code_commune: int
    code_insee: str
    commune_name: str
    dep_code: str
    prediction: str
    population: Optional[int] = None
    taux_global_tfb: Optional[float] = None

    class Config:
        from_attributes = True


class Predictions2026ResultSchema(BaseModel):
    """Schema for 2026 predictions result."""
    
    year: int = 2026
    total_predictions: int
    predictions: List[Prediction2026Schema]
    hausse_count: int = 0
    baisse_count: int = 0
    stable_count: int = 0

    class Config:
        from_attributes = True


class PostalCodePredictionSchema(BaseModel):
    """Schema for postal code prediction result."""
    
    postal_code: str
    predicted_trend: str
    total_records: int
    records: List[Prediction2026Schema]
    hausse_count: int = 0
    baisse_count: int = 0
    stable_count: int = 0
    year: int = 2026

    class Config:
        from_attributes = True


class ModelStatusSchema(BaseModel):
    """Schema for model training status."""
    
    is_trained: bool
    accuracy: Optional[float] = None
    total_training_samples: int = 0
    message: str
