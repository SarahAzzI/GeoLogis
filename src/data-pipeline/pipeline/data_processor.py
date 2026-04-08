"""
Data processor service that orchestrates the entire data processing pipeline.
Coordinates data loading, cleaning, normalization, and storage.
"""
import pandas as pd
import logging
from typing import Optional, List
from pathlib import Path

from ..transform.cleaning import DataCleaner
from ..transform.normalization import DataNormalizer

logger = logging.getLogger(__name__)


class DataProcessor:
    """Orchestrates the complete data processing pipeline."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.cleaner = DataCleaner()
        self.normalizer = DataNormalizer()
        self.processed_data: Optional[pd.DataFrame] = None
    
    def process_dataframe(
        self, 
        df: pd.DataFrame, 
        clean: bool = True, 
        normalize: bool = True,
        filter_years: bool = True,
        min_year: int = 2020,
        max_year: int = 2025
    ) -> pd.DataFrame:
        """
        Process a dataframe through the complete pipeline.
        
        Args:
            df: Input dataframe
            clean: Whether to apply cleaning
            normalize: Whether to apply normalization
            filter_years: Whether to filter by year range
            min_year: Minimum year
            max_year: Maximum year
            
        Returns:
            Processed dataframe
        """
        logger.info(f"Starting data processing pipeline. Input: {len(df)} rows, {len(df.columns)} columns")
        
        # Cleaning step
        if clean:
            logger.info("Applying cleaning...")
            df = self.cleaner.clean(df)
        
        # Year filtering
        if filter_years and "annee" in df.columns:
            logger.info(f"Filtering to years {min_year}-{max_year}...")
            df = self.cleaner.filter_by_year_range(df, min_year, max_year)
        
        # Normalization step
        if normalize:
            logger.info("Applying normalization...")
            df = self.normalizer.normalize(df)
        
        self.processed_data = df
        logger.info(f"Data processing completed. Output: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def process_csv(
        self, 
        csv_path: str,
        sep: str = ";",
        clean: bool = True,
        normalize: bool = True,
        filter_years: bool = True,
        min_year: int = 2020,
        max_year: int = 2025
    ) -> pd.DataFrame:
        """
        Load and process a CSV file.
        
        Args:
            csv_path: Path to CSV file
            sep: CSV separator
            clean: Whether to apply cleaning
            normalize: Whether to apply normalization
            filter_years: Whether to filter by year range
            min_year: Minimum year
            max_year: Maximum year
            
        Returns:
            Processed dataframe
        """
        logger.info(f"Loading CSV from {csv_path}")
        try:
            df = pd.read_csv(csv_path, sep=sep)
            logger.info(f"CSV loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            raise
        
        return self.process_dataframe(
            df, 
            clean=clean, 
            normalize=normalize, 
            filter_years=filter_years,
            min_year=min_year,
            max_year=max_year
        )
    
    def merge_data_sources(
        self,
        real_estate_df: Optional[pd.DataFrame] = None,
        communes_df: Optional[pd.DataFrame] = None,
        inflation_df: Optional[pd.DataFrame] = None,
        taxe_fonciere_df: Optional[pd.DataFrame] = None,
        join_type: str = "inner"
    ) -> pd.DataFrame:
        """
        Merge data from multiple sources.
        
        Args:
            real_estate_df: Real estate market data
            communes_df: Communes/municipality data
            inflation_df: Inflation rate data
            taxe_fonciere_df: Property tax data
            join_type: Type of join to perform
            
        Returns:
            Merged dataframe
        """
        logger.info("Merging data from multiple sources...")
        
        dfs_to_merge = []
        
        if real_estate_df is not None:
            dfs_to_merge.append(("real_estate", real_estate_df))
        if communes_df is not None:
            dfs_to_merge.append(("communes", communes_df))
        if inflation_df is not None:
            dfs_to_merge.append(("inflation", inflation_df))
        if taxe_fonciere_df is not None:
            dfs_to_merge.append(("taxe_fonciere", taxe_fonciere_df))
        
        if not dfs_to_merge:
            logger.error("No dataframes provided for merging")
            raise ValueError("At least one dataframe must be provided")
        
        if len(dfs_to_merge) == 1:
            logger.info(f"Only one data source provided: {dfs_to_merge[0][0]}")
            return dfs_to_merge[0][1]
        
        # Start with the first dataframe
        result_df = dfs_to_merge[0][1].copy()
        logger.info(f"Starting with {dfs_to_merge[0][0]}: {len(result_df)} rows")
        
        # Merge remaining dataframes
        for name, df in dfs_to_merge[1:]:
            initial_len = len(result_df)
            
            # Determine key columns for join
            join_keys = self._find_join_keys(result_df, df)
            
            if join_keys:
                logger.info(f"Merging {name} on keys: {join_keys}")
                result_df = result_df.merge(df, on=join_keys, how=join_type)
            else:
                logger.warning(f"No common columns found for merging {name}, using cartesian product")
                result_df = result_df.merge(df, left_index=True, right_index=True, how=join_type)
            
            merged_len = len(result_df)
            logger.info(f"After merging {name}: {initial_len} -> {merged_len} rows")
        
        logger.info(f"Data merge completed. Final: {len(result_df)} rows, {len(result_df.columns)} columns")
        return result_df
    
    def _find_join_keys(self, df1: pd.DataFrame, df2: pd.DataFrame) -> List[str]:
        """
        Find common columns between two dataframes for joining.
        
        Args:
            df1: First dataframe
            df2: Second dataframe
            
        Returns:
            List of common column names
        """
        common_cols = list(set(df1.columns) & set(df2.columns))
        
        # Prioritize common keys
        priority_keys = ["annee", "code_commune", "code_postal", "code_insee", "dep_code"]
        join_keys = [k for k in priority_keys if k in common_cols]
        
        return join_keys if join_keys else common_cols
    
    def get_processing_stats(self) -> dict:
        """
        Get statistics about the processed data.
        
        Returns:
            Dictionary with processing statistics
        """
        if self.processed_data is None:
            return {"error": "No data has been processed yet"}
        
        return self.normalizer.get_feature_info(self.processed_data)
    
    def save_processed_data(self, output_path: str, format: str = "csv") -> bool:
        """
        Save processed data to file.
        
        Args:
            output_path: Path where to save the data
            format: Output format ('csv' or 'parquet')
            
        Returns:
            True if save was successful
        """
        if self.processed_data is None:
            logger.error("No processed data to save")
            return False
        
        try:
            if format == "csv":
                self.processed_data.to_csv(output_path, index=False)
            elif format == "parquet":
                self.processed_data.to_parquet(output_path, index=False)
            else:
                logger.error(f"Unsupported format: {format}")
                return False
            
            logger.info(f"Data saved to {output_path} in {format} format")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False
