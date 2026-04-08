from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class InflationRate(Base):
    """SQLAlchemy model for inflation rate data."""

    __tablename__ = "inflation_rates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    annee: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    taux_inflation: Mapped[float] = mapped_column(Float, nullable=False)
    sources: Mapped[str] = mapped_column(String(255), nullable=True)
