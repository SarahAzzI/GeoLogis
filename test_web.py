#!/usr/bin/env python3
"""
Test rapide de l'interface web pour vérifier l'affichage des prédictions
"""
import requests
from bs4 import BeautifulSoup

def test_web_interface():
    """Test de l'interface web avec simulation de formulaire"""
    print("🧪 Test de l'interface web avec prédiction...")

    # URL de l'interface
    url = 'http://127.0.0.1:8005/predictions/'

    # Données du formulaire
    data = {'zipcode': '75001'}

    try:
        # Faire la requête POST
        response = requests.post(url, data=data, allow_redirects=True)

        if response.status_code == 200:
            print("✅ Page chargée avec succès")

            # Parser le HTML pour chercher le résultat
            soup = BeautifulSoup(response.text, 'html.parser')

            # Chercher les éléments qui contiennent le résultat
            prediction_div = soup.find('div', class_='animate-fade-in')
            if prediction_div:
                print("📊 Section de prédiction trouvée !")

                # Chercher le résultat spécifique
                result_div = prediction_div.find('div', class_='text-3xl')
                if result_div:
                    result_text = result_div.get_text().strip()
                    print(f"🎯 Résultat affiché : {result_text}")
                    return True
                else:
                    print("⚠️ Section de prédiction trouvée mais pas le résultat")
                    print("Contenu de la section :", prediction_div.get_text()[:200])
            else:
                print("❌ Aucune section de prédiction trouvée")
                print("Recherche d'autres indices de prédiction...")

                # Chercher n'importe quel texte contenant "prediction" ou "result"
                if 'prediction' in response.text.lower():
                    print("📝 Mot 'prediction' trouvé dans la page")
                if 'result' in response.text.lower():
                    print("📝 Mot 'result' trouvé dans la page")

        else:
            print(f"❌ Erreur HTTP: {response.status_code}")

    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

    return False

if __name__ == "__main__":
    print("🚀 Test de l'affichage des prédictions\n")

    success = test_web_interface()

    if success:
        print("\n🎉 SUCCÈS ! Le résultat de prédiction s'affiche maintenant !")
        print("🌐 Ouvrez http://127.0.0.1:8005/predictions/ dans votre navigateur")
        print("📝 Entrez un code postal (ex: 75001) et cliquez sur 'Lancer la recherche'")
    else:
        print("\n⚠️ Problème détecté - Vérifiez les logs du serveur")