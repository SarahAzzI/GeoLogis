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
        """
        Get database session. This is a generator that yields a database session and ensures it is closed after use.
        
        Yields:
            Database session for performing operations
        """
        from ..model.database import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load CSV file and return DataFrame.

        Args:
            file_path: Path to the CSV file containing inflation rate data.

        Returns:
            DataFrame with the loaded data. If the file is not found or cannot be read, an empty DataFrame is returned.

        """
        try:
            return pd.read_csv(file_path, dtype={"annee": int})
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()

    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean inflation rate data. This includes:
        - Dropping rows with missing required fields (annee, taux_inflation)
        - Converting data types to correct formats
        - Filling missing values with defaults if necessary

        Args:
            df: DataFrame to validate
        Returns:
            Cleaned and validated DataFrame
        """
        required_columns = ["annee", "taux_inflation"]
        
        df = df.dropna(subset=required_columns)
        
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df["taux_inflation"] = pd.to_numeric(df["taux_inflation"], errors="coerce")
        
        df = df.fillna("")
        
        return df

    def sync_from_csv(self, file_path: Optional[str] = None, replace: bool = False) -> dict:
        """
        Sync inflation rate data from CSV file to database. 
        This includes loading the data, validating it, and then inserting it into the database. 
        
        If the replace flag is set, existing data will be cleared before inserting new records.

        Args:
            file_path: Optional path to the CSV file. If None, defaults to "flatfiles/inflation_rates.csv"
            replace: Whether to replace existing records in the database
        Returns:
            Dictionary with sync status and number of records synced
        """
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
        """
        Get average inflation for a period. This calculates the average inflation rate between the specified start and end years.

        Args:
            annee_start: Starting year of the period (inclusive)
            annee_end: Ending year of the period (inclusive)

        Returns:
            Dictionary with the average inflation rate for the specified period or an error message if something goes wrong

        """
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
        """
        Get inflation rate for a specific year. This retrieves the inflation rate for the specified year from the database.

        Args:
            annee: Year for which to retrieve the inflation rate

        Returns:
            Dictionary with the inflation rate for the specified year or an error message if no data is found
        """
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
