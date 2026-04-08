from sqlalchemy import String, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class TaxeFonciere(Base):
    """SQLAlchemy model for taxe foncière data."""

    __tablename__ = "taxe_fonciere"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dept: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    nom_commune: Mapped[str] = mapped_column(String(255), nullable=False)
    insee_com: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    code_postal: Mapped[str] = mapped_column(String(5), nullable=True, index=True)
    annee_cible: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    annee_source: Mapped[int] = mapped_column(Integer, nullable=False)
    est_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    taux_global_tfb: Mapped[float] = mapped_column(Float, nullable=True)
    taux_global_tfnb: Mapped[float] = mapped_column(Float, nullable=True)
    taux_plein_teom: Mapped[float] = mapped_column(Float, nullable=True)
    taux_global_th: Mapped[float] = mapped_column(Float, nullable=True)
