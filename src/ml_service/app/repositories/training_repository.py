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
        """
        Retrieve all training records from the database.

        This method queries the Training table without any filters and returns
        every training record available.

        Returns:
            List of all Training records in the database.
        """
        return self.db.query(Training).all()

    def get_by_id(self, record_id: int):
        """
        Retrieve a single training record by its primary key.

        This method filters the Training table by the given ID and returns
        the first matching record, or None if no match is found.

        Args:
            record_id: The integer primary key of the training record to retrieve.
        Returns:
            The matching Training record, or None if not found.
        """
        return self.db.query(Training).filter(Training.id == record_id).first()

    def get_by_commune(self, code_commune: int) -> List[Training]:
        """
        Retrieve all training records for a specific commune.

        This method filters the Training table by the given commune code and
        returns all matching records across all available years.

        Args:
            code_commune: The integer commune code to filter records by.
        Returns:
            List of Training records for the specified commune.
        """
        return self.db.query(Training).filter(Training.code_commune == code_commune).all()

    def get_by_year(self, annee: int) -> List[Training]:
        """
        Retrieve all training records for a specific year.

        This method filters the Training table by the given year and returns
        all matching records regardless of commune.

        Args:
            annee: The integer year to filter records by.
        Returns:
            List of Training records for the specified year.
        """
        return self.db.query(Training).filter(Training.annee == annee).all()

    def get_by_year_range(self, min_year: int, max_year: int) -> List[Training]:
        """
        Retrieve all training records within an inclusive year range.

        This method applies a compound filter to select records whose year falls
        between min_year and max_year, returning all matches regardless of commune.

        Args:
            min_year: The integer start year of the range (inclusive).
            max_year: The integer end year of the range (inclusive).
        Returns:
            List of Training records within the specified year range.
        """
        return self.db.query(Training).filter(
            (Training.annee >= min_year) & (Training.annee <= max_year)
        ).all()

    def feed_data(self, data: TrainingCreateSchema):
        """
        Add a single training record to the database.

        This method constructs a Training ORM object from the provided schema,
        adds it to the session, and commits the transaction. The record is then
        refreshed to reflect any database-generated values.

        Args:
            data: A TrainingCreateSchema instance containing the data for the new record.
        Returns:
            The newly created and refreshed Training record.
        """
        new_training_data = Training(**data.model_dump())
        self.db.add(new_training_data)
        self.db.commit()
        self.db.refresh(new_training_data)
        logger.info(f"Added training record for commune {data.code_commune}, year {data.annee}")
        return new_training_data

    def feed_batch(self, records: List[TrainingCreateSchema]) -> int:
        """
        Bulk insert multiple training records from a list of schemas.

        This method constructs Training ORM objects from all provided schemas,
        adds them to the session in a single batch, and commits the transaction.
        If any error occurs during the process, the transaction is rolled back,
        an error is logged, and the exception is re-raised.

        Args:
            records: List of TrainingCreateSchema instances representing the records to insert.
        Returns:
            The number of successfully inserted records.
        Raises:
            Exception: If the batch insert fails, the original exception is re-raised
                       after rollback.
        """
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
        """
        Delete a single training record by its primary key.

        This method retrieves the record by ID and, if found, deletes it and
        commits the transaction. If the record does not exist, a warning is
        logged and False is returned.

        Args:
            record_id: The integer primary key of the training record to delete.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        record = self.db.query(Training).filter(Training.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted training record {record_id}")
            return True
        logger.warning(f"Training record {record_id} not found")
        return False

    def clear_all(self) -> int:
        """
        Delete all training records from the database.

        This method issues a bulk delete query against the entire Training table
        without any filtering, then commits the transaction and logs a warning
        with the number of deleted records.

        Returns:
            The total number of deleted records.
        """
        count = self.db.query(Training).delete()
        self.db.commit()
        logger.warning(f"Cleared {count} training records")
        return count

    def clear_by_year(self, annee: int) -> int:
        """
        Delete all training records for a specific year.

        This method issues a bulk delete query filtered by the given year,
        then commits the transaction and logs the number of deleted records.

        Args:
            annee: The integer year whose training records should be deleted.
        Returns:
            The number of deleted records.
        """
        count = self.db.query(Training).filter(Training.annee == annee).delete()
        self.db.commit()
        logger.info(f"Deleted {count} training records for year {annee}")
        return count

    def count_records(self) -> int:
        """
        Count the total number of training records in the database.

        This method issues a COUNT query against the entire Training table
        without any filtering.

        Returns:
            The total number of Training records as an integer.
        """
        return self.db.query(Training).count()

    def count_by_year(self, annee: int) -> int:
        """
        Count the number of training records for a specific year.

        This method issues a COUNT query filtered by the given year.

        Args:
            annee: The integer year to count records for.
        Returns:
            The number of Training records for the specified year.
        """
        return self.db.query(Training).filter(Training.annee == annee).count()

    def get_statistics(self) -> dict:
        """
        Compute global statistics about the training dataset.

        This method aggregates several metrics across the entire Training table,
        including total record count, the earliest and latest years present, and
        the number of distinct communes and years represented.

        Returns:
            A dict containing total_records, min_year, max_year, unique_communes,
            and unique_years, with None for any metric where no data is available.
        """
        total = self.count_records()

        min_year_query = self.db.query(Training.annee).order_by(Training.annee).first()
        max_year_query = self.db.query(Training.annee).order_by(Training.annee.desc()).first()

        return {
            "total_records": total,
            "min_year": min_year_query[0] if min_year_query else None,
            "max_year": max_year_query[0] if max_year_query else None,
            "unique_communes": self.db.query(Training.code_commune).distinct().count(),
            "unique_years": self.db.query(Training.annee).distinct().count()
        }