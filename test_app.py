#!/usr/bin/env python3
"""
Script de test pour vérifier que les prédictions par code postal fonctionnent
"""
import requests
import json

def test_api():
    """Test de l'API REST"""
    print("🧪 Test de l'API REST...")

    # Données de test complètes
    test_data = {
        'dep_code': '75',
        'reg_code': '11',
        'code_postal': '75001',
        'taux_inflation': 2.5,
        'annee': 2024,
        'population': 2000000,
        'superficie_km2': 105.4,
        'zone_emploi': 1,
        'taux_global_tfb': 25.5,
        'taux_global_tfnb': 15.2,
        'taux_plein_teom': 8.3,
        'taux_global_th': 12.1,
        'nb_ventes': 15000,
        'densite': 18980.0,
        'ratio_taxe': 2.1,
        'ventes_par_habitant': 0.0075,
        'taxe_x_population': 51000000.0,
        'evolution_ventes': 0.05,
        'evolution_taxe': 0.03,
        'taxe_vs_moyenne_dep': 1.1,
        'ventes_moyennes_dep': 12000
    }

    try:
        response = requests.post(
            'http://127.0.0.1:8005/api/predictions/api/',
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            print("✅ API REST fonctionne !")
            print("📊 Prédiction:", response.json())
            return True
        else:
            print("❌ Erreur API:", response.status_code, response.text)
            return False

    except Exception as e:
        print("❌ Erreur de connexion API:", e)
        return False

def test_web_interface():
    """Test de l'interface web"""
    print("\n🌐 Test de l'interface web...")

    try:
        response = requests.get('http://127.0.0.1:8005/predictions/', timeout=10)

        if response.status_code == 200:
            print("✅ Interface web accessible !")
            print("📍 URL: http://127.0.0.1:8005/predictions/")
            return True
        else:
            print("❌ Erreur interface web:", response.status_code)
            return False

    except Exception as e:
        print("❌ Erreur de connexion web:", e)
        return False

if __name__ == "__main__":
    print("🚀 Test de l'application GeoLogis\n")

    api_ok = test_api()
    web_ok = test_web_interface()

    print("\n" + "="*50)
    if api_ok and web_ok:
        print("🎉 TOUT FONCTIONNE !")
        print("📱 Interface web: http://127.0.0.1:8005/predictions/")
        print("🔧 API REST: http://127.0.0.1:8005/api/predictions/api/")
        print("\n💡 Pour tester les prédictions par code postal:")
        print("   1. Ouvrez l'URL ci-dessus dans votre navigateur")
        print("   2. Entrez un code postal français (ex: 75001)")
        print("   3. Cliquez sur 'Analyser' pour voir la prédiction ML")
    else:
        print("⚠️  Problèmes détectés - Vérifiez les logs du serveur")
    print("="*50)