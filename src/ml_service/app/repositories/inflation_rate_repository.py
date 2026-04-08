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
            logger.info(f"Bulk inserted {len(records)} inflation rate records")
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0

    def add_single(self, schema: InflationRateCreateSchema) -> Optional[InflationRate]:
        """Add a single inflation rate record."""
        try:
            record = InflationRate(**schema.model_dump())
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Added inflation rate record for year {schema.annee}")
            return record
        except Exception as e:
            logger.error(f"Error adding single record: {e}")
            self.db.rollback()
            return None

    def update(self, record_id: int, data: dict) -> Optional[InflationRate]:
        """Update an inflation rate record."""
        record = self.db.query(InflationRate).filter(InflationRate.id == record_id).first()
        if record:
            for key, value in data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Updated inflation rate record {record_id}")
        return record

    def delete(self, record_id: int) -> bool:
        """Delete an inflation rate record by ID."""
        record = self.db.query(InflationRate).filter(InflationRate.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted inflation rate record {record_id}")
            return True
        logger.warning(f"Inflation rate record {record_id} not found")
        return False

    def delete_by_year(self, annee: int) -> bool:
        """Delete inflation rate record for a specific year."""
        record = self.db.query(InflationRate).filter(InflationRate.annee == annee).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted inflation rate record for year {annee}")
            return True
        logger.warning(f"Inflation rate record for year {annee} not found")
        return False

    def count_records(self) -> int:
        """Get total number of inflation rate records."""
        return self.db.query(InflationRate).count()

    def get_statistics(self) -> dict:
        """Get statistics about inflation rate data."""
        total = self.count_records()
        
        min_year_query = self.db.query(InflationRate.annee).order_by(InflationRate.annee).first()
        max_year_query = self.db.query(InflationRate.annee).order_by(InflationRate.annee.desc()).first()
        
        avg_rate = self.db.query(
            func.avg(InflationRate.taux_inflation).label("avg_taux")
        ).first()
        
        max_rate = self.db.query(
            func.max(InflationRate.taux_inflation).label("max_taux")
        ).first()
        
        min_rate = self.db.query(
            func.min(InflationRate.taux_inflation).label("min_taux")
        ).first()
        
        return {
            "total_records": total,
            "min_year": min_year_query[0] if min_year_query else None,
            "max_year": max_year_query[0] if max_year_query else None,
            "average_rate": round(float(avg_rate.avg_taux), 4) if avg_rate and avg_rate.avg_taux else None,
            "max_rate": round(float(max_rate.max_taux), 4) if max_rate and max_rate.max_taux else None,
            "min_rate": round(float(min_rate.min_taux), 4) if min_rate and min_rate.min_taux else None
        }
