from pydantic import BaseModel, Field
from typing import Optional


class RealEstateMktCreateSchema(BaseModel):
    """Schema for creating real estate market records."""

    code_commune: int = Field(ge=1)
    annee: int = Field(ge=2020, le=2025)
    prix_m2: Optional[float] = Field(default=None, ge=0.0)
    surface_reelle_bati: Optional[float] = Field(default=None, ge=0.0)
    nb_ventes: Optional[int] = Field(default=None, ge=0)

    class Config:
        from_attributes = True


class RealEstateMktReadSchema(BaseModel):
    """Schema for reading real estate market records."""

    id: int
    code_commune: int
    annee: int
    prix_m2: Optional[float] = None
    surface_reelle_bati: Optional[float] = None
    nb_ventes: Optional[int] = None

    class Config:
        from_attributes = True
