"""
Data processor service that combines cleaning and normalization.
Provides a unified interface for data preprocessing pipeline.
"""
import pandas as pd
import logging
from typing import Optional, List, Tuple
import sys
from pathlib import Path

# Add data-pipeline to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "data-pipeline"))

from transform.cleaning import DataCleaner
from transform.normalization import DataNormalizer

logger = logging.getLogger(__name__)


class DataProcessorService:
    """Service for complete data processing pipeline (cleaning + normalization)."""
    
    def __init__(
        self,
        drop_columns: Optional[List[str]] = None,
        normalize_method: str = "minmax"
    ):
        """
        Initialize the data processor service.
        
        Args:
            drop_columns: Columns to drop during cleaning
            normalize_method: Method for normalization ('minmax', 'zscore')
        """
        self.cleaner = DataCleaner(drop_columns=drop_columns)
        self.normalizer = DataNormalizer()
        self.normalize_method = normalize_method
        self.processing_stats = {}
        
    def process(
        self,
        df: pd.DataFrame,
        clean: bool = True,
        normalize: bool = True,
        handle_outliers: bool = False
    ) -> pd.DataFrame:
        """
        Execute complete data processing pipeline.
        
        Args:
            df: Input dataframe
            clean: Whether to apply cleaning
            normalize: Whether to apply normalization
            handle_outliers: Whether to clip outliers
            
        Returns:
            Processed dataframe
        """
        logger.info(f"Starting data processing pipeline. Input rows: {len(df)}")
        original_shape = df.shape
        
        # Step 1: Cleaning
        if clean:
            logger.info("Step 1: Cleaning")
            df = self.cleaner.clean(df)
            logger.info(f"After cleaning: {len(df)} rows, {len(df.columns)} columns")
        
        # Step 2: Remove duplicates
        logger.info("Step 2: Removing duplicates")
        initial_len = len(df)
        df = self.cleaner.remove_duplicates(df)
        logger.info(f"Removed {initial_len - len(df)} duplicate rows")
        
        # Step 3: Handle outliers
        if handle_outliers:
            logger.info("Step 3: Handling outliers")
            df = self.normalizer.clip_outliers(df)
        
        # Step 4: Normalization
        if normalize:
            logger.info("Step 4: Normalization")
            df = self.normalizer.normalize(df)
            
            if self.normalize_method == "zscore":
                logger.info("Applying z-score standardization")
                df = self.normalizer.standardize_numeric(df)
            
            logger.info(f"After normalization: {len(df)} rows, {len(df.columns)} columns")
        
        # Record statistics
        self.processing_stats = {
            "original_shape": original_shape,
            "final_shape": df.shape,
            "rows_removed": original_shape[0] - len(df),
            "rows_retained": len(df),
            "retention_rate": (len(df) / original_shape[0]) * 100 if original_shape[0] > 0 else 0,
            "normalize_method": self.normalize_method if normalize else None
        }
        
        logger.info(f"Processing complete. Final rows: {len(df)}")
        return df
    
    def process_for_training(
        self,
        df: pd.DataFrame,
        min_year: int = 2020,
        max_year: int = 2025,
        target_col: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Process data specifically for model training.
        Separates features and target if specified.
        
        Args:
            df: Input dataframe
            min_year: Minimum year to include
            max_year: Maximum year to include
            target_col: Column name to use as target (removed from features if present)
            
        Returns:
            Tuple of (processed features, target series if specified)
        """
        logger.info("Processing data for training")
        
        # Filter by year range
        df = self.cleaner.filter_by_year_range(df, min_year=min_year, max_year=max_year)
        
        # Separate target if specified
        target = None
        if target_col and target_col in df.columns:
            logger.info(f"Extracting target column: {target_col}")
            target = df[target_col].copy()
            df = df.drop(columns=[target_col])
        
        # Process features
        df = self.process(df, clean=True, normalize=True, handle_outliers=True)
        
        return df, target
    
    def get_processing_stats(self) -> dict:
        """Get statistics from the last processing operation."""
        return self.processing_stats.copy()
    
    def get_feature_info(self, df: pd.DataFrame) -> dict:
        """Get information about features in the dataframe."""
        return self.normalizer.get_feature_info(df)
    
    def validate_data(self, df: pd.DataFrame) -> dict:
        """
        Validate data quality and return report.
        
        Args:
            df: Dataframe to validate
            
        Returns:
            Validation report
        """
        logger.info("Validating data quality")
        
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
            "total_missing": df.isnull().sum().sum(),
            "missing_rate": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            "duplicates": df.duplicated().sum(),
            "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=["object"]).columns.tolist(),
        }
        
        # Check for infinite values
        try:
            numeric_df = df.select_dtypes(include=["number"])
            inf_count = (numeric_df == float('inf')).sum().sum() + (numeric_df == float('-inf')).sum().sum()
            report["infinite_values"] = int(inf_count)
        except:
            report["infinite_values"] = 0
        
        # Data quality score
        total_issues = report["total_missing"] + report["duplicates"] + report["infinite_values"]
        report["quality_score"] = max(0, 100 - (total_issues / (len(df) * len(df.columns)) * 100))
        
        logger.info(f"Data validation complete. Quality score: {report['quality_score']:.2f}%")
        return report
    
    def handle_missing_values(
        self,
        df: pd.DataFrame,
        strategy: str = "mean",
        threshold: float = 0.5
    ) -> pd.DataFrame:
        """
        Handle missing values in the dataframe.
        
        Args:
            df: Input dataframe
            strategy: Strategy for handling missing values ('mean', 'median', 'forward_fill', 'drop')
            threshold: If missing rate > threshold, drop column
            
        Returns:
            Dataframe with handled missing values
        """
        logger.info(f"Handling missing values using {strategy} strategy")
        
        df = df.copy()
        
        # Drop columns where missing rate > threshold
        for col in df.columns:
            missing_rate = df[col].isnull().sum() / len(df)
            if missing_rate > threshold:
                logger.info(f"Dropping column {col} (missing rate: {missing_rate:.2%})")
                df = df.drop(columns=[col])
        
        # Handle numeric columns
        df = self.cleaner.handle_missing_numeric(df, strategy=strategy)
        
        # Drop rows with any remaining missing values
        df = df.dropna()
        
        logger.info(f"Missing values handled. Final rows: {len(df)}")
        return df
    
    def encode_categorical(
        self,
        df: pd.DataFrame,
        categorical_cols: Optional[List[str]] = None,
        method: str = "label"
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Encode categorical variables.
        
        Args:
            df: Input dataframe
            categorical_cols: Columns to encode
            method: Encoding method ('label' or 'onehot')
            
        Returns:
            Tuple of (encoded dataframe, encoding mappings)
        """
        logger.info(f"Encoding categorical variables using {method} method")
        
        return self.normalizer.encode_categorical(df, categorical_cols=categorical_cols, method=method)
    
    def create_training_splits(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Create training, validation, and test splits.
        
        Args:
            df: Input dataframe
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
            random_state: Random state for reproducibility
            
        Returns:
            Tuple of (train, validation, test) dataframes
        """
        assert train_ratio + val_ratio + test_ratio == 1.0, "Ratios must sum to 1.0"
        
        logger.info(f"Creating splits: train={train_ratio}, val={val_ratio}, test={test_ratio}")
        
        # Shuffle dataframe
        df_shuffled = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        # Calculate split indices
        train_idx = int(len(df_shuffled) * train_ratio)
        val_idx = train_idx + int(len(df_shuffled) * val_ratio)
        
        train_df = df_shuffled[:train_idx]
        val_df = df_shuffled[train_idx:val_idx]
        test_df = df_shuffled[val_idx:]
        
        logger.info(f"Splits created: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
        
        return train_df, val_df, test_df
