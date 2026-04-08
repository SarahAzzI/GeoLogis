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
        """
        Retrieve all real estate market records from the database.

        This method queries the RealEstateMkt table without any filters and returns
        every record available.

        Returns:
            List of all RealEstateMkt records in the database.
        """
        return self.db.query(RealEstateMkt).all()

    def get_by_id(self, record_id: int) -> Optional[RealEstateMkt]:
        """
        Retrieve a single real estate record by its primary key.

        This method filters the RealEstateMkt table by the given ID and returns
        the first matching record, or None if no match is found.

        Args:
            record_id: The integer primary key of the record to retrieve.
        Returns:
            The matching RealEstateMkt record, or None if not found.
        """
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.id == record_id
        ).first()

    def get_by_commune(self, code_commune: int) -> List[RealEstateMkt]:
        """
        Retrieve all real estate records for a specific commune.

        This method filters the RealEstateMkt table by the given commune code and
        returns all matching records across all available years.

        Args:
            code_commune: The integer commune code to filter records by.
        Returns:
            List of RealEstateMkt records for the specified commune.
        """
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.code_commune == code_commune
        ).all()

    def get_by_year(self, annee: int) -> List[RealEstateMkt]:
        """
        Retrieve all real estate records for a specific year.

        This method filters the RealEstateMkt table by the given year and returns
        all matching records regardless of commune.

        Args:
            annee: The integer year to filter records by.
        Returns:
            List of RealEstateMkt records for the specified year.
        """
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.annee == annee
        ).all()

    def get_by_commune_and_year(
        self, code_commune: int, annee: int
    ) -> Optional[RealEstateMkt]:
        """
        Retrieve a single real estate record matching both a commune code and a year.

        This method applies a compound filter on commune code and year, returning
        the first matching record or None if no match is found.

        Args:
            code_commune: The integer commune code to match against.
            annee: The integer year to match against.
        Returns:
            The matching RealEstateMkt record, or None if not found.
        """
        return self.db.query(RealEstateMkt).filter(
            (RealEstateMkt.code_commune == code_commune) &
            (RealEstateMkt.annee == annee)
        ).first()

    def get_trend_by_commune(self, code_commune: int) -> List[RealEstateMkt]:
        """
        Retrieve the price trend for a specific commune ordered by year ascending.

        This method filters the RealEstateMkt table by commune code and returns
        all matching records sorted chronologically, suitable for time-series analysis.

        Args:
            code_commune: The integer commune code to retrieve the price trend for.
        Returns:
            List of RealEstateMkt records for the commune ordered by year ascending.
        """
        return self.db.query(RealEstateMkt).filter(
            RealEstateMkt.code_commune == code_commune
        ).order_by(RealEstateMkt.annee).all()

    def get_average_price_by_year(self, annee: int) -> dict:
        """
        Compute average price per m² and average number of sales for all communes in a given year.

        This method issues aggregate AVG queries on prix_m2 and nb_ventes scoped to
        the given year. Results are rounded to two decimal places before being returned.
        If no records are found, None is returned for both averages.

        Args:
            annee: The integer year to compute averages for.
        Returns:
            A dict containing annee, avg_prix_m2, and avg_ventes, with None for
            any metric where no data is available.
        """
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
        """
        Bulk insert multiple real estate records from a list of schemas.

        This method iterates over the provided schemas to construct RealEstateMkt
        ORM objects, casting fields to their expected types and defaulting optional
        fields to None where absent. All records are added to the session in a
        single batch and committed together.
        If any error occurs during the process, the transaction is rolled back,
        an error is logged, and 0 is returned.

        Args:
            schemas: List of RealEstateMktCreateSchema instances representing the records to insert.
        Returns:
            The number of successfully inserted records, or 0 if the operation failed.
        """
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
            logger.info(f"Bulk inserted {len(records)} real estate records")
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0

    def add_single(self, schema: RealEstateMktCreateSchema) -> Optional[RealEstateMkt]:
        """
        Add a single real estate record to the database.

        This method constructs a RealEstateMkt ORM object from the provided schema,
        adds it to the session, and commits the transaction. The record is then
        refreshed to reflect any database-generated values.
        If any error occurs, the transaction is rolled back, an error is logged,
        and None is returned.

        Args:
            schema: A RealEstateMktCreateSchema instance containing the data for the new record.
        Returns:
            The newly created and refreshed RealEstateMkt record, or None if the operation failed.
        """
        try:
            record = RealEstateMkt(**schema.model_dump())
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Added real estate record for commune {schema.code_commune}, year {schema.annee}")
            return record
        except Exception as e:
            logger.error(f"Error adding single record: {e}")
            self.db.rollback()
            return None

    def update(self, record_id: int, data: dict) -> Optional[RealEstateMkt]:
        """
        Update an existing real estate record with new field values.

        This method retrieves the record by ID, then iterates over the provided
        data dictionary to set each valid attribute on the ORM object. The session
        is committed and the record refreshed after the update.
        If the record is not found, no changes are made and None is returned.

        Args:
            record_id: The integer primary key of the record to update.
            data: A dictionary mapping field names to their new values.
        Returns:
            The updated and refreshed RealEstateMkt record, or None if the record was not found.
        """
        record = self.db.query(RealEstateMkt).filter(RealEstateMkt.id == record_id).first()
        if record:
            for key, value in data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Updated real estate record {record_id}")
        return record

    def delete(self, record_id: int) -> bool:
        """
        Delete a single real estate record by its primary key.

        This method retrieves the record by ID and, if found, deletes it and
        commits the transaction. If the record does not exist, a warning is
        logged and False is returned.

        Args:
            record_id: The integer primary key of the record to delete.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        record = self.db.query(RealEstateMkt).filter(RealEstateMkt.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted real estate record {record_id}")
            return True
        logger.warning(f"Real estate record {record_id} not found")
        return False

    def delete_by_commune_year(self, code_commune: int, annee: int) -> int:
        """
        Delete all real estate records for a specific commune and year combination.

        This method issues a bulk delete query with a compound filter on commune code
        and year, then commits the transaction and logs the number of deleted records.

        Args:
            code_commune: The integer commune code to filter records by.
            annee: The integer year to filter records by.
        Returns:
            The number of deleted records.
        """
        count = self.db.query(RealEstateMkt).filter(
            (RealEstateMkt.code_commune == code_commune) &
            (RealEstateMkt.annee == annee)
        ).delete()
        self.db.commit()
        logger.info(f"Deleted {count} real estate records for commune {code_commune}, year {annee}")
        return count

    def count_records(self) -> int:
        """
        Count the total number of real estate records in the database.

        This method issues a COUNT query against the entire RealEstateMkt table
        without any filtering.

        Returns:
            The total number of RealEstateMkt records as an integer.
        """
        return self.db.query(RealEstateMkt).count()

    def count_by_year(self, annee: int) -> int:
        """
        Count the number of real estate records for a specific year.

        This method issues a COUNT query filtered by the given year.

        Args:
            annee: The integer year to count records for.
        Returns:
            The number of RealEstateMkt records for the specified year.
        """
        return self.db.query(RealEstateMkt).filter(RealEstateMkt.annee == annee).count()

    def get_statistics(self) -> dict:
        """
        Compute global statistics about the real estate market dataset.

        This method aggregates several metrics across the entire RealEstateMkt table,
        including total record count, the earliest and latest years present, and the
        number of distinct communes and years represented.

        Returns:
            A dict containing total_records, min_year, max_year, unique_communes,
            and unique_years, with None for any metric where no data is available.
        """
        total = self.count_records()

        min_year_query = self.db.query(RealEstateMkt.annee).order_by(RealEstateMkt.annee).first()
        max_year_query = self.db.query(RealEstateMkt.annee).order_by(RealEstateMkt.annee.desc()).first()

        return {
            "total_records": total,
            "min_year": min_year_query[0] if min_year_query else None,
            "max_year": max_year_query[0] if max_year_query else None,
            "unique_communes": self.db.query(RealEstateMkt.code_commune).distinct().count(),
            "unique_years": self.db.query(RealEstateMkt.annee).distinct().count()
        }