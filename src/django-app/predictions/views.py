from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Prediction
import folium 
import requests
from django.shortcuts import render
from django.urls import reverse

import os
import sys
import joblib
import pandas as pd

# Permet d'importer le pipeline depuis le dossier data-pipeline
DATA_PIPELINE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data-pipeline'))
if DATA_PIPELINE_ROOT not in sys.path:
    sys.path.append(DATA_PIPELINE_ROOT)

MODEL_FILE = os.path.join(DATA_PIPELINE_ROOT, 'pipeline', 'pipeline_model.joblib')
_pipeline_model = None

def interpret_prediction(result):
    """Convertit le résultat numérique du modèle en texte compréhensible"""
    if isinstance(result, str) and result.startswith("Erreur"):
        return result
    
    # Le modèle retourne une liste, prendre le premier élément
    if isinstance(result, list) and len(result) > 0:
        prediction_num = result[0]
    else:
        prediction_num = result
    
    # Mapping des valeurs numériques aux catégories
    mapping = {
        0: "📉 Baisse - Prix en diminution",
        1: "➡️ Stable - Prix stables", 
        2: "📈 Hausse - Prix en augmentation"
    }
    
    return mapping.get(prediction_num, f"Résultat inconnu: {prediction_num}")

def get_pipeline():
    global _pipeline_model
    if _pipeline_model is not None:
        return _pipeline_model

    if os.path.exists(MODEL_FILE):
        _pipeline_model = joblib.load(MODEL_FILE)
        return _pipeline_model

    raise RuntimeError('Modèle introuvable, entraînez-le d\'abord avec train.py')


def run_prediction(payload):
    """Run the shared prediction pipeline logic."""
    pipeline = get_pipeline()
    df = pd.DataFrame([payload])
    df = pipeline.clean(df)

    features = [
        'taux_inflation', 'evolution_ventes', 'evolution_taxe', 'taxe_vs_moyenne_dep',
        'ventes_moyennes_dep', 'densite', 'ratio_taxe', 'ventes_par_habitant',
        'taxe_x_population', 'annee', 'dep_code', 'reg_code', 'code_postal',
        'population', 'superficie_km2', 'zone_emploi', 'taux_global_tfb',
        'taux_global_tfnb', 'taux_plein_teom', 'taux_global_th', 'nb_ventes'
    ]

    missing = [c for c in features if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes: {missing}")

    X = df[features]
    y_pred = pipeline.predict(X)
    return y_pred.tolist() if hasattr(y_pred, 'tolist') else [int(y_pred)]


@api_view(['POST'])
def predict_api(request):
    """Endpoint API POST pour prédiction via data-pipeline/Pipeline"""
    payload = request.data

    # Exemple de payload attendu (clé = nom des features) :
    # {
    #   "taux_inflation": 1.2,
    #   "annee": 2024,
    #   "population": 10000,
    #   ...
    # }

    try:
        result = run_prediction(payload)
    except ValueError as e:
        return Response({'error': str(e)}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

    return Response({'prediction': result})


@api_view(["GET", "POST"]) 
def predict(request):
    prediction = None
    map_html = None
    nom_commune = "Zone non définie"

    if request.method == "POST":
        
        data = request.data
        zipcode = request.data.get("zipcode")
        
        
        
        
        
        geo_url = f"https://geo.api.gouv.fr/communes?codePostal={zipcode}&fields=nom,centre,contour,population&format=json&geometry=contour"
        
        try:
            geo_response = requests.get(geo_url)
            geo_data = geo_response.json()

            if geo_data:
                commune = geo_data[0]
                nom_commune = commune.get('nom')
                pop_auto = commune.get('population', 0)
                lon, lat = commune['centre']['coordinates']
                
                prediction_data = {
                    'dep_code': zipcode[:2],  # Extraire le département du code postal
                    'reg_code': '11',  # Région par défaut (Île-de-France pour Paris)
                    'code_postal': zipcode,
                    'taux_inflation': 2.5,  # Valeur par défaut
                    'annee': 2024,
                    'population': pop_auto,
                    'superficie_km2': 50.0,  # Valeur par défaut
                    'zone_emploi': 1,
                    'taux_global_tfb': 25.0,  # Valeur par défaut
                    'taux_global_tfnb': 15.0,  # Valeur par défaut
                    'taux_plein_teom': 8.0,  # Valeur par défaut
                    'taux_global_th': 12.0,  # Valeur par défaut
                    'nb_ventes': 1000,  # Valeur par défaut
                    'densite': pop_auto / 50.0,  # Calcul simple
                    'ratio_taxe': 2.1,  # Valeur par défaut
                    'ventes_par_habitant': 1000 / (pop_auto + 1),
                    'taxe_x_population': 25.0 * (pop_auto + 1),
                    'evolution_ventes': 0.05,  # Valeur par défaut
                    'evolution_taxe': 0.03,  # Valeur par défaut
                    'taxe_vs_moyenne_dep': 1.1,  # Valeur par défaut
                    'ventes_moyennes_dep': 800  # Valeur par défaut
                }

                try:
                    api_url = request.build_absolute_uri(reverse('api_predict'))
                    api_response = requests.post(api_url, json=prediction_data, timeout=10)
                    api_response.raise_for_status()
                    api_data = api_response.json()
                    result = api_data.get('prediction')
                except requests.exceptions.RequestException as e:
                    result = f"Erreur API prédiction: {str(e)}"
                except ValueError as e:
                    result = f"Erreur lecture réponse API: {str(e)}"

                # Convertir le résultat numérique en texte compréhensible
                prediction_text = interpret_prediction(result)
                
                m = folium.Map(location=[lat, lon], zoom_start=12, tiles="OpenStreetMap")

                
                if 'contour' in commune:
                    folium.GeoJson(
                        commune['contour'],
                        style_function=lambda x: {
                            'fillColor': '#8CA5A5', 
                            'color': '#7A5B3E', 
                            'weight': 2, 
                            'fillOpacity': 0.3
                        }
                    ).add_to(m)

                
                folium.Marker(
                    [lat, lon], 
                    popup=f"Analyse : {nom_commune}",
                    icon=folium.Icon(color='red', icon='home')
                ).add_to(m)

                
                map_html = m._repr_html_()

                prediction = {
                    "result": result,
                    "result_text": prediction_text,
                    "population": pop_auto,
                    "nom": nom_commune
                }

        except Exception as e:
            print(f"Erreur API Géo/Folium: {e}")

       

    
    return render(request, "prediction/prediction.html", {
        "prediction": prediction,
        "map_html": map_html,
        "nom_commune": nom_commune
    })

@api_view(["GET"])
def get_predictions(request):
    """Vue pour l'historique (utilisée par ton URLconf)"""
    predictions = Prediction.objects.all().order_by('-id').values()
    return Response(list(predictions))        