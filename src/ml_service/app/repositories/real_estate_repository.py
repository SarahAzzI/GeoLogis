from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from ..model.database import get_db
from ..model.real_estate import RealEstateMkt
from ..schemas.real_estate_schema import RealEstateMktCreateSchema

logger = logging.getLogger(__name__)


class RealEstateMktRepository:
    """Repository for real estate market data operations."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_all(self) -> List[RealEstateMkt]:
        """Get all real estate market records."""
        return self.db.query(RealEstateMkt).all()

    def get_by_id(self, record_id: int) -> Optional[RealEstateMkt]:
        """Get a record by ID."""
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.id == record_id
        ).first()

    def get_by_commune(self, code_commune: int) -> List[RealEstateMkt]:
        """Get all records for a specific commune."""
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.code_commune == code_commune
        ).all()

    def get_by_year(self, annee: int) -> List[RealEstateMkt]:
        """Get all records for a specific year."""
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.annee == annee
        ).all()

    def get_by_commune_and_year(
        self, code_commune: int, annee: int
    ) -> Optional[RealEstateMkt]:
        """Get record for a specific commune and year."""
        return self.db.query(RealEstateMkt).filter(
            (RealEstateMkt.code_commune == code_commune) &
            (RealEstateMkt.annee == annee)
        ).first()

    def get_trend_by_commune(self, code_commune: int) -> List[RealEstateMkt]:
        """Get price trend for a commune (sorted by year)."""
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.code_commune == code_commune
        ).order_by(RealEstateMkt.annee).all()

    def get_average_price_by_year(self, annee: int) -> dict:
        """Get average price per m2 for all communes in a year."""
        result = self.db.query(
            func.avg(RealEstateMkt.prix_m2).label("avg_prix_m2"),
            func.avg(RealEstateMkt.nb_ventes).label("avg_ventes"),
        ).filter(RealEstateMkt.annee == annee).first()

        return {
            "annee": annee,
            "avg_prix_m2": round(float(result.avg_prix_m2), 2) if result.avg_prix_m2 else None,
            "avg_ventes": round(float(result.avg_ventes), 2) if result.avg_ventes else None,
        }

    def create_bulk(self, schemas: List[RealEstateMktCreateSchema]) -> int:
        """Bulk insert multiple real estate records from schemas."""
        try:
            records = [
                RealEstateMkt(
                    code_commune=int(schema.code_commune),
                    annee=int(schema.annee),
                    prix_m2=float(schema.prix_m2) if schema.prix_m2 else None,
                    surface_reelle_bati=float(schema.surface_reelle_bati) if schema.surface_reelle_bati else None,
                    nb_ventes=int(schema.nb_ventes) if schema.nb_ventes else None,
                )
                for schema in schemas
            ]
            self.db.add_all(records)
            self.db.commit()
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0
