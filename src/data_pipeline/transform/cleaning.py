"""
Cleaning module for data preprocessing.
Handles missing values, data validation, and basic transformations.
"""
import pandas as pd
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class DataCleaner:
    """Handles data cleaning operations."""
    
    def __init__(self, drop_columns: Optional[List[str]] = None):
        """
        Initialize the data cleaner.
        
        Args:
            drop_columns: List of columns to drop from the dataframe
        """
        self.drop_columns = drop_columns or ["dep_nom", "reg_nom", "variation"]
        self.bad_dep_codes = ["2A", "2B"]
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform cleaning operations on dataframe.
        
        Args:
            df: Input dataframe to clean
            
        Returns:
            Cleaned dataframe
        """
        logger.info(f"Starting cleaning process on {len(df)} rows")
        df = df.copy()
        
        # Drop unnecessary columns
        existing_drop = [c for c in self.drop_columns if c in df.columns]
        if existing_drop:
            logger.info(f"Dropping columns: {existing_drop}")
            df = df.drop(columns=existing_drop)
        
        # Remove rows with bad department codes
        if "dep_code" in df.columns:
            initial_len = len(df)
            df = df[~df["dep_code"].isin(self.bad_dep_codes)]
            removed = initial_len - len(df)
            if removed > 0:
                logger.info(f"Removed {removed} rows with bad department codes")
        
        # Handle missing values
        logger.info(f"Removing rows with missing values. Before: {len(df)} rows")
        df = df.dropna()
        logger.info(f"After dropna: {len(df)} rows")
        
        # Standardize column types
        df = self._standardize_types(df)
        
        # Reset index
        df = df.reset_index(drop=True)
        
        logger.info(f"Cleaning completed. Final rows: {len(df)}")
        return df
    
    def _standardize_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize data types across the dataframe.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with standardized types
        """
        # Integer columns
        int_cols = ["annee", "code_commune", "code_postal", "population", "zone_emploi", "sales_numbers"]
        for col in int_cols:
            if col in df.columns:
                try:
                    df[col] = df[col].astype("int64")
                except Exception as e:
                    logger.warning(f"Could not convert {col} to int64: {e}")
        
        # Float columns
        float_cols = ["prix_m2", "superficie_km2", "taux_global_tfb", "taux_global_tfnb", "taux_plein_teom", "taux_global_th"]
        for col in float_cols:
            if col in df.columns:
                try:
                    df[col] = df[col].astype("float64")
                except Exception as e:
                    logger.warning(f"Could not convert {col} to float64: {e}")
        
        # String columns
        str_cols = ["nom_commune", "dep_nom", "reg_nom"]
        for col in str_cols:
            if col in df.columns:
                try:
                    df[col] = df[col].astype("str")
                except Exception as e:
                    logger.warning(f"Could not convert {col} to str: {e}")
        
        return df
    
    def handle_missing_numeric(self, df: pd.DataFrame, strategy: str = "mean") -> pd.DataFrame:
        """
        Handle missing values in numeric columns.
        
        Args:
            df: Input dataframe
            strategy: Strategy for filling missing values ('mean', 'median', 'forward_fill')
            
        Returns:
            Dataframe with handled missing values
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        
        for col in numeric_cols:
            if df[col].isna().any():
                if strategy == "mean":
                    df[col].fillna(df[col].mean(), inplace=True)
                elif strategy == "median":
                    df[col].fillna(df[col].median(), inplace=True)
                elif strategy == "forward_fill":
                    df[col].fillna(method="ffill", inplace=True)
                logger.info(f"Filled {df[col].isna().sum()} missing values in {col} using {strategy}")
        
        return df
    
    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate rows.
        
        Args:
            df: Input dataframe
            subset: Columns to consider for duplicates
            
        Returns:
            Dataframe without duplicates
        """
        initial_len = len(df)
        df = df.drop_duplicates(subset=subset)
        removed = initial_len - len(df)
        logger.info(f"Removed {removed} duplicate rows")
        return df
    
    def filter_by_year_range(self, df: pd.DataFrame, min_year: int = 2020, max_year: int = 2025) -> pd.DataFrame:
        """
        Filter dataframe to include only specific year range.
        
        Args:
            df: Input dataframe
            min_year: Minimum year to include
            max_year: Maximum year to include
            
        Returns:
            Filtered dataframe
        """
        if "annee" not in df.columns:
            logger.warning("annee column not found, skipping year filtering")
            return df
        
        initial_len = len(df)
        df = df[(df["annee"] >= min_year) & (df["annee"] <= max_year)]
        filtered = initial_len - len(df)
        logger.info(f"Filtered by year range {min_year}-{max_year}. Removed {filtered} rows")
        return df
