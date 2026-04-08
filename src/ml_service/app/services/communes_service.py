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
        self.data_path = Path(__file__).parent.parent.parent.parent / "flatfiles" / "commune_france" / "communes_france_2025.csv"

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
        """
        Load commune data from a CSV file. The CSV is expected to have columns like:
        - code_insee
        - dep_code
        - reg_code
        - code_postal
        - zone_emploi

        If the file is not found or cannot be read, an empty DataFrame is returned. 
        The code_insee column is treated as a string to preserve leading zeros and support Corsican codes (2A, 2B).

        Args:
            file_path: Path to the CSV file
        Returns:
            DataFrame with commune data
        """
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
        """
        Validate and clean commune data. This includes:
        - Dropping unnecessary columns
        - Removing rows with bad department codes (2A, 2B)
        - Handling missing values in critical columns (code_insee, nom_standard, annee)
        - Standardizing data types (code_insee as string, annee as int)

        If critical columns are missing or empty after validation, an empty DataFrame is returned.

        Args:
            df: Input DataFrame to validate
        Returns:
            Validated and cleaned DataFrame
        """

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
        """
        Sync commune data from CSV file to database. 

        If replace is True, existing commune records will be deleted before inserting new ones.

        Args:
            file_path: Optional path to the CSV file. If None, defaults to "flatfiles/communes.csv"
            replace: Whether to replace existing records in the database

        Returns:
            Dictionary with sync status and number of records synced
        """
        if file_path is None:
            file_path = str(self.data_path / "communes_france_2025.csv")
        
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
        """
        Get department statistics for a year. This includes count of communes and average population density for the specified department and year.
        
        Args:
            dep_code: Department code (e.g., "75" for Paris)
            annee: Year for which to get statistics (e.g., 2020)
        Returns:
            Dictionary with department statistics or error message
        """
        try:
            return self.repo.get_department_stats(dep_code, annee)
        except Exception as e:
            return {"error": str(e)}

    def get_communes_by_department(self, dep_code: str) -> dict:
        """
        Get all communes in a department. Returns a list of commune names for the specified department code.

        Args:
            dep_code: Department code (e.g., "75" for Paris)
            count: Number of communes in the department
            communes: List of commune names in the department
        Returns:
            Dictionary with count of communes and list of commune names or error message
        """
        try:
            communes = self.repo.get_by_department(dep_code)
            return {
                "dep_code": dep_code,
                "count": len(communes),
                "communes": [c.nom_standard for c in communes]
            }
        except Exception as e:
            return {"error": str(e)}
