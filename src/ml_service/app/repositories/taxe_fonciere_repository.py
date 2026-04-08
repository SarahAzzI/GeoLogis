from typing import List, Optional
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from ..model.database import get_db
from ..model.taxe_fonciere import TaxeFonciere
from ..schemas.taxe_fonciere_schema import (
    TaxeFonciereCreateSchema,
    TaxeFonciereReadSchema,
    TaxeFonciereFilterSchema,
)

logger = logging.getLogger(__name__)


class TaxeFonciereRepository:
    """Repository for taxe foncière database operations."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_all(self) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records from the database.

        This method queries the TaxeFonciere table without any filters and returns
        every record available.

        Returns:
            List of all TaxeFonciere records in the database.
        """
        return self.db.query(TaxeFonciere).all()

    def get_by_id(self, record_id: int) -> Optional[TaxeFonciere]:
        """
        Retrieve a single taxe foncière record by its primary key.

        This method filters the TaxeFonciere table by the given ID and returns
        the first matching record, or None if no match is found.

        Args:
            record_id: The integer primary key of the record to retrieve.
        Returns:
            The matching TaxeFonciere record, or None if not found.
        """
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.id == record_id).first()

    def get_by_dept(self, dept: str) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records for a specific department.

        This method filters the TaxeFonciere table by the given department code and
        returns all matching records across all available years.

        Args:
            dept: The department code string to filter records by.
        Returns:
            List of TaxeFonciere records for the specified department.
        """
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.dept == dept).all()

    def get_by_postal_code(self, postal_code: str) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records for a specific postal code.

        This method filters the TaxeFonciere table by the given postal code and
        returns all matching records across all available years.

        Args:
            postal_code: The postal code string to filter records by.
        Returns:
            List of TaxeFonciere records for the specified postal code.
        """
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.code_postal == postal_code).all()

    def get_by_postal_code_and_year(self, postal_code: str, annee_cible: int) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records matching a postal code and a target year.

        This method applies a compound filter on postal code and year, returning
        all matching records for that combination.

        Args:
            postal_code: The postal code string to filter records by.
            annee_cible: The integer target year to filter records by.
        Returns:
            List of TaxeFonciere records matching the postal code and year.
        """
        return self.db.query(TaxeFonciere).filter(
            and_(
                TaxeFonciere.code_postal == postal_code,
                TaxeFonciere.annee_cible == annee_cible,
            )
        ).all()

    def get_by_postal_code_and_dept(self, postal_code: str, dept: str) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records matching a postal code and a department.

        This method applies a compound filter on postal code and department code,
        returning all records that satisfy both conditions.

        Args:
            postal_code: The postal code string to filter records by.
            dept: The department code string to filter records by.
        Returns:
            List of TaxeFonciere records matching the postal code and department.
        """
        return self.db.query(TaxeFonciere).filter(
            and_(
                TaxeFonciere.code_postal == postal_code,
                TaxeFonciere.dept == dept,
            )
        ).all()

    def get_by_insee(self, insee_com: str) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records for a specific INSEE commune code.

        This method filters the TaxeFonciere table by the given INSEE code and
        returns all matching records across all available years.

        Args:
            insee_com: The INSEE commune code string to filter records by.
        Returns:
            List of TaxeFonciere records for the specified INSEE commune code.
        """
        return self.db.query(TaxeFonciere).filter(
            TaxeFonciere.insee_com == insee_com
        ).all()

    def get_by_year(self, annee_cible: int) -> List[TaxeFonciere]:
        """
        Retrieve all taxe foncière records for a specific target year.

        This method filters the TaxeFonciere table by the given year and returns
        all matching records regardless of geographic criteria.

        Args:
            annee_cible: The integer target year to filter records by.
        Returns:
            List of TaxeFonciere records for the specified year.
        """
        return self.db.query(TaxeFonciere).filter(
            TaxeFonciere.annee_cible == annee_cible
        ).all()

    def get_by_dept_and_year(
        self, dept: str, annee_cible: int
    ) -> Optional[TaxeFonciere]:
        """
        Retrieve a single taxe foncière record matching both a department and a target year.

        This method applies a compound filter on department code and year, returning
        the first matching record or None if no match is found.

        Args:
            dept: The department code string to match against.
            annee_cible: The integer target year to match against.
        Returns:
            The matching TaxeFonciere record, or None if not found.
        """
        return self.db.query(TaxeFonciere).filter(
            and_(
                TaxeFonciere.dept == dept,
                TaxeFonciere.annee_cible == annee_cible,
            )
        ).first()

    def count_fallback(self, postal_code: Optional[str] = None) -> int:
        """
        Count the number of records that used a fallback year, optionally scoped to a postal code.

        This method filters the TaxeFonciere table to records where est_fallback is True.
        If a postal code is provided, an additional filter is applied to restrict the
        count to that postal code only.

        Args:
            postal_code: An optional postal code string to restrict the count to. If None,
                         all fallback records are counted regardless of location.
        Returns:
            The number of fallback records matching the criteria.
        """
        query = self.db.query(TaxeFonciere).filter(TaxeFonciere.est_fallback == True)
        if postal_code:
            query = query.filter(TaxeFonciere.code_postal == postal_code)
        return query.count()

    def get_average_rates_by_year(self, annee_cible: int, postal_code: Optional[str] = None) -> dict:
        """
        Compute average tax rates for a specific year, optionally scoped to a postal code.

        This method issues aggregate AVG queries on taux_global_tfb, taux_global_tfnb,
        taux_plein_teom, and taux_global_th, filtered by the given year. If a postal
        code is provided, an additional filter is applied to restrict results to that
        area. If no records match, an empty dict is returned.

        Args:
            annee_cible: The integer target year to compute averages for.
            postal_code: An optional postal code string to restrict the averages to.
                         If None, averages are computed across all communes for that year.
        Returns:
            A dict containing annee_cible, postal_code, and the four average rate fields,
            or an empty dict if no matching records are found.
        """
        from sqlalchemy import func

        query = self.db.query(
            func.avg(TaxeFonciere.taux_global_tfb).label("avg_taux_global_tfb"),
            func.avg(TaxeFonciere.taux_global_tfnb).label("avg_taux_global_tfnb"),
            func.avg(TaxeFonciere.taux_plein_teom).label("avg_taux_plein_teom"),
            func.avg(TaxeFonciere.taux_global_th).label("avg_taux_global_th"),
        ).filter(TaxeFonciere.annee_cible == annee_cible)

        if postal_code:
            query = query.filter(TaxeFonciere.code_postal == postal_code)

        result = query.first()

        return {
            "annee_cible": annee_cible,
            "postal_code": postal_code,
            "avg_taux_global_tfb": result.avg_taux_global_tfb,
            "avg_taux_global_tfnb": result.avg_taux_global_tfnb,
            "avg_taux_plein_teom": result.avg_taux_plein_teom,
            "avg_taux_global_th": result.avg_taux_global_th,
        } if result else {}

    def create_bulk(self, schemas: List[TaxeFonciereCreateSchema]) -> int:
        """
        Bulk insert multiple taxe foncière records from a list of schemas.

        This method iterates over the provided schemas to construct TaxeFonciere ORM
        objects, casting fields to their expected types and defaulting optional rate
        fields to None where absent. All records are added to the session in a single
        batch and committed together.
        If any error occurs during the process, the transaction is rolled back,
        an error is logged, and 0 is returned.

        Args:
            schemas: List of TaxeFonciereCreateSchema instances representing the records to insert.
        Returns:
            The number of successfully inserted records, or 0 if the operation failed.
        """
        try:
            records = [
                TaxeFonciere(
                    dept=schema.dept,
                    nom_commune=schema.nom_commune,
                    insee_com=schema.insee_com,
                    annee_cible=int(schema.annee_cible),
                    annee_source=int(schema.annee_source),
                    est_fallback=schema.est_fallback if hasattr(schema, 'est_fallback') else False,
                    taux_global_tfb=float(schema.taux_global_tfb) if schema.taux_global_tfb else None,
                    taux_global_tfnb=float(schema.taux_global_tfnb) if schema.taux_global_tfnb else None,
                    taux_plein_teom=float(schema.taux_plein_teom) if schema.taux_plein_teom else None,
                    taux_global_th=float(schema.taux_global_th) if schema.taux_global_th else None,
                )
                for schema in schemas
            ]
            self.db.add_all(records)
            self.db.commit()
            logger.info(f"Bulk inserted {len(records)} taxe foncière records")
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0

    def add_single(self, schema: TaxeFonciereCreateSchema) -> Optional[TaxeFonciere]:
        """
        Add a single taxe foncière record to the database.

        This method constructs a TaxeFonciere ORM object from the provided schema,
        adds it to the session, and commits the transaction. The record is then
        refreshed to reflect any database-generated values.
        If any error occurs, the transaction is rolled back, an error is logged,
        and None is returned.

        Args:
            schema: A TaxeFonciereCreateSchema instance containing the data for the new record.
        Returns:
            The newly created and refreshed TaxeFonciere record, or None if the operation failed.
        """
        try:
            record = TaxeFonciere(**schema.model_dump())
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Added taxe foncière record for {schema.nom_commune}, year {schema.annee_cible}")
            return record
        except Exception as e:
            logger.error(f"Error adding single record: {e}")
            self.db.rollback()
            return None

    def update(self, record_id: int, data: dict) -> Optional[TaxeFonciere]:
        """
        Update an existing taxe foncière record with new field values.

        This method retrieves the record by ID, then iterates over the provided
        data dictionary to set each valid attribute on the ORM object. The session
        is committed and the record refreshed after the update.
        If the record is not found, no changes are made and None is returned.

        Args:
            record_id: The integer primary key of the record to update.
            data: A dictionary mapping field names to their new values.
        Returns:
            The updated and refreshed TaxeFonciere record, or None if the record was not found.
        """
        record = self.db.query(TaxeFonciere).filter(TaxeFonciere.id == record_id).first()
        if record:
            for key, value in data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.db.commit()
            self.db.refresh(record)
            logger.info(f"Updated taxe foncière record {record_id}")
        return record

    def delete(self, record_id: int) -> bool:
        """
        Delete a single taxe foncière record by its primary key.

        This method retrieves the record by ID and, if found, deletes it and
        commits the transaction. If the record does not exist, a warning is
        logged and False is returned.

        Args:
            record_id: The integer primary key of the record to delete.
        Returns:
            True if the record was found and deleted, False otherwise.
        """
        record = self.db.query(TaxeFonciere).filter(TaxeFonciere.id == record_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            logger.info(f"Deleted taxe foncière record {record_id}")
            return True
        logger.warning(f"Taxe foncière record {record_id} not found")
        return False

    def delete_by_year(self, annee_cible: int) -> int:
        """
        Delete all taxe foncière records for a specific target year.

        This method issues a bulk delete query filtered by the given year,
        then commits the transaction and logs the number of deleted records.

        Args:
            annee_cible: The integer target year whose records should be deleted.
        Returns:
            The number of deleted records.
        """
        count = self.db.query(TaxeFonciere).filter(TaxeFonciere.annee_cible == annee_cible).delete()
        self.db.commit()
        logger.info(f"Deleted {count} taxe foncière records for year {annee_cible}")
        return count

    def count_records(self) -> int:
        """
        Count the total number of taxe foncière records in the database.

        This method issues a COUNT query against the entire TaxeFonciere table
        without any filtering.

        Returns:
            The total number of TaxeFonciere records as an integer.
        """
        return self.db.query(TaxeFonciere).count()

    def count_by_year(self, annee_cible: int) -> int:
        """
        Count the number of taxe foncière records for a specific target year.

        This method issues a COUNT query filtered by the given year.

        Args:
            annee_cible: The integer target year to count records for.
        Returns:
            The number of TaxeFonciere records for the specified year.
        """
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.annee_cible == annee_cible).count()

    def get_statistics(self) -> dict:
        """
        Compute global statistics about the taxe foncière dataset.

        This method aggregates several metrics across the entire TaxeFonciere table,
        including total record count, the earliest and latest target years present,
        the number of distinct communes, departments, and years represented, and
        the total number of records that relied on a fallback year.

        Returns:
            A dict containing total_records, min_year, max_year, unique_communes,
            unique_departments, unique_years, and fallback_records, with None for
            any metric where no data is available.
        """
        from sqlalchemy import func

        total = self.count_records()

        min_year_query = self.db.query(TaxeFonciere.annee_cible).order_by(TaxeFonciere.annee_cible).first()
        max_year_query = self.db.query(TaxeFonciere.annee_cible).order_by(TaxeFonciere.annee_cible.desc()).first()

        fallback_count = self.db.query(TaxeFonciere).filter(TaxeFonciere.est_fallback == True).count()

        return {
            "total_records": total,
            "min_year": min_year_query[0] if min_year_query else None,
            "max_year": max_year_query[0] if max_year_query else None,
            "unique_communes": self.db.query(TaxeFonciere.insee_com).distinct().count(),
            "unique_departments": self.db.query(TaxeFonciere.dept).distinct().count(),
            "unique_years": self.db.query(TaxeFonciere.annee_cible).distinct().count(),
            "fallback_records": fallback_count
        }