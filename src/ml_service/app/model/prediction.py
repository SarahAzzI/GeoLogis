from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Prediction(Base):
    """SQLAlchemy model for storing predictions."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code_commune: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    population: Mapped[int] = mapped_column(Integer, nullable=False)
    superficie_km2: Mapped[float] = mapped_column(Float, nullable=False)
    zone_emploi: Mapped[str] = mapped_column(String(100), nullable=False)
    taux_global_tfb: Mapped[float] = mapped_column(Float, nullable=False)
    taux_global_tfnb: Mapped[float] = mapped_column(Float, nullable=False)
    taux_plein_teom: Mapped[float] = mapped_column(Float, nullable=False)
    taux_global_th: Mapped[float] = mapped_column(Float, nullable=False)
    nb_ventes: Mapped[int] = mapped_column(Integer, nullable=False)
    densite: Mapped[float] = mapped_column(Float, nullable=True)
    ratio_taxe: Mapped[float] = mapped_column(Float, nullable=True)
    ventes_par_habitant: Mapped[float] = mapped_column(Float, nullable=True)
    taxe_x_population: Mapped[float] = mapped_column(Float, nullable=True)
    evolution_ventes: Mapped[float] = mapped_column(Float, nullable=True)
    evolution_taxe: Mapped[float] = mapped_column(Float, nullable=True)
    taxe_vs_moyenne_dep: Mapped[float] =  mapped_column(Float, nullable=True)
    ventes_moyennes_dep: Mapped[float] = mapped_column(Float, nullable=True)
    dep_code: Mapped[str] = mapped_column(String(10), nullable=False)
    reg_code: Mapped[str] = mapped_column(String(10), nullable=False)
    code_postal: Mapped[str] = mapped_column(String(10), nullable=False)
    prediction: Mapped[str] = mapped_column(String(50), nullable=False)
