from django.urls import path
from .views import get_predictions, predict_api, predict

urlpatterns = [
    # Route pour la vue web de prédiction
    path('', predict, name='prediction'),
    
    # Route pour l'API de prédiction
    path('api/', predict_api, name='api_predict'),
    
    # Route pour l'historique
    path('history/', get_predictions, name='prediction_history'),
]