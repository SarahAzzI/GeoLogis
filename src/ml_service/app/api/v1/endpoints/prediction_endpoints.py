from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from ....model.database import get_db
from ....schemas.prediction_schema import (
    PredictionInputSchema,
    PredictionOutputSchema,
    ModelStatusSchema,
    Predictions2026ResultSchema,
    PostalCodePredictionSchema,
)
from ....services.prediction_service import get_prediction_service, PredictionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/train", response_model=ModelStatusSchema)
async def train_model(db: Session = Depends(get_db)):
    """
    Train the machine learning model using data from the database.
    
    This endpoint loads real estate market data, communes data, and inflation data
    from the database, cleans it, and trains the XGBoost classification model
    to predict price trends (hausse, baisse, stable).
    """
    service = get_prediction_service()
    success, message = service.train(db)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "is_trained": service.is_trained,
        "accuracy": service.accuracy,
        "total_training_samples": service.training_samples,
        "message": message,
    }


@router.get("/status", response_model=ModelStatusSchema)
async def get_model_status():
    """
    Get the current status of the model.
    
    Returns whether the model is trained, its accuracy, and number of training samples.
    """
    service = get_prediction_service()
    
    return {
        "is_trained": service.is_trained,
        "accuracy": service.accuracy,
        "total_training_samples": service.training_samples,
        "message": "Model is trained" if service.is_trained else "Model is not trained",
    }


@router.post("/predict", response_model=PredictionOutputSchema)
async def make_prediction(input_data: PredictionInputSchema):
    """
    Make a prediction on the provided features.
    
    Requires:
    - The model must be trained first (call /predictions/train endpoint)
    - All required features must be provided in the request
    
    Returns:
    - prediction: One of "hausse" (price increase), "baisse" (price decrease), or "stable" (no change)
    - features_used: Number of features processed
    """
    service = get_prediction_service()
    
    if not service.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Model is not trained. Please call /predictions/train first."
        )
    
    # Convert input schema to dictionary
    input_dict = input_data.model_dump()
    
    # Make prediction
    result = service.predict(input_dict)
    
    if result is None:
        raise HTTPException(status_code=500, detail="Error making prediction")
    
    return result


@router.post("/retrain", response_model=ModelStatusSchema)
async def retrain_model(db: Session = Depends(get_db)):
    """
    Retrain the model with fresh data from the database.
    
    Same as /train endpoint but explicitly indicates retraining of an existing model.
    """
    service = get_prediction_service()
    success, message = service.train(db)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "is_trained": service.is_trained,
        "accuracy": service.accuracy,
        "total_training_samples": service.training_samples,
        "message": message,
    }


@router.get("/2026", response_model=Predictions2026ResultSchema)
async def get_2026_predictions(db: Session = Depends(get_db)):
    """
    Get price trend predictions for all communes for year 2026.
    
    This endpoint:
    1. Uses the 2024 baseline data from the training dataset
    2. Applies the trained model to predict 2026 trends
    3. Returns predictions for all communes grouped by prediction class
    
    Returns:
    - predictions: List of all commune predictions with details
    - hausse_count: Number of communes predicted to have price increases
    - baisse_count: Number of communes predicted to have price decreases
    - stable_count: Number of communes predicted to be stable
    
    Requires:
    - Model must be trained first (call /predictions/train endpoint)
    """
    service = get_prediction_service()
    
    if not service.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Model is not trained. Please call /predictions/train first."
        )
    
    # Make 2026 predictions
    result = service.predict_2026(db)
    
    if result is None:
        raise HTTPException(status_code=500, detail="Error making 2026 predictions")
    
    return result


@router.get("/2026/postal/{postal_code}", response_model=PostalCodePredictionSchema)
async def get_predictions_by_postal_code(postal_code: str, db: Session = Depends(get_db)):
    """
    Get price trend predictions for a specific postal code for year 2026.
    
    This endpoint:
    1. Filters the 2024 baseline data by postal code
    2. Projects this data forward to 2026
    3. Applies the trained model to predict trends
    4. Returns the dominant trend and individual predictions
    
    Parameters:
    - postal_code: The postal code to filter by (e.g., "75001", "69001")
    
    Returns:
    - predicted_trend: Dominant trend for this postal code (hausse, baisse, or stable)
    - records: List of all predictions for this postal code
    - hausse_count: Number of records predicted to have price increases
    - baisse_count: Number of records predicted to have price decreases
    - stable_count: Number of records predicted to be stable
    
    Requires:
    - Model must be trained first (call /predictions/train endpoint)
    """
    service = get_prediction_service()
    
    if not service.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Model is not trained. Please call /predictions/train first."
        )
    
    # Get predictions for given postal code
    result = service.get_predictions_by_postal_code(postal_code, db)
    
    if result is None:
        raise HTTPException(status_code=500, detail=f"Error getting predictions for postal code {postal_code}")
    
    return result
