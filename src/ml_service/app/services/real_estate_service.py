import pandas as pd
from pathlib import Path
from typing import Optional

from ..model.database import engine
from ..schemas.real_estate_schema import RealEstateMktCreateSchema
from ..repositories.real_estate_repository import RealEstateMktRepository


class RealEstateService:
    """Service for loading and managing real estate market data."""

    def __init__(self):
        self.repo = RealEstateMktRepository(db=next(self._get_db()))
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
            return pd.read_csv(file_path, sep=";", dtype={"code_commune": str})
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean real estate data."""
        required_columns = ["code_commune", "annee", "prix_m2", "surface_reelle_bati", "nb_ventes"]
        
        df = df.dropna(subset=["code_commune", "annee"])
        
        df["code_commune"] = pd.to_numeric(df["code_commune"], errors="coerce")
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df["prix_m2"] = pd.to_numeric(df["prix_m2"], errors="coerce")
        df["surface_reelle_bati"] = pd.to_numeric(df["surface_reelle_bati"], errors="coerce")
        df["nb_ventes"] = pd.to_numeric(df["nb_ventes"], errors="coerce")
        
        df = df.dropna(subset=["code_commune", "annee"])
        
        return df

    def sync_from_csv(self, file_path: Optional[str] = None, replace: bool = False) -> dict:
        """Sync real estate data from CSV file to database."""
        if file_path is None:
            file_path = str(self.data_path / "real_estate_market.csv")
        
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
                    DELETE FROM real_estate_market
                """).all())
                self.repo.db.commit()
            
            records = [
                RealEstateMktCreateSchema(**row.to_dict())
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

    def get_price_statistics(self, annee: int) -> dict:
        """Get price statistics for a year."""
        try:
            return self.repo.get_average_price_by_year(annee)
        except Exception as e:
            return {"error": str(e)}
