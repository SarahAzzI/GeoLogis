from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from ..model.database import get_db
from ..model.inflation_rate import InflationRate
from ..schemas.inflation_rate_schema import InflationRateCreateSchema

logger = logging.getLogger(__name__)


class InflationRateRepository:
    """Repository for inflation rate data operations."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_all(self) -> List[InflationRate]:
        """Get all inflation rate records."""
        return self.db.query(InflationRate).order_by(InflationRate.annee).all()

    def get_by_id(self, record_id: int) -> Optional[InflationRate]:
        """Get a record by ID."""
        return self.db.query(InflationRate).filter(
            InflationRate.id == record_id
        ).first()

    def get_by_year(self, annee: int) -> Optional[InflationRate]:
        """Get inflation rate for a specific year."""
        return self.db.query(InflationRate).filter(
            InflationRate.annee == annee
        ).first()

    def get_year_range(self, annee_start: int, annee_end: int) -> List[InflationRate]:
        """Get inflation rates for a range of years."""
        return self.db.query(InflationRate).filter(
            and_(
                InflationRate.annee >= annee_start,
                InflationRate.annee <= annee_end,
            )
        ).order_by(InflationRate.annee).all()

    def get_average_inflation(self, annee_start: int, annee_end: int) -> float:
        """Get average inflation rate for a period."""
        result = self.db.query(
            func.avg(InflationRate.taux_inflation).label("avg_taux")
        ).filter(
            and_(
                InflationRate.annee >= annee_start,
                InflationRate.annee <= annee_end,
            )
        ).first()

        return round(float(result.avg_taux), 4) if result.avg_taux else 0.0

    def create_bulk(self, schemas: List[InflationRateCreateSchema]) -> int:
        """Bulk insert multiple inflation rate records from schemas."""
        try:
            records = [
                InflationRate(
                    annee=int(schema.annee),
                    taux_inflation=float(schema.taux_inflation),
                    sources=schema.sources if hasattr(schema, 'sources') and schema.sources else None,
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
