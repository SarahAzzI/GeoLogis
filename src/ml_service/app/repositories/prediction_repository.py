from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..model.database import get_db
from ..model.prediction import Prediction
from ..schemas.prediction_schema import PredictionReadSchema, PredictionCreateSchema
import logging

logger = logging.getLogger(__name__)


class PredictionRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_predictions(self) -> List[Prediction]:
        """Get all predictions."""
        return self.db.query(Prediction).all()
    
    def get_by_id(self, record_id: int) -> Optional[Prediction]:
        """Get a specific prediction by ID."""
        return self.db.query(Prediction).filter(Prediction.id == record_id).first()
    
    def get_by_commune(self, code_commune: int) -> List[Prediction]:
        """Get all predictions for a specific commune."""
        return self.db.query(Prediction).filter(Prediction.code_commune == code_commune).all()
    
    def get_recent_predictions(self, limit: int = 10) -> List[Prediction]:
        """Get the most recent predictions."""
        return self.db.query(Prediction).order_by(desc(Prediction.created_at)).limit(limit).all()
    
    def get_by_model_id(self, model_id: str) -> List[Prediction]:
        """Get all predictions made by a specific model."""
        return self.db.query(Prediction).filter(Prediction.model_id == model_id).all()
    
    def add_prediction(self, data: PredictionCreateSchema) -> Prediction:
        """Add a single prediction."""
        new_prediction = Prediction(**data.model_dump())
        self.db.add(new_prediction)
        self.db.commit()
        self.db.refresh(new_prediction)
        logger.info(f"Added prediction for commune {data.code_commune} with model {data.model_id}")
        return new_prediction
    
    def add_batch_predictions(self, records: List[PredictionCreateSchema]) -> int:
        """Add multiple predictions in batch."""
        try:
            predictions = [Prediction(**record.model_dump()) for record in records]
            self.db.add_all(predictions)
            self.db.commit()
            logger.info(f"Batch inserted {len(predictions)} predictions")
            return len(predictions)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error inserting batch predictions: {e}")
            raise
    
    def update_prediction(self, record_id: int, data: dict) -> Optional[Prediction]:
        """Update a prediction record."""
        prediction = self.db.query(Prediction).filter(Prediction.id == record_id).first()
        if prediction:
            for key, value in data.items():
                if hasattr(prediction, key):
                    setattr(prediction, key, value)
            self.db.commit()
            self.db.refresh(prediction)
            logger.info(f"Updated prediction {record_id}")
        return prediction
    
    def delete(self, record_id: int) -> bool:
        """Delete a prediction by ID."""
        prediction = self.db.query(Prediction).filter(Prediction.id == record_id).first()
        if prediction:
            self.db.delete(prediction)
            self.db.commit()
            logger.info(f"Deleted prediction {record_id}")
            return True
        logger.warning(f"Prediction {record_id} not found")
        return False
    
    def clear_all(self) -> int:
        """Clear all predictions."""
        count = self.db.query(Prediction).delete()
        self.db.commit()
        logger.warning(f"Cleared {count} predictions")
        return count
    
    def clear_by_model(self, model_id: str) -> int:
        """Delete all predictions for a specific model."""
        count = self.db.query(Prediction).filter(Prediction.model_id == model_id).delete()
        self.db.commit()
        logger.info(f"Deleted {count} predictions for model {model_id}")
        return count
    
    def count_records(self) -> int:
        """Get total number of predictions."""
        return self.db.query(Prediction).count()
    
    def count_by_model(self, model_id: str) -> int:
        """Get count of predictions for a specific model."""
        return self.db.query(Prediction).filter(Prediction.model_id == model_id).count()
    
    def get_statistics(self) -> dict:
        """Get statistics about predictions."""
        total = self.count_records()
        
        return {
            "total_predictions": total,
            "unique_communes": self.db.query(Prediction.code_commune).distinct().count(),
            "unique_models": self.db.query(Prediction.model_id).distinct().count()
        }
