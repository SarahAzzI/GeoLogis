import logging
import pandas as pd
from typing import Optional, Tuple
import importlib.util
from pathlib import Path

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for making predictions using the trained model."""
    
    def __init__(self):
        self.model: Optional[object] = None
        self.label_encoder = None
        self.is_trained = False
        self.accuracy = None
        self.training_samples = 0
    
    def _load_pipeline_module(self):
        """Dynamically load the Pipeline class from pipeline.py."""
        try:
            # Path calculation: 
            # __file__ = .../src/ml_service/app/services/prediction_service.py
            # parent (services) -> parent (app) -> parent (ml_service) -> parent (src) -> parent (GeoLogis)
            # Then navigate to src/data-pipeline/pipeline/pipeline.py
            base_path = Path(__file__).parent.parent.parent.parent.parent
            pipeline_path = base_path / "src" / "data-pipeline" / "pipeline" / "pipeline.py"
            
            logger.info(f"Loading pipeline module from: {pipeline_path}")
            if not pipeline_path.exists():
                logger.error(f"Pipeline module not found at {pipeline_path}")
                return None
            
            spec = importlib.util.spec_from_file_location("pipeline_module", pipeline_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info("Pipeline module loaded successfully")
            return module.Pipeline
        except Exception as e:
            logger.error(f"Error loading pipeline module: {e}", exc_info=True)
            return None
    
    def load_training_data_from_csv(self) -> Optional[pd.DataFrame]:
        """Load training data from CSV file."""
        try:
            # Path calculation:
            # __file__ = .../src/ml_service/app/services/prediction_service.py
            # parent (services) -> parent (app) -> parent (ml_service) -> parent (src) -> parent (GeoLogis)
            # Then navigate to src/data-pipeline/merge/raw/csv_full_post.csv
            base_path = Path(__file__).parent.parent.parent.parent.parent
            csv_path = base_path / "src" / "data-pipeline" / "merge" / "raw" / "csv_full_post.csv"
            
            logger.info(f"Loading training data from {csv_path}")
            if not csv_path.exists():
                logger.warning(f"CSV file not found at {csv_path}")
                return None
            
            logger.info(f"Loading training data from {csv_path}...")
            df = pd.read_csv(str(csv_path), sep=";")
            logger.info(f"Loaded {len(df)} rows from CSV")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading training data from CSV: {e}", exc_info=True)
            return None
    
    def load_training_data_from_db(self, db: Session) -> Optional[pd.DataFrame]:
        """Load and merge training data from database repositories."""
        try:
            from ..repositories.taxe_fonciere_repository import TaxeFonciereRepository
            
            logger.info("Loading training data from database...")
            
            # Initialize repository
            taxe_repo = TaxeFonciereRepository(db=db)
            
            # Try to load from taxe_fonciere table
            from ..model.taxe_fonciere import TaxeFonciere
            taxe_records = db.query(TaxeFonciere).all()
            
            if not taxe_records:
                logger.warning("No taxe foncière records found in database")
                return None
            
            logger.info(f"Loaded {len(taxe_records)} taxe foncière records from database")
            return None  # Will fall back to CSV
            
        except Exception as e:
            logger.error(f"Error loading training data from database: {e}", exc_info=True)
            return None
    
    def train(self, db: Session) -> Tuple[bool, str]:
        """Train the model using data from CSV."""
        try:
            # Load the Pipeline class
            Pipeline = self._load_pipeline_module()
            if Pipeline is None:
                return False, "Pipeline module could not be loaded"
            
            # Try loading from CSV first
            df = self.load_training_data_from_csv()
            
            # Fallback to database if CSV not available
            if df is None:
                df = self.load_training_data_from_db(db)
            
            if df is None or len(df) == 0:
                msg = "No training data available"
                logger.warning(msg)
                return False, msg
            
            logger.info(f"Starting model training with {len(df)} samples...")
            
            # Initialize pipeline
            self.model = Pipeline(
                target_col="y",
                drop_cols=["dep_nom", "reg_nom", "variation"],
                bad_dep_codes=["2A", "2B"],
                selected_k=5,
            )
            
            # Clean data
            df_clean = self.model.clean(df)
            self.training_samples = len(df_clean)
            
            if len(df_clean) == 0:
                msg = "No data after cleaning"
                logger.warning(msg)
                return False, msg
            
            logger.info(f"Data after cleaning: {len(df_clean)} samples")
            
            # Define features
            features = [
                "evolution_ventes", "evolution_taxe", "taxe_vs_moyenne_dep",
                "ventes_moyennes_dep", "densite", "ratio_taxe", "ventes_par_habitant",
                "taxe_x_population", "annee", "dep_code", "reg_code", "code_postal",
                "population", "superficie_km2", "zone_emploi",
                "taux_global_tfb", "taux_global_tfnb", "taux_plein_teom",
                "taux_global_th", "nb_ventes",
            ]
            
            # Split data
            X_train, X_test, y_train, y_test = self.model.split(df_clean, features)
            
            logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")
            
            # Train
            self.model.train(X_train, y_train)
            self.label_encoder = self.model.label_encoder
            
            # Evaluate
            result = self.model.evaluate(X_test, y_test)
            self.accuracy = result["accuracy"]
            self.is_trained = True
            
            msg = f"Model trained successfully. Accuracy: {self.accuracy:.4f}"
            logger.info(msg)
            return True, msg
            
        except Exception as e:
            msg = f"Error training model: {e}"
            logger.error(msg, exc_info=True)
            return False, msg
    
    def predict(self, input_data: dict) -> Optional[dict]:
        """Make a prediction on the input data."""
        if not self.is_trained or self.model is None:
            logger.error("Model is not trained. Train the model first.")
            return None
        
        try:
            # Convert input to DataFrame
            df = pd.DataFrame([input_data])
            
            # Make prediction
            prediction = self.model.predict(df)
            prediction_label = self.label_encoder.inverse_transform(prediction)[0]
            
            return {
                "prediction": prediction_label,
                "confidence": None,  # Not easily available from sklearn models
                "features_used": len(df.columns),
                "probabilities": None
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}", exc_info=True)
            return None
    
    def predict_2026(self, db: Session) -> Optional[dict]:
        """Make bulk predictions for all communes for year 2026."""
        if not self.is_trained or self.model is None:
            logger.error("Model is not trained. Train the model first.")
            return None
        
        try:
            # Load data from CSV (2024 data to use as baseline for 2026)
            df = self.load_training_data_from_csv()
            
            if df is None or len(df) == 0:
                logger.warning("No training data available for 2026 predictions")
                return None
            
            logger.info(f"Available columns: {list(df.columns)}")
            logger.info(f"Making 2026 predictions for {len(df)} records...")
            
            # Get the latest year's data (usually 2024)
            latest_year = df["annee"].max()
            df_latest = df[df["annee"] == latest_year].copy()
            logger.info(f"Using {latest_year} data as baseline for 2026 predictions ({len(df_latest)} records)")
            
            # Update year to 2026
            df_predict = df_latest.copy()
            df_predict["annee"] = 2026
            
            # Define features
            features = [
                "evolution_ventes", "evolution_taxe", "taxe_vs_moyenne_dep",
                "ventes_moyennes_dep", "densite", "ratio_taxe", "ventes_par_habitant",
                "taxe_x_population", "annee", "dep_code", "reg_code", "code_postal",
                "population", "superficie_km2", "zone_emploi",
                "taux_global_tfb", "taux_global_tfnb", "taux_plein_teom",
                "taux_global_th", "nb_ventes",
            ]
            
            # Filter to available features only
            available_features = [f for f in features if f in df_predict.columns]
            logger.info(f"Using {len(available_features)} features for prediction")
            
            X_predict = df_predict[available_features]
            
            # Make predictions
            predictions = self.model.predict(X_predict)
            prediction_labels = self.label_encoder.inverse_transform(predictions)
            
            # Build results
            results = []
            hausse_count = 0
            baisse_count = 0
            stable_count = 0
            
            for idx, row in df_predict.iterrows():
                pred_label = prediction_labels[idx]
                
                if pred_label == "hausse":
                    hausse_count += 1
                elif pred_label == "baisse":
                    baisse_count += 1
                else:
                    stable_count += 1
                
                results.append({
                    "code_commune": idx,  # Use index as commune identifier
                    "code_insee": str(int(row.get("code_postal", "0"))),
                    "commune_name": f"Postal Code {int(row.get('code_postal', 0))}",
                    "dep_code": str(row.get("dep_code", "")),
                    "prediction": pred_label,
                    "population": int(row.get("population", 0)) if pd.notna(row.get("population")) else None,
                    "taux_global_tfb": float(row.get("taux_global_tfb", 0)) if pd.notna(row.get("taux_global_tfb")) else None,
                })
            
            logger.info(f"2026 Predictions: {hausse_count} hausse, {baisse_count} baisse, {stable_count} stable")
            
            return {
                "year": 2026,
                "total_predictions": len(results),
                "predictions": results,
                "hausse_count": hausse_count,
                "baisse_count": baisse_count,
                "stable_count": stable_count,
            }
            
        except Exception as e:
            logger.error(f"Error making 2026 predictions: {e}", exc_info=True)
            return None
    
    def get_predictions_by_postal_code(self, postal_code: str, db: Session) -> Optional[dict]:
        """Get 2026 predictions filtered by postal code."""
        if not self.is_trained or self.model is None:
            logger.error("Model is not trained. Train the model first.")
            return None
        
        try:
            # Load data from CSV
            df = self.load_training_data_from_csv()
            
            if df is None or len(df) == 0:
                logger.warning("No training data available")
                return None
            
            logger.info(f"Filtering predictions for postal code: {postal_code}")
            
            # Get the latest year's data
            latest_year = df["annee"].max()
            df_latest = df[df["annee"] == latest_year].copy()
            
            # Filter by postal code
            # Handle both float and string postal codes
            try:
                postal_code_int = int(float(postal_code))
                df_postal = df_latest[df_latest["code_postal"].astype(float).astype(int) == postal_code_int].copy()
            except (ValueError, TypeError):
                # If conversion fails, try string comparison
                df_postal = df_latest[df_latest["code_postal"].astype(str).str.strip() == str(postal_code).strip()].copy()
            
            if len(df_postal) == 0:
                logger.warning(f"No data found for postal code: {postal_code}")
                return {
                    "postal_code": postal_code,
                    "predicted_trend": "N/A",
                    "total_records": 0,
                    "records": [],
                    "hausse_count": 0,
                    "baisse_count": 0,
                    "stable_count": 0,
                    "year": 2026,
                }
            
            logger.info(f"Found {len(df_postal)} records for postal code {postal_code}")
            
            # Update year to 2026
            df_postal["annee"] = 2026
            
            # Define features
            features = [
                "evolution_ventes", "evolution_taxe", "taxe_vs_moyenne_dep",
                "ventes_moyennes_dep", "densite", "ratio_taxe", "ventes_par_habitant",
                "taxe_x_population", "annee", "dep_code", "reg_code", "code_postal",
                "population", "superficie_km2", "zone_emploi",
                "taux_global_tfb", "taux_global_tfnb", "taux_plein_teom",
                "taux_global_th", "nb_ventes",
            ]
            
            # Filter to available features
            available_features = [f for f in features if f in df_postal.columns]
            X_postal = df_postal[available_features]
            
            # Make predictions
            predictions = self.model.predict(X_postal)
            prediction_labels = self.label_encoder.inverse_transform(predictions)
            
            # Build results
            results = []
            hausse_count = 0
            baisse_count = 0
            stable_count = 0
            trend_counts = {"hausse": 0, "baisse": 0, "stable": 0}
            
            for pred_idx, (_, row) in enumerate(df_postal.iterrows()):
                pred_label = prediction_labels[pred_idx]
                
                if pred_label == "hausse":
                    hausse_count += 1
                elif pred_label == "baisse":
                    baisse_count += 1
                else:
                    stable_count += 1
                
                trend_counts[pred_label] = trend_counts.get(pred_label, 0) + 1
                
                results.append({
                    "code_commune": pred_idx,
                    "code_insee": str(postal_code),
                    "commune_name": f"Postal Code {postal_code}",
                    "dep_code": str(row.get("dep_code", "")),
                    "prediction": pred_label,
                    "population": int(row.get("population", 0)) if pd.notna(row.get("population")) else None,
                    "taux_global_tfb": float(row.get("taux_global_tfb", 0)) if pd.notna(row.get("taux_global_tfb")) else None,
                })
            
            # Determine dominant trend
            dominant_trend = max(trend_counts, key=trend_counts.get)
            
            logger.info(f"Postal code {postal_code} - Hausse: {hausse_count}, Baisse: {baisse_count}, Stable: {stable_count}")
            
            return {
                "postal_code": postal_code,
                "predicted_trend": dominant_trend,
                "total_records": len(results),
                "records": results,
                "hausse_count": hausse_count,
                "baisse_count": baisse_count,
                "stable_count": stable_count,
                "year": 2026,
            }
            
        except Exception as e:
            logger.error(f"Error getting predictions for postal code {postal_code}: {e}", exc_info=True)
            return None


# Global prediction service instance
_prediction_service: Optional[PredictionService] = None


def get_prediction_service() -> PredictionService:
    """Get or create the global prediction service instance."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
