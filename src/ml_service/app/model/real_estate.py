from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class RealEstateMkt(Base):
    """SQLAlchemy model for real estate market data."""

    __tablename__ = "real_estate_market"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code_commune: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    annee: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prix_m2: Mapped[float] = mapped_column(Float, nullable=True)
    surface_reelle_bati: Mapped[float] = mapped_column(Float, nullable=True)
    nb_ventes: Mapped[int] = mapped_column(Integer, nullable=True)
