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
        """Get all commune records."""
        return self.db.query(Commune).all()

    def get_by_id(self, record_id: int) -> Optional[Commune]:
        """Get a record by ID."""
        return self.db.query(Commune).filter(Commune.id == record_id).first()

    def get_by_insee(self, code_insee: str) -> List[Commune]:
        """Get all records for a specific INSEE code."""
        return self.db.query(Commune).filter(
            Commune.code_insee == code_insee
        ).order_by(Commune.annee.desc()).all()

    def get_by_postal_code(self, code_postal: str) -> List[Commune]:
        """Get all communes for a specific postal code."""
        return self.db.query(Commune).filter(
            Commune.code_postal == code_postal
        ).all()

    def get_by_department(self, dep_code: str) -> List[Commune]:
        """Get all communes in a department."""
        return self.db.query(Commune).filter(
            Commune.dep_code == dep_code
        ).all()

    def get_by_region(self, reg_code: str) -> List[Commune]:
        """Get all communes in a region."""
        return self.db.query(Commune).filter(
            Commune.reg_code == reg_code
        ).all()

    def get_by_year(self, annee: int) -> List[Commune]:
        """Get all communes for a specific year."""
        return self.db.query(Commune).filter(Commune.annee == annee).all()

    def get_by_insee_and_year(self, code_insee: str, annee: int) -> Optional[Commune]:
        """Get a specific commune in a specific year."""
        return self.db.query(Commune).filter(
            and_(
                Commune.code_insee == code_insee,
                Commune.annee == annee,
            )
        ).first()

    def filter_records(self, filters: CommuneFilterSchema) -> List[Commune]:
        """Filter records based on multiple criteria."""
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
        """Get department statistics for a year."""
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
        """Bulk insert multiple commune records from schemas."""
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
            return len(records)
        except Exception as e:
            logger.error(f"Error in create_bulk: {e}", exc_info=True)
            self.db.rollback()
            return 0
    