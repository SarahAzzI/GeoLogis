from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from ..model.database import get_db
from ..model.training import Training
from ..schemas.training_schema import TrainingCreateSchema
import logging

logger = logging.getLogger(__name__)


class TrainingRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_training_data(self):
        """Get all training records."""
        return self.db.query(Training).all()
    
    def get_by_id(self, record_id: int):
        """Get a specific training record by ID."""
        return self.db.query(Training).filter(Training.id == record_id).first()
    
    def get_by_commune(self, code_commune: int) -> List[Training]:
        """Get all training records for a specific commune."""
        return self.db.query(Training).filter(Training.code_commune == code_commune).all()
    
    def get_by_year(self, annee: int) -> List[Training]:
        """Get all training records for a specific year."""
        return self.db.query(Training).filter(Training.annee == annee).all()
    
    def get_by_year_range(self, min_year: int, max_year: int) -> List[Training]:
        """Get training records within a year range."""
        return self.db.query(Training).filter(
            (Training.annee >= min_year) & (Training.annee <= max_year)
        ).all()
    
    def feed_data(self, data: TrainingCreateSchema):
        """Add a single training record."""
        new_training_data = Training(**data.model_dump())
        self.db.add(new_training_data)
        self.db.commit()
        self.db.refresh(new_training_data)
        logger.info(f"Added training record for commune {data.code_commune}, year {data.annee}")
        return new_training_data
    
    def feed_batch(self, records: List[TrainingCreateSchema]) -> int:
        """Add multiple training records in batch."""
        try:
            training_records = [Training(**record.model_dump()) for record in records]
            self.db.add_all(training_records)
            self.db.commit()
            logger.info(f"Batch inserted {len(training_records)} training records")
            return len(training_records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error inserting batch: {e}")
            raise
    
    def delete(self, record_id: int) -> bool:
        """Delete a training record by ID."""
        record = self.db.query(Training).filter(Training.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted training record {record_id}")
            return True
        logger.warning(f"Training record {record_id} not found")
        return False
    
    def clear_all(self) -> int:
        """Clear all training records."""
        count = self.db.query(Training).delete()
        self.db.commit()
        logger.warning(f"Cleared {count} training records")
        return count
    
    def clear_by_year(self, annee: int) -> int:
        """Delete all training records for a specific year."""
        count = self.db.query(Training).filter(Training.annee == annee).delete()
        self.db.commit()
        logger.info(f"Deleted {count} training records for year {annee}")
        return count
    
    def count_records(self) -> int:
        """Get total number of training records."""
        return self.db.query(Training).count()
    
    def count_by_year(self, annee: int) -> int:
        """Get count of training records for a specific year."""
        return self.db.query(Training).filter(Training.annee == annee).count()
    
    def get_statistics(self) -> dict:
        """Get statistics about training data."""
        total = self.count_records()
        
        # Get year range
        min_year_query = self.db.query(Training.annee).order_by(Training.annee).first()
        max_year_query = self.db.query(Training.annee).order_by(Training.annee.desc()).first()
        
        return {
            "total_records": total,
            "min_year": min_year_query[0] if min_year_query else None,
            "max_year": max_year_query[0] if max_year_query else None,
            "unique_communes": self.db.query(Training.code_commune).distinct().count(),
            "unique_years": self.db.query(Training.annee).distinct().count()
        }