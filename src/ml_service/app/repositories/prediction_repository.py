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
        """
        Retrieve all prediction records from the database.

        This method queries the Prediction table without any filters and returns
        every prediction record available.

        Returns:
            List of all Prediction records in the database.
        """
        return self.db.query(Prediction).all()

    def get_by_id(self, record_id: int) -> Optional[Prediction]:
        """
        Retrieve a single prediction record by its primary key.

        This method filters the Prediction table by the given ID and returns
        the first matching record, or None if no match is found.

        Args:
            record_id: The integer primary key of the prediction record to retrieve.
        Returns:
            The matching Prediction record, or None if not found.
        """
        return self.db.query(Prediction).filter(Prediction.id == record_id).first()

    def get_by_commune(self, code_commune: int) -> List[Prediction]:
        """
        Retrieve all prediction records for a specific commune.

        This method filters the Prediction table by the given commune code and
        returns all matching records regardless of model or creation date.

        Args:
            code_commune: The integer commune code to filter predictions by.
        Returns:
            List of Prediction records for the specified commune.
        """
        return self.db.query(Prediction).filter(Prediction.code_commune == code_commune).all()

    def get_recent_predictions(self, limit: int = 10) -> List[Prediction]:
        """
        Retrieve the most recently created prediction records.

        This method orders the Prediction table by creation date descending and
        returns up to the specified number of records.

        Args:
            limit: The maximum number of records to return (default is 10).
        Returns:
            List of the most recent Prediction records, up to the specified limit.
        """
        return self.db.query(Prediction).order_by(desc(Prediction.created_at)).limit(limit).all()

    def get_by_model_id(self, model_id: str) -> List[Prediction]:
        """
        Retrieve all prediction records produced by a specific model.

        This method filters the Prediction table by the given model ID and
        returns all matching records regardless of commune or creation date.

        Args:
            model_id: The string identifier of the model to filter predictions by.
        Returns:
            List of Prediction records associated with the specified model.
        """
        return self.db.query(Prediction).filter(Prediction.model_id == model_id).all()

    def add_prediction(self, data: PredictionCreateSchema) -> Prediction:
        """
        Add a single prediction record to the database.

        This method constructs a Prediction ORM object from the provided schema,
        adds it to the session, and commits the transaction. The record is then
        refreshed to reflect any database-generated values.

        Args:
            data: A PredictionCreateSchema instance containing the data for the new record.
        Returns:
            The newly created and refreshed Prediction record.
        """
        new_prediction = Prediction(**data.model_dump())
        self.db.add(new_prediction)
        self.db.commit()
        self.db.refresh(new_prediction)
        logger.info(f"Added prediction for commune {data.code_commune} with model {data.model_id}")
        return new_prediction

    def add_batch_predictions(self, records: List[PredictionCreateSchema]) -> int:
        """
        Bulk insert multiple prediction records from a list of schemas.

        This method constructs Prediction ORM objects from all provided schemas,
        adds them to the session in a single batch, and commits the transaction.
        If any error occurs during the process, the transaction is rolled back,
        an error is logged, and the exception is re-raised.

        Args:
            records: List of PredictionCreateSchema instances representing the records to insert.
        Returns:
            The number of successfully inserted records.
        Raises:
            Exception: If the batch insert fails, the original exception is re-raised
                       after rollback.
        """
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
        """
        Update an existing prediction record with new field values.

        This method retrieves the record by ID, then iterates over the provided
        data dictionary to set each valid attribute on the ORM object. The session
        is committed and the record refreshed after the update.
        If the record is not found, no changes are made and None is returned.

        Args:
            record_id: The integer primary key of the prediction record to update.
            data: A dictionary mapping field names to their new values.
        Returns:
            The updated and refreshed Prediction record, or None if the record was not found.
        """
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
        """
        Delete a single prediction record by its primary key.

        This method retrieves the record by ID and, if found, deletes it and
        commits the transaction. If the record does not exist, a warning is
        logged and False is returned.

        Args:
            record_id: The integer primary key of the prediction record to delete.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        prediction = self.db.query(Prediction).filter(Prediction.id == record_id).first()
        if prediction:
            self.db.delete(prediction)
            self.db.commit()
            logger.info(f"Deleted prediction {record_id}")
            return True
        logger.warning(f"Prediction {record_id} not found")
        return False

    def clear_all(self) -> int:
        """
        Delete all prediction records from the database.

        This method issues a bulk delete query against the entire Prediction table
        without any filtering, then commits the transaction and logs a warning
        with the number of deleted records.

        Returns:
            The total number of deleted records.
        """
        count = self.db.query(Prediction).delete()
        self.db.commit()
        logger.warning(f"Cleared {count} predictions")
        return count

    def clear_by_model(self, model_id: str) -> int:
        """
        Delete all prediction records associated with a specific model.

        This method issues a bulk delete query filtered by the given model ID,
        then commits the transaction and logs the number of deleted records.

        Args:
            model_id: The string identifier of the model whose predictions should be deleted.
        Returns:
            The number of deleted records.
        """
        count = self.db.query(Prediction).filter(Prediction.model_id == model_id).delete()
        self.db.commit()
        logger.info(f"Deleted {count} predictions for model {model_id}")
        return count

    def count_records(self) -> int:
        """
        Count the total number of prediction records in the database.

        This method issues a COUNT query against the entire Prediction table
        without any filtering.

        Returns:
            The total number of Prediction records as an integer.
        """
        return self.db.query(Prediction).count()

    def count_by_model(self, model_id: str) -> int:
        """
        Count the number of prediction records for a specific model.

        This method issues a COUNT query filtered by the given model ID.

        Args:
            model_id: The string identifier of the model to count predictions for.
        Returns:
            The number of Prediction records associated with the specified model.
        """
        return self.db.query(Prediction).filter(Prediction.model_id == model_id).count()

    def get_statistics(self) -> dict:
        """
        Compute global statistics about the prediction dataset.

        This method aggregates several metrics across the entire Prediction table,
        including total record count and the number of distinct communes and models
        represented.

        Returns:
            A dict containing total_predictions, unique_communes, and unique_models.
        """
        total = self.count_records()

        return {
            "total_predictions": total,
            "unique_communes": self.db.query(Prediction.code_commune).distinct().count(),
            "unique_models": self.db.query(Prediction.model_id).distinct().count()
        }