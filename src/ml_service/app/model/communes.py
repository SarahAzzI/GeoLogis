from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Commune(Base):
    """SQLAlchemy model for commune geographic and demographic data."""

    __tablename__ = "communes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code_insee: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    nom_standard: Mapped[str] = mapped_column(String(255), nullable=False)
    code_postal: Mapped[str] = mapped_column(String(5), nullable=True, index=True)
    annee: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    dep_code: Mapped[str] = mapped_column(String(5), nullable=True, index=True)
    dep_nom: Mapped[str] = mapped_column(String(255), nullable=True)
    reg_code: Mapped[str] = mapped_column(String(5), nullable=True)
    reg_nom: Mapped[str] = mapped_column(String(255), nullable=True)
    population: Mapped[int] = mapped_column(Integer, nullable=True)
    densite: Mapped[float] = mapped_column(Float, nullable=True)
    superficie_km2: Mapped[float] = mapped_column(Float, nullable=True)
    latitude_centre: Mapped[float] = mapped_column(Float, nullable=True)
    longitude_centre: Mapped[float] = mapped_column(Float, nullable=True)
    zone_emploi: Mapped[str] = mapped_column(String(50), nullable=True)
