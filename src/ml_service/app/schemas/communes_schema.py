from pydantic import BaseModel, Field
from typing import Optional


class CommuneCreateSchema(BaseModel):
    """Schema for creating commune records."""

    code_insee: str = Field(min_length=1, max_length=10)
    nom_standard: str = Field(min_length=1)
    code_postal: Optional[str] = Field(default=None, max_length=5)
    annee: int = Field(ge=2020, le=2025)
    dep_code: Optional[str] = Field(default=None, max_length=5)
    dep_nom: Optional[str] = Field(default=None)
    reg_code: Optional[str] = Field(default=None, max_length=5)
    reg_nom: Optional[str] = Field(default=None)
    population: Optional[int] = Field(default=None, ge=0)
    densite: Optional[float] = Field(default=None, ge=0.0)
    superficie_km2: Optional[float] = Field(default=None, ge=0.0)
    latitude_centre: Optional[float] = Field(default=None)
    longitude_centre: Optional[float] = Field(default=None)
    zone_emploi: Optional[str] = Field(default=None, max_length=50)

    class Config:
        from_attributes = True


class CommuneReadSchema(BaseModel):
    """Schema for reading commune records."""

    id: int
    code_insee: str
    nom_standard: str
    code_postal: Optional[str] = None
    annee: int
    dep_code: Optional[str] = None
    dep_nom: Optional[str] = None
    reg_code: Optional[str] = None
    reg_nom: Optional[str] = None
    population: Optional[int] = None
    densite: Optional[float] = None
    superficie_km2: Optional[float] = None
    latitude_centre: Optional[float] = None
    longitude_centre: Optional[float] = None
    zone_emploi: Optional[str] = None

    class Config:
        from_attributes = True


class CommuneFilterSchema(BaseModel):
    """Schema for filtering commune queries."""

    code_insee: Optional[str] = Field(default=None)
    code_postal: Optional[str] = Field(default=None)
    annee: Optional[int] = Field(default=None, ge=2020, le=2025)
    dep_code: Optional[str] = Field(default=None)
    reg_code: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True
