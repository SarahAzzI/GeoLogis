from pydantic import BaseModel, Field
from typing import Optional


class TaxeFonciereCreateSchema(BaseModel):
    """Schema for creating taxe foncière records."""

    dept: str = Field(min_length=1, max_length=5)
    nom_commune: str = Field(min_length=1)
    insee_com: str = Field(min_length=5, max_length=5)
    annee_cible: int = Field(ge=2021, le=2024)
    annee_source: int = Field(ge=2021, le=2024)
    est_fallback: bool = Field(default=False)
    taux_global_tfb: Optional[float] = Field(default=None, ge=0.0)
    taux_global_tfnb: Optional[float] = Field(default=None, ge=0.0)
    taux_plein_teom: Optional[float] = Field(default=None, ge=0.0)
    taux_global_th: Optional[float] = Field(default=None, ge=0.0)

    class Config:
        from_attributes = True


class TaxeFonciereReadSchema(BaseModel):
    """Schema for reading taxe foncière records."""

    id: int
    dept: str
    nom_commune: str
    insee_com: str
    annee_cible: int
    annee_source: int
    est_fallback: bool
    taux_global_tfb: Optional[float] = None
    taux_global_tfnb: Optional[float] = None
    taux_plein_teom: Optional[float] = None
    taux_global_th: Optional[float] = None

    class Config:
        from_attributes = True


class TaxeFonciereFilterSchema(BaseModel):
    """Schema for filtering taxe foncière queries."""

    dept: Optional[str] = Field(default=None)
    insee_com: Optional[str] = Field(default=None)
    annee_cible: Optional[int] = Field(default=None, ge=2021, le=2024)
    annee_source: Optional[int] = Field(default=None, ge=2021, le=2024)
    est_fallback: Optional[bool] = Field(default=None)

    class Config:
        from_attributes = True
