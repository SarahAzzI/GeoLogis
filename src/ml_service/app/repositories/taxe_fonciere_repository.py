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
        """Get all taxe foncière records."""
        return self.db.query(TaxeFonciere).all()

    def get_by_id(self, record_id: int) -> Optional[TaxeFonciere]:
        """Get a taxe foncière record by ID."""
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.id == record_id).first()

    def get_by_dept(self, dept: str) -> List[TaxeFonciere]:
        """Get all records for a specific department."""
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.dept == dept).all()
    
    def get_by_postal_code(self, postal_code: str) -> List[TaxeFonciere]:
        """Get all records for a specific postal code."""
        return self.db.query(TaxeFonciere).filter(TaxeFonciere.code_postal == postal_code).all()
    
    def get_by_postal_code_and_year(self, postal_code: str, annee_cible: int) -> List[TaxeFonciere]:
        """Get records for a specific postal code and year."""
        return self.db.query(TaxeFonciere).filter(
            and_(
                TaxeFonciere.code_postal == postal_code,
                TaxeFonciere.annee_cible == annee_cible,
            )
        ).all()
    
    def get_by_postal_code_and_dept(self, postal_code: str, dept: str) -> List[TaxeFonciere]:
        """Get records for a specific postal code and department."""
        return self.db.query(TaxeFonciere).filter(
            and_(
                TaxeFonciere.code_postal == postal_code,
                TaxeFonciere.dept == dept,
            )
        ).all()

    def get_by_insee(self, insee_com: str) -> List[TaxeFonciere]:
        """Get all records for a specific INSEE commune code."""
        return self.db.query(TaxeFonciere).filter(
            TaxeFonciere.insee_com == insee_com
        ).all()

    def get_by_year(self, annee_cible: int) -> List[TaxeFonciere]:
        """Get all records for a specific year."""
        return self.db.query(TaxeFonciere).filter(
            TaxeFonciere.annee_cible == annee_cible
        ).all()

    def get_by_dept_and_year(
        self, dept: str, annee_cible: int
    ) -> Optional[TaxeFonciere]:
        """Get a record for a specific department and year."""
        return self.db.query(TaxeFonciere).filter(
            and_(
                TaxeFonciere.dept == dept,
                TaxeFonciere.annee_cible == annee_cible,
            )
        ).first()

    def count_fallback(self, postal_code: Optional[str] = None) -> int:
        """Get count of records that used fallback years, optionally filtered by postal code."""
        query = self.db.query(TaxeFonciere).filter(TaxeFonciere.est_fallback == True)
        if postal_code:
            query = query.filter(TaxeFonciere.code_postal == postal_code)
        return query.count()

    def get_average_rates_by_year(self, annee_cible: int, postal_code: Optional[str] = None) -> dict:
        """Get average tax rates for a specific year, optionally filtered by postal code."""
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
        """Bulk insert multiple taxe foncière records from schemas."""
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
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0
