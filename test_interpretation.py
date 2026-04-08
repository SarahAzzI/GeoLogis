#!/usr/bin/env python3
"""
Test de l'interprétation des prédictions
"""
import sys
import os

# Ajouter le chemin Django
sys.path.append('/home/lohan/Bureau/DEV_IA/Brief_API/GeoLogis/src/django-app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from predictions.views import interpret_prediction

def test_interpretation():
    """Test de la fonction d'interprétation"""
    print("🧪 Test de l'interprétation des prédictions\n")

    test_cases = [
        ([0], "📉 Baisse - Prix en diminution"),
        ([1], "➡️ Stable - Prix stables"),
        ([2], "📈 Hausse - Prix en augmentation"),
        (0, "📉 Baisse - Prix en diminution"),
        (1, "➡️ Stable - Prix stables"),
        (2, "📈 Hausse - Prix en augmentation"),
        ("Erreur test", "Erreur test"),
        ([], "Résultat inconnu: []"),
        (3, "Résultat inconnu: 3")
    ]

    for input_val, expected in test_cases:
        result = interpret_prediction(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} {input_val} -> {result}")
        if result != expected:
            print(f"   Attendu: {expected}")

if __name__ == "__main__":
    test_interpretation()