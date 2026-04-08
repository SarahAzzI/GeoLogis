from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from ..model.database import get_db
from ..model.communes import Commune
from ..schemas.communes_schema import CommuneCreateSchema, CommuneFilterSchema

logger = logging.getLogger(__name__)


class CommuneRepository:
    """Repository for commune geographic and demographic data operations."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_all(self) -> List[Commune]:
        """
        Retrieve all commune records from the database.

        This method queries the database without any filters and returns every
        commune record available.

        Returns:
            List of all Commune records in the database.
        """
        return self.db.query(Commune).all()

    def get_by_id(self, record_id: int) -> Optional[Commune]:
        """
        Retrieve a single commune record by its primary key.

        This method filters the Commune table by the given ID and returns
        the first matching record, or None if no match is found.

        Args:
            record_id: The integer primary key of the commune record to retrieve.
        Returns:
            The matching Commune record, or None if not found.
        """
        return self.db.query(Commune).filter(Commune.id == record_id).first()

    def get_by_insee(self, code_insee: str) -> List[Commune]:
        """
        Retrieve all records for a specific INSEE code, ordered by year descending.

        This method filters the Commune table by the given INSEE code and returns
        all matching records sorted from the most recent year to the oldest.

        Args:
            code_insee: The INSEE code string identifying the commune.
        Returns:
            List of Commune records matching the INSEE code, ordered by year descending.
        """
        return self.db.query(Commune).filter(
            Commune.code_insee == code_insee
        ).order_by(Commune.annee.desc()).all()

    def get_by_postal_code(self, code_postal: str) -> List[Commune]:
        """
        Retrieve all communes matching a specific postal code.

        This method filters the Commune table by the given postal code and returns
        all matching records regardless of year.

        Args:
            code_postal: The postal code string to filter communes by.
        Returns:
            List of Commune records matching the postal code.
        """
        return self.db.query(Commune).filter(
            Commune.code_postal == code_postal
        ).all()

    def get_by_department(self, dep_code: str) -> List[Commune]:
        """
        Retrieve all commune records belonging to a specific department.

        This method filters the Commune table by the given department code and
        returns all matching records across all available years.

        Args:
            dep_code: The department code string to filter communes by.
        Returns:
            List of Commune records belonging to the specified department.
        """
        return self.db.query(Commune).filter(
            Commune.dep_code == dep_code
        ).all()

    def get_by_region(self, reg_code: str) -> List[Commune]:
        """
        Retrieve all commune records belonging to a specific region.

        This method filters the Commune table by the given region code and
        returns all matching records across all available years.

        Args:
            reg_code: The region code string to filter communes by.
        Returns:
            List of Commune records belonging to the specified region.
        """
        return self.db.query(Commune).filter(
            Commune.reg_code == reg_code
        ).all()

    def get_by_year(self, annee: int) -> List[Commune]:
        """
        Retrieve all commune records for a specific year.

        This method filters the Commune table by the given year and returns
        all matching records regardless of geographic criteria.

        Args:
            annee: The integer year to filter commune records by.
        Returns:
            List of Commune records for the specified year.
        """
        return self.db.query(Commune).filter(Commune.annee == annee).all()

    def get_by_insee_and_year(self, code_insee: str, annee: int) -> Optional[Commune]:
        """
        Retrieve a single commune record matching both an INSEE code and a year.

        This method applies a compound filter on INSEE code and year, returning
        the first matching record or None if no match is found.

        Args:
            code_insee: The INSEE code string identifying the commune.
            annee: The integer year to match against.
        Returns:
            The matching Commune record, or None if not found.
        """
        return self.db.query(Commune).filter(
            and_(
                Commune.code_insee == code_insee,
                Commune.annee == annee,
            )
        ).first()

    def filter_records(self, filters: CommuneFilterSchema) -> List[Commune]:
        """
        Filter commune records based on multiple optional criteria.

        This method dynamically builds a query by applying only the filters
        that are present in the provided schema. Each non-null field in the
        schema is added as an additional WHERE clause on the query.

        Args:
            filters: A CommuneFilterSchema instance containing the optional filter fields
                     (code_insee, code_postal, annee, dep_code, reg_code).
        Returns:
            List of Commune records matching all provided filter criteria.
        """
        query = self.db.query(Commune)

        if filters.code_insee:
            query = query.filter(Commune.code_insee == filters.code_insee)
        if filters.code_postal:
            query = query.filter(Commune.code_postal == filters.code_postal)
        if filters.annee:
            query = query.filter(Commune.annee == filters.annee)
        if filters.dep_code:
            query = query.filter(Commune.dep_code == filters.dep_code)
        if filters.reg_code:
            query = query.filter(Commune.reg_code == filters.reg_code)

        return query.all()

    def get_department_stats(self, dep_code: str, annee: int) -> dict:
        """
        Compute aggregate statistics for a department in a given year.

        This method retrieves all commune records for the specified department
        and year, then calculates summary metrics including record count and
        average population. If no records are found, an error dict is returned.

        Args:
            dep_code: The department code string to compute statistics for.
            annee: The integer year to scope the statistics to.
        Returns:
            A dict containing dep_code, annee, count, and avg_population,
            or a dict with an "error" key if no records are found.
        """
        records = self.db.query(Commune).filter(
            and_(Commune.dep_code == dep_code, Commune.annee == annee)
        ).all()
        
        if not records:
            return {"error": "No records found"}
        
        return {
            "dep_code": dep_code,
            "annee": annee,
            "count": len(records),
            "avg_population": sum(r.population for r in records if r.population) / len([r for r in records if r.population]) if any(r.population for r in records) else None,
        }

    def create_bulk(self, schemas: List[CommuneCreateSchema]) -> int:
        """
        Bulk insert multiple commune records from a list of schemas.

        This method iterates over the provided schemas to construct Commune ORM
        objects, safely casting optional fields where present. All records are
        added to the session in a single batch and committed together.
        If any error occurs during the process, the transaction is rolled back,
        an error is logged, and 0 is returned.

        Args:
            schemas: List of CommuneCreateSchema instances representing the records to insert.
        Returns:
            The number of successfully inserted records, or 0 if the operation failed.
        """
        try:
            records = [
                Commune(
                    code_insee=schema.code_insee,
                    nom_standard=schema.nom_standard,
                    code_postal=schema.code_postal if hasattr(schema, 'code_postal') and schema.code_postal else None,
                    annee=int(schema.annee),
                    dep_code=schema.dep_code if hasattr(schema, 'dep_code') and schema.dep_code else None,
                    dep_nom=schema.dep_nom if hasattr(schema, 'dep_nom') and schema.dep_nom else None,
                    reg_code=schema.reg_code if hasattr(schema, 'reg_code') and schema.reg_code else None,
                    reg_nom=schema.reg_nom if hasattr(schema, 'reg_nom') and schema.reg_nom else None,
                    population=int(schema.population) if hasattr(schema, 'population') and schema.population else None,
                    densite=float(schema.densite) if hasattr(schema, 'densite') and schema.densite else None,
                    superficie_km2=float(schema.superficie_km2) if hasattr(schema, 'superficie_km2') and schema.superficie_km2 else None,
                    latitude_centre=float(schema.latitude_centre) if hasattr(schema, 'latitude_centre') and schema.latitude_centre else None,
                    longitude_centre=float(schema.longitude_centre) if hasattr(schema, 'longitude_centre') and schema.longitude_centre else None,
                    zone_emploi=schema.zone_emploi if hasattr(schema, 'zone_emploi') and schema.zone_emploi else None,
                )
                for schema in schemas
            ]
            self.db.add_all(records)
            self.db.commit()
            logger.info(f"Bulk inserted {len(records)} commune records")
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0

    def add_single(self, schema: CommuneCreateSchema) -> Optional[Commune]:
        """
        Add a single commune record to the database.

        This method constructs a Commune ORM object from the provided schema,
        adds it to the session, and commits the transaction. The record is then
        refreshed to reflect any database-generated values.
        If any error occurs, the transaction is rolled back, an error is logged,
        and None is returned.

        Args:
            schema: A CommuneCreateSchema instance containing the data for the new record.
        Returns:
            The newly created and refreshed Commune record, or None if the operation failed.
        """
        try:
            record = Commune(**schema.model_dump())
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Added commune record {schema.code_insee}, year {schema.annee}")
            return record
        except Exception as e:
            logger.error(f"Error adding single record: {e}")
            self.db.rollback()
            return None

    def update(self, record_id: int, data: dict) -> Optional[Commune]:
        """
        Update an existing commune record with new field values.

        This method retrieves the record by ID, then iterates over the provided
        data dictionary to set each valid attribute on the ORM object. The session
        is committed and the record refreshed after the update.
        If the record is not found, no changes are made and None is returned.

        Args:
            record_id: The integer primary key of the commune record to update.
            data: A dictionary mapping field names to their new values.
        Returns:
            The updated and refreshed Commune record, or None if the record was not found.
        """
        record = self.db.query(Commune).filter(Commune.id == record_id).first()
        if record:
            for key, value in data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Updated commune record {record_id}")
        return record

    def delete(self, record_id: int) -> bool:
        """
        Delete a single commune record by its primary key.

        This method retrieves the record by ID and, if found, deletes it and
        commits the transaction. If the record does not exist, a warning is
        logged and False is returned.

        Args:
            record_id: The integer primary key of the commune record to delete.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        record = self.db.query(Commune).filter(Commune.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted commune record {record_id}")
            return True
        logger.warning(f"Commune record {record_id} not found")
        return False

    def delete_by_year(self, annee: int) -> int:
        """
        Delete all commune records for a specific year.

        This method issues a bulk delete query filtering by the given year,
        then commits the transaction and logs the number of deleted records.

        Args:
            annee: The integer year whose commune records should be deleted.
        Returns:
            The number of records deleted.
        """
        count = self.db.query(Commune).filter(Commune.annee == annee).delete()
        self.db.commit()
        logger.info(f"Deleted {count} commune records for year {annee}")
        return count

    def count_records(self) -> int:
        """
        Count the total number of commune records in the database.

        This method issues a COUNT query against the entire Commune table
        without any filtering.

        Returns:
            The total number of Commune records as an integer.
        """
        return self.db.query(Commune).count()

    def count_by_year(self, annee: int) -> int:
        """
        Count the number of commune records for a specific year.

        This method issues a COUNT query filtered by the given year.

        Args:
            annee: The integer year to count records for.
        Returns:
            The number of Commune records for the specified year.
        """
        return self.db.query(Commune).filter(Commune.annee == annee).count()

    def get_statistics(self) -> dict:
        """
        Compute global statistics about the commune dataset.

        This method aggregates several metrics across the entire Commune table,
        including total record count, the earliest and latest years present,
        and the number of distinct communes, departments, regions, and years.

        Returns:
            A dict containing total_records, min_year, max_year, unique_communes,
            unique_departments, unique_regions, and unique_years.
        """
        total = self.count_records()
        
        min_year_query = self.db.query(Commune.annee).order_by(Commune.annee).first()
        max_year_query = self.db.query(Commune.annee).order_by(Commune.annee.desc()).first()
        
        return {
            "total_records": total,
            "min_year": min_year_query[0] if min_year_query else None,
            "max_year": max_year_query[0] if max_year_query else None,
            "unique_communes": self.db.query(Commune.code_insee).distinct().count(),
            "unique_departments": self.db.query(Commune.dep_code).distinct().count(),
            "unique_regions": self.db.query(Commune.reg_code).distinct().count(),
            "unique_years": self.db.query(Commune.annee).distinct().count()
        }