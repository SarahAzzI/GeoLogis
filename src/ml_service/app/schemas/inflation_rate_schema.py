from pydantic import BaseModel, Field
from typing import Optional


class InflationRateCreateSchema(BaseModel):
    """Schema for creating inflation rate records."""

    annee: int = Field(ge=2020, le=2025)
    taux_inflation: float = Field(ge=-10, le=100)
    sources: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class InflationRateReadSchema(BaseModel):
    """Schema for reading inflation rate records."""

    id: int
    annee: int
    taux_inflation: float
    sources: Optional[str] = None

    class Config:
        from_attributes = True
