import pandas as pd
from pathlib import Path
from typing import Optional

from ..model.database import engine
from ..schemas.inflation_rate_schema import InflationRateCreateSchema
from ..repositories.inflation_rate_repository import InflationRateRepository


class InflationRateService:
    """Service for loading and managing inflation rate data."""

    def __init__(self):
        self.repo = InflationRateRepository(db=next(self._get_db()))
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
            return pd.read_csv(file_path, dtype={"annee": int})
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean inflation rate data."""
        required_columns = ["annee", "taux_inflation"]
        
        df = df.dropna(subset=required_columns)
        
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df["taux_inflation"] = pd.to_numeric(df["taux_inflation"], errors="coerce")
        
        df = df.fillna("")
        
        return df

    def sync_from_csv(self, file_path: Optional[str] = None, replace: bool = False) -> dict:
        """Sync inflation rate data from CSV file to database."""
        if file_path is None:
            file_path = str(self.data_path / "inflation_rates.csv")
        
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
                    DELETE FROM inflation_rates
                """).all())
                self.repo.db.commit()
            
            records = [
                InflationRateCreateSchema(**row.to_dict())
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

    def get_average_inflation(self, annee_start: int, annee_end: int) -> dict:
        """Get average inflation for a period."""
        try:
            average = self.repo.get_average_inflation(annee_start, annee_end)
            return {
                "period_start": annee_start,
                "period_end": annee_end,
                "average_inflation": average
            }
        except Exception as e:
            return {"error": str(e)}

    def get_inflation_by_year(self, annee: int) -> dict:
        """Get inflation rate for a specific year."""
        try:
            record = self.repo.get_by_year(annee)
            if not record:
                return {"error": f"No data for year {annee}"}
            
            return {
                "annee": record.annee,
                "taux_inflation": record.taux_inflation,
                "sources": record.sources
            }
        except Exception as e:
            return {"error": str(e)}
