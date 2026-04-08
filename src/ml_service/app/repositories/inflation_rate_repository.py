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
        """
        Retrieve all inflation rate records ordered by year ascending.

        This method queries the entire InflationRate table without filtering
        and returns results sorted from the earliest to the most recent year.

        Returns:
            List of all InflationRate records ordered by year ascending.
        """
        return self.db.query(InflationRate).order_by(InflationRate.annee).all()

    def get_by_id(self, record_id: int) -> Optional[InflationRate]:
        """
        Retrieve a single inflation rate record by its primary key.

        This method filters the InflationRate table by the given ID and returns
        the first matching record, or None if no match is found.

        Args:
            record_id: The integer primary key of the inflation rate record to retrieve.
        Returns:
            The matching InflationRate record, or None if not found.
        """
        return self.db.query(InflationRate).filter(
            InflationRate.id == record_id
        ).first()

    def get_by_year(self, annee: int) -> Optional[InflationRate]:
        """
        Retrieve the inflation rate record for a specific year.

        This method filters the InflationRate table by the given year and returns
        the first matching record, or None if no record exists for that year.

        Args:
            annee: The integer year to retrieve the inflation rate for.
        Returns:
            The matching InflationRate record, or None if not found.
        """
        return self.db.query(InflationRate).filter(
            InflationRate.annee == annee
        ).first()

    def get_year_range(self, annee_start: int, annee_end: int) -> List[InflationRate]:
        """
        Retrieve all inflation rate records within an inclusive year range.

        This method applies a compound filter to select records whose year falls
        between annee_start and annee_end, and returns them ordered by year ascending.

        Args:
            annee_start: The integer start year of the range (inclusive).
            annee_end: The integer end year of the range (inclusive).
        Returns:
            List of InflationRate records within the specified year range, ordered by year ascending.
        """
        return self.db.query(InflationRate).filter(
            and_(
                InflationRate.annee >= annee_start,
                InflationRate.annee <= annee_end,
            )
        ).order_by(InflationRate.annee).all()

    def get_average_inflation(self, annee_start: int, annee_end: int) -> float:
        """
        Compute the average inflation rate over an inclusive year range.

        This method issues an aggregate AVG query scoped to the given year range.
        The result is rounded to four decimal places before being returned.
        If no records are found for the period, 0.0 is returned.

        Args:
            annee_start: The integer start year of the period (inclusive).
            annee_end: The integer end year of the period (inclusive).
        Returns:
            The average inflation rate as a float rounded to 4 decimal places,
            or 0.0 if no records exist for the period.
        """
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
        """
        Bulk insert multiple inflation rate records from a list of schemas.

        This method iterates over the provided schemas to construct InflationRate
        ORM objects, casting fields to their expected types and defaulting optional
        fields to None where absent. All records are added to the session in a
        single batch and committed together.
        If any error occurs during the process, the transaction is rolled back,
        an error is logged, and 0 is returned.

        Args:
            schemas: List of InflationRateCreateSchema instances representing the records to insert.
        Returns:
            The number of successfully inserted records, or 0 if the operation failed.
        """
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
        """
        Add a single inflation rate record to the database.

        This method constructs an InflationRate ORM object from the provided schema,
        adds it to the session, and commits the transaction. The record is then
        refreshed to reflect any database-generated values.
        If any error occurs, the transaction is rolled back, an error is logged,
        and None is returned.

        Args:
            schema: An InflationRateCreateSchema instance containing the data for the new record.
        Returns:
            The newly created and refreshed InflationRate record, or None if the operation failed.
        """
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
        """
        Update an existing inflation rate record with new field values.

        This method retrieves the record by ID, then iterates over the provided
        data dictionary to set each valid attribute on the ORM object. The session
        is committed and the record refreshed after the update.
        If the record is not found, no changes are made and None is returned.

        Args:
            record_id: The integer primary key of the inflation rate record to update.
            data: A dictionary mapping field names to their new values.
        Returns:
            The updated and refreshed InflationRate record, or None if the record was not found.
        """
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
        """
        Delete a single inflation rate record by its primary key.

        This method retrieves the record by ID and, if found, deletes it and
        commits the transaction. If the record does not exist, a warning is
        logged and False is returned.

        Args:
            record_id: The integer primary key of the inflation rate record to delete.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        record = self.db.query(InflationRate).filter(InflationRate.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted inflation rate record {record_id}")
            return True
        logger.warning(f"Inflation rate record {record_id} not found")
        return False

    def delete_by_year(self, annee: int) -> bool:
        """
        Delete the inflation rate record for a specific year.

        This method retrieves the record matching the given year and, if found,
        deletes it and commits the transaction. If no record exists for that year,
        a warning is logged and False is returned.

        Args:
            annee: The integer year whose inflation rate record should be deleted.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        record = self.db.query(InflationRate).filter(InflationRate.annee == annee).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted inflation rate record for year {annee}")
            return True
        logger.warning(f"Inflation rate record for year {annee} not found")
        return False

    def count_records(self) -> int:
        """
        Count the total number of inflation rate records in the database.

        This method issues a COUNT query against the entire InflationRate table
        without any filtering.

        Returns:
            The total number of InflationRate records as an integer.
        """
        return self.db.query(InflationRate).count()

    def get_statistics(self) -> dict:
        """
        Compute global statistics about the inflation rate dataset.

        This method aggregates several metrics across the entire InflationRate table,
        including total record count, the earliest and latest years present, and the
        average, maximum, and minimum inflation rates. All rate values are rounded
        to four decimal places.

        Returns:
            A dict containing total_records, min_year, max_year, average_rate,
            max_rate, and min_rate, with None for any metric where no data is available.
        """
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