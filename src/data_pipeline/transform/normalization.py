"""
Normalization module for data standardization and feature engineering.
Handles data scaling, transformation, and feature creation.
"""
import pandas as pd
import numpy as np
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Handles data normalization and feature engineering."""
    
    def __init__(self):
        """Initialize the normalizer."""
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform normalization operations on dataframe.
        
        Args:
            df: Input dataframe to normalize
            
        Returns:
            Normalized dataframe
        """
        logger.info(f"Starting normalization process on {len(df)} rows")
        df = df.copy()
        
        # Identify column types
        self.numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        
        logger.info(f"Numeric columns: {len(self.numeric_cols)}, Categorical columns: {len(self.categorical_cols)}")
        
        # Perform feature engineering
        df = self._create_features(df)
        
        # Normalize numeric values
        df = self._normalize_numeric(df)
        
        logger.info(f"Normalization completed")
        return df
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived features through feature engineering.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with new features
        """
        logger.info("Creating derived features")
        
        # Population density
        if "population" in df.columns and "superficie_km2" in df.columns:
            df["densite"] = df["population"] / (df["superficie_km2"] + 1)
            logger.info("Created densite feature")
        
        # Tax ratio
        if "taux_global_tfb" in df.columns and "taux_global_th" in df.columns:
            df["ratio_taxe"] = df["taux_global_tfb"] / (df["taux_global_th"] + 1)
            logger.info("Created ratio_taxe feature")
        
        # Sales per capita
        if "sales_numbers" in df.columns and "population" in df.columns:
            df["ventes_par_habitant"] = df["sales_numbers"] / (df["population"] + 1)
            logger.info("Created ventes_par_habitant feature")
        
        # Tax times population
        if "taux_global_tfb" in df.columns and "population" in df.columns:
            df["taxe_x_population"] = df["taux_global_tfb"] * (df["population"] + 1)
            logger.info("Created taxe_x_population feature")
        
        # Evolution features (by postal code)
        if "code_postal" in df.columns and "sales_numbers" in df.columns:
            df["evolution_ventes"] = df.groupby("code_postal")["sales_numbers"].pct_change()
            logger.info("Created evolution_ventes feature")
        
        if "code_postal" in df.columns and "taux_global_tfb" in df.columns:
            df["evolution_taxe"] = df.groupby("code_postal")["taux_global_tfb"].pct_change()
            logger.info("Created evolution_taxe feature")
        
        # Tax vs department average
        if "taux_global_tfb" in df.columns and "dep_code" in df.columns:
            df["taxe_vs_moyenne_dep"] = df["taux_global_tfb"] / df.groupby("dep_code")["taux_global_tfb"].transform("mean")
            logger.info("Created taxe_vs_moyenne_dep feature")
        
        # Average sales by department
        if "sales_numbers" in df.columns and "dep_code" in df.columns:
            df["ventes_moyennes_dep"] = df.groupby("dep_code")["sales_numbers"].transform("mean")
            logger.info("Created ventes_moyennes_dep feature")
        
        # Fill NaN values from feature engineering (e.g., first month has no pct_change)
        df = df.fillna(0)
        
        return df
    
    def _normalize_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize numeric columns to 0-1 range (Min-Max scaling).
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with normalized numeric values
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        
        for col in numeric_cols:
            min_val = df[col].min()
            max_val = df[col].max()
            
            if max_val - min_val != 0:
                df[col] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[col] = 0
        
        logger.info(f"Normalized {len(numeric_cols)} numeric columns using Min-Max scaling")
        return df
    
    def standardize_numeric(self, df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Standardize numeric columns (z-score normalization: (x - mean) / std).
        
        Args:
            df: Input dataframe
            exclude_cols: Columns to exclude from standardization
            
        Returns:
            Dataframe with standardized numeric values
        """
        exclude_cols = exclude_cols or []
        numeric_cols = df.select_dtypes(include=["number"]).columns
        numeric_cols = [c for c in numeric_cols if c not in exclude_cols]
        
        for col in numeric_cols:
            mean_val = df[col].mean()
            std_val = df[col].std()
            
            if std_val != 0:
                df[col] = (df[col] - mean_val) / std_val
            else:
                df[col] = 0
        
        logger.info(f"Standardized {len(numeric_cols)} numeric columns using z-score normalization")
        return df
    
    def encode_categorical(self, df: pd.DataFrame, categorical_cols: Optional[List[str]] = None, method: str = "label") -> Tuple[pd.DataFrame, dict]:
        """
        Encode categorical variables.
        
        Args:
            df: Input dataframe
            categorical_cols: Columns to encode
            method: Encoding method ('label' or 'onehot')
            
        Returns:
            Tuple of (encoded dataframe, encoding mappings)
        """
        from sklearn.preprocessing import LabelEncoder
        
        if categorical_cols is None:
            categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        
        encodings = {}
        df = df.copy()
        
        for col in categorical_cols:
            if col in df.columns:
                if method == "label":
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype("str"))
                    encodings[col] = {i: label for i, label in enumerate(le.classes_)}
                    logger.info(f"Label encoded column {col}")
        
        return df, encodings
    
    def clip_outliers(self, df: pd.DataFrame, std_dev: float = 3.0) -> pd.DataFrame:
        """
        Remove or clip outliers beyond n standard deviations.
        
        Args:
            df: Input dataframe
            std_dev: Number of standard deviations for outlier threshold
            
        Returns:
            Dataframe with clipped outliers
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            lower_bound = mean - (std_dev * std)
            upper_bound = mean + (std_dev * std)
            
            df[col] = df[col].clip(lower_bound, upper_bound)
        
        logger.info(f"Clipped outliers for {len(numeric_cols)} numeric columns using {std_dev} std dev threshold")
        return df
    
    def get_feature_info(self, df: pd.DataFrame) -> dict:
        """
        Get information about features in the dataset.
        
        Args:
            df: Input dataframe
            
        Returns:
            Dictionary with feature information
        """
        return {
            "numeric_features": df.select_dtypes(include=["number"]).columns.tolist(),
            "categorical_features": df.select_dtypes(include=["object"]).columns.tolist(),
            "total_features": len(df.columns),
            "total_rows": len(df),
            "missing_values": df.isna().sum().to_dict()
        }
