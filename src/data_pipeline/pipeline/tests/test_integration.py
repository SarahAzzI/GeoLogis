"""
Integration tests for the complete data processing and training pipeline.
Tests the flow from data loading through processing to training.
"""
import pytest
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import tempfile
import sys

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data-pipeline"))
sys.path.insert(0, str(PROJECT_ROOT / "ml_service"))

logger = logging.getLogger(__name__)


class TestDataCleaning:
    """Test data cleaning module."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample dataframe for testing."""
        return pd.DataFrame({
            'annee': [2020, 2021, 2022, 2023, 2024, 2025],
            'code_commune': [75056, 75056, 75056, 75056, 75056, 75056],
            'code_postal': ['75001', '75001', '75001', '75001', '75001', '75001'],
            'dep_code': ['75', '75', '75', '75', '75', '75'],
            'population': [1000, 1100, 1200, 1300, 1400, 1500],
            'prix_m2': [10000.0, 11000.0, 12000.0, 13000.0, 14000.0, 15000.0],
            'taux_global_tfb': [1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
            'dep_nom': ['Paris', 'Paris', 'Paris', 'Paris', 'Paris', 'Paris'],
        })
    
    def test_cleaner_imports(self):
        """Test that cleaner module can be imported."""
        from transform.cleaning import DataCleaner
        cleaner = DataCleaner()
        assert cleaner is not None
        assert cleaner.bad_dep_codes == ["2A", "2B"]
    
    def test_clean_drops_columns(self, sample_dataframe):
        """Test that cleaner drops specified columns."""
        from transform.cleaning import DataCleaner
        
        df = sample_dataframe.copy()
        cleaner = DataCleaner(drop_columns=['dep_nom'])
        result = cleaner.clean(df)
        
        assert 'dep_nom' not in result.columns
        assert 'annee' in result.columns
    
    def test_clean_removes_bad_dep_codes(self, sample_dataframe):
        """Test that cleaner removes rows with bad department codes."""
        from transform.cleaning import DataCleaner
        
        df = sample_dataframe.copy()
        df.loc[0, 'dep_code'] = '2A'  # Bad code
        
        cleaner = DataCleaner()
        result = cleaner.clean(df)
        
        assert len(result) < len(df)
        assert '2A' not in result['dep_code'].values
    
    def test_remove_duplicates(self, sample_dataframe):
        """Test removing duplicate rows."""
        from transform.cleaning import DataCleaner
        
        df = pd.concat([sample_dataframe, sample_dataframe.iloc[0:1]], ignore_index=True)
        assert len(df) > len(sample_dataframe)
        
        cleaner = DataCleaner()
        result = cleaner.remove_duplicates(df)
        
        assert len(result) <= len(df)
    
    def test_filter_by_year_range(self, sample_dataframe):
        """Test filtering by year range."""
        from transform.cleaning import DataCleaner
        
        cleaner = DataCleaner()
        result = cleaner.filter_by_year_range(sample_dataframe, min_year=2021, max_year=2023)
        
        assert result['annee'].min() >= 2021
        assert result['annee'].max() <= 2023


class TestDataNormalization:
    """Test data normalization module."""
    
    @pytest.fixture
    def numeric_dataframe(self):
        """Create a numeric dataframe for testing."""
        return pd.DataFrame({
            'annee': [2020, 2021, 2022, 2023, 2024, 2025],
            'population': [1000, 2000, 3000, 4000, 5000, 6000],
            'prix_m2': [10000.0, 15000.0, 20000.0, 25000.0, 30000.0, 35000.0],
            'dep_code': ['75', '75', '75', '75', '75', '75'],
            'code_postal': ['75001', '75001', '75001', '75001', '75001', '75001'],
        })
    
    def test_normalizer_imports(self):
        """Test that normalizer module can be imported."""
        from transform.normalization import DataNormalizer
        normalizer = DataNormalizer()
        assert normalizer is not None
    
    def test_normalize_creates_features(self, numeric_dataframe):
        """Test that normalization creates derived features."""
        from transform.normalization import DataNormalizer
        
        df = numeric_dataframe.copy()
        normalizer = DataNormalizer()
        result = normalizer.normalize(df)
        
        assert len(result.columns) >= len(df.columns)
        assert 'densite' in result.columns or result.shape[1] > df.shape[1]
    
    def test_encode_categorical(self, numeric_dataframe):
        """Test categorical encoding."""
        from transform.normalization import DataNormalizer
        
        df = numeric_dataframe.copy()
        normalizer = DataNormalizer()
        encoded_df, encodings = normalizer.encode_categorical(df, categorical_cols=['dep_code'])
        
        assert isinstance(encodings, dict)
        assert 'dep_code' in encodings


class TestDataProcessor:
    """Test data processor service."""
    
    @pytest.fixture
    def test_dataframe(self):
        """Create test dataframe."""
        return pd.DataFrame({
            'annee': list(range(2020, 2026)),
            'code_commune': [75056] * 6,
            'code_postal': ['75001'] * 6,
            'dep_code': ['75'] * 6,
            'population': [1000, 1100, 1200, 1300, 1400, 1500],
            'superficie_km2': [100, 100, 100, 100, 100, 100],
            'prix_m2': [10000, 11000, 12000, 13000, 14000, 15000],
            'nb_ventes': [100, 110, 120, 130, 140, 150],
            'taux_global_tfb': [1.5, 1.6, 1.7, 1.8, 1.9, 2.0],
            'taux_global_th': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        })
    
    def test_processor_imports(self):
        """Test that data processor service can be imported."""
        from app.services.data_processor_service import DataProcessorService
        processor = DataProcessorService()
        assert processor is not None
    
    def test_process_completes(self, test_dataframe):
        """Test that processing completes successfully."""
        from app.services.data_processor_service import DataProcessorService
        
        processor = DataProcessorService()
        result = processor.process(test_dataframe)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
    
    def test_validate_data(self, test_dataframe):
        """Test data validation."""
        from app.services.data_processor_service import DataProcessorService
        
        processor = DataProcessorService()
        report = processor.validate_data(test_dataframe)
        
        assert 'total_rows' in report
        assert 'total_columns' in report
        assert 'quality_score' in report
        assert 0 <= report['quality_score'] <= 100
    
    def test_create_splits(self, test_dataframe):
        """Test creating train/val/test splits."""
        from app.services.data_processor_service import DataProcessorService
        
        processor = DataProcessorService()
        train_df, val_df, test_df = processor.create_training_splits(
            test_dataframe,
            train_ratio=0.6,
            val_ratio=0.2,
            test_ratio=0.2
        )
        
        total = len(train_df) + len(val_df) + len(test_df)
        assert total == len(test_dataframe)
        assert len(train_df) > 0
        assert len(val_df) > 0
        assert len(test_df) > 0


class TestPipeline:
    """Test ML pipeline integration."""
    
    @pytest.fixture
    def pipeline_instance(self):
        """Create a pipeline instance."""
        from pipeline.pipeline import Pipeline
        return Pipeline()
    
    def test_pipeline_imports(self):
        """Test that pipeline module can be imported."""
        from pipeline.pipeline import Pipeline
        pipeline = Pipeline()
        assert pipeline is not None
    
    def test_pipeline_clean(self, pipeline_instance):
        """Test pipeline cleaning method."""
        df = pd.DataFrame({
            'annee': [2020, 2021, 2022],
            'code_commune': [75056, 75056, 75056],
            'dep_code': ['75', '75', '75'],
            'population': [1000, 1100, 1200],
            'price_m2': [10000, 11000, 12000],
            'taux_global_tfb': [1.5, 1.6, 1.7],
            'taux_global_th': [0.5, 0.5, 0.5],
            'nb_ventes': [100, 110, 120],
            'superficie_km2': [100, 100, 100],
            'dep_nom': ['Paris', 'Paris', 'Paris'],
            'reg_nom': ['Ile-de-France', 'Ile-de-France', 'Ile-de-France'],
        })
        
        result = pipeline_instance.clean(df)
        assert isinstance(result, pd.DataFrame)
        assert 'dep_nom' not in result.columns
        assert 'reg_nom' not in result.columns
    
    def test_pipeline_split(self, pipeline_instance):
        """Test pipeline split method."""
        df = pd.DataFrame({
            'annee': [2020, 2021, 2022, 2023, 2024],
            'code_commune': [75056] * 5,
            'dep_code': ['75'] * 5,
            'population': [1000, 1100, 1200, 1300, 1400],
            'y': ['hausse', 'baisse', 'stable', 'hausse', 'hausse'],
        })
        
        features = ['population']
        X_train, X_test, y_train, y_test = pipeline_instance.split(df, features)
        
        assert len(X_train) > 0
        assert len(X_test) > 0
        assert len(y_train) > 0
        assert len(y_test) > 0


class TestIntegration:
    """Integration tests for complete pipeline."""
    
    def test_end_to_end_pipeline(self):
        """Test complete pipeline from loading to processing."""
        from app.services.data_processor_service import DataProcessorService
        from pipeline.pipeline import Pipeline
        
        # Create test data
        df = pd.DataFrame({
            'annee': list(range(2020, 2026)),
            'code_commune': [75056] * 6,
            'code_postal': ['75001'] * 6,
            'dep_code': ['75'] * 6,
            'population': list(range(1000, 1600, 100)),
            'superficie_km2': [100] * 6,
            'prix_m2': list(range(10000, 16000, 1000)),
            'nb_ventes': list(range(100, 160, 10)),
            'taux_global_tfb': [1.5 + i*0.1 for i in range(6)],
            'taux_global_th': [0.5] * 6,
            'dep_nom': ['Paris'] * 6,
            'reg_nom': ['Ile-de-France'] * 6,
        })
        
        # Step 1: Process data
        processor = DataProcessorService()
        processed_df = processor.process(df, clean=True, normalize=True)
        
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) > 0
        
        # Step 2: Create splits
        train_df, val_df, test_df = processor.create_training_splits(processed_df)
        
        assert len(train_df) + len(val_df) + len(test_df) == len(processed_df)
        
        # Step 3: Clean with pipeline
        pipeline = Pipeline()
        df_copy = df.copy()
        cleaned = pipeline.clean(df_copy)
        
        assert 'dep_nom' not in cleaned.columns
        assert len(cleaned) > 0
    
    def test_data_quality_workflow(self):
        """Test data quality validation workflow."""
        from app.services.data_processor_service import DataProcessorService
        
        # Create data with some quality issues
        df = pd.DataFrame({
            'annee': [2020, 2021, None, 2023, 2024],
            'code_commune': [75056, 75056, 75056, 75056, 75056],
            'population': [1000, np.nan, 1200, 1300, 1400],
            'prix_m2': [10000, 11000, 12000, 13000, 14000],
        })
        
        processor = DataProcessorService()
        report = processor.validate_data(df)
        
        assert 'total_rows' in report
        assert 'missing_values' in report
        assert report['total_missing'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
