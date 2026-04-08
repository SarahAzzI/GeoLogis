import pandas as pd
from pathlib import Path
from typing import Optional

from ..model.database import engine
from ..schemas.communes_schema import CommuneCreateSchema
from ..repositories.communes_repository import CommuneRepository


class CommuneService:
    """Service for loading and managing commune geographic data."""

    def __init__(self):
        self.repo = CommuneRepository(db=next(self._get_db()))
        self.data_path = Path(__file__).parent.parent.parent.parent / "flatfiles"

    @staticmethod
    def _get_db():
        """Get database session."""
        from ..model.database import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load CSV file and return DataFrame."""
        try:
            return pd.read_csv(
                file_path,
                sep=";",
                dtype={
                    "code_insee": str,
                    "dep_code": str,
                    "reg_code": str,
                    "code_postal": str,
                    "zone_emploi": str,
                },
            )
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean commune data."""
        required_columns = ["code_insee", "nom_standard", "annee"]
        
        df = df.dropna(subset=required_columns)
        
        # Keep code_insee as string (supports Corsican codes like 2A004)
        df["code_insee"] = df["code_insee"].astype(str)
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        
        if "population" in df.columns:
            df["population"] = pd.to_numeric(df["population"], errors="coerce")
        if "densite" in df.columns:
            df["densite"] = pd.to_numeric(df["densite"], errors="coerce")
        if "superficie_km2" in df.columns:
            df["superficie_km2"] = pd.to_numeric(df["superficie_km2"], errors="coerce")
        
        df = df.fillna("")
        
        return df

    def sync_from_csv(self, file_path: Optional[str] = None, replace: bool = False) -> dict:
        """Sync commune data from CSV file to database."""
        if file_path is None:
            file_path = str(self.data_path / "communes.csv")
        
        try:
            # Load and validate
            df = self.load_csv(file_path)
            if df.empty:
                return {"error": "No data loaded", "records_synced": 0}
            
            df = self.validate_data(df)
            if df.empty:
                return {"error": "No valid data after validation", "records_synced": 0}
            
            # Clear existing data if replace flag is set
            if replace:
                self.repo.db.query(self.repo.db.query("""
                    DELETE FROM communes
                """).all())
                self.repo.db.commit()
            
            records = [
                CommuneCreateSchema(**row.to_dict())
                for _, row in df.iterrows()
            ]
            
            count = self.repo.create_bulk(records)
            
            return {
                "status": "success",
                "records_synced": count,
                "source": file_path
            }
        
        except Exception as e:
            return {"error": str(e), "records_synced": 0}

    def get_department_statistics(self, dep_code: str, annee: int) -> dict:
        """Get department statistics for a year."""
        try:
            return self.repo.get_department_stats(dep_code, annee)
        except Exception as e:
            return {"error": str(e)}

    def get_communes_by_department(self, dep_code: str) -> dict:
        """Get all communes in a department."""
        try:
            communes = self.repo.get_by_department(dep_code)
            return {
                "dep_code": dep_code,
                "count": len(communes),
                "communes": [c.nom_standard for c in communes]
            }
        except Exception as e:
            return {"error": str(e)}
