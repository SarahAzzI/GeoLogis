# GeoLogis : Plateforme d'Analyse et de Prédiction Immobilière

**GeoLogis** est une solution de traitement de données et de prédiction pour le marché immobilier. Le projet combine un pipeline de données, un service de Machine Learning (ML) basé sur FastAPI et une interface utilisateur moderne développée avec Django et Tailwind CSS. Il permet d'extraire des données géographiques, de les transformer et de fournir des prédictions précises sur les tendances du marché.

## 🏗️ Architecture du Projet

L'architecture de GeoLogis est divisée en trois composants principaux, chacun ayant une responsabilité spécifique dans le cycle de vie des données :

| Composant | Technologie | Description |
| :--- | :--- | :--- |
| **Data Pipeline** | Python, Pandas, Scikit-learn | Extraction, transformation et nettoyage des données immobilières. |
| **ML Service** | FastAPI, SQLAlchemy | API REST fournissant des endpoints pour l'entraînement des modèles et les prédictions. |
| **Django App** | Django, Tailwind CSS | Interface web permettant aux utilisateurs de visualiser les données et d'interagir avec les modèles. |

## 🚀 Fonctionnalités Clés

*   **Extraction de Données Géographiques** : Scripts dédiés à la récupération de données depuis l'API pour enrichir les analyses immobilières.
*   **Pipeline de Machine Learning** : Système automatisé pour le prétraitement des données, l'entraînement de modèles et la sauvegarde des modèles entraînés.
*   **Service de Prédiction API** : Une API FastAPI performante offrant des endpoints pour :
    *   L'estimation de la taxe foncière.
    *   La prédiction des états immobiliers.
    *   L'analyse des taux d'inflation et des données communales.
*   **Interface Utilisateur Intuitive** : Dashboard Django intégrant des cartes interactives et des formulaires de prédiction.

## 📁 Structure du Dépôt

```text
GeoLogis/
├── src/
│   ├── data-pipeline/    # Scripts d'ETL et notebooks d'expérimentation
│   ├── django-app/       # Application web principale (Django)
│   └── ml_service/       # API de Machine Learning (FastAPI)
├── static/               # Fichiers statiques et ressources géographiques
├── flatfiles/            # Stockage des données brutes
├── requirements.txt      # Dépendances globales du projet
└── geologis.db           # Base de données SQLite pour le développement
```

## 🛠️ Installation et Configuration

1.  **Cloner le dépôt** :
    ```bash
    git clone https://github.com/FatimaUY/GeoLogis.git
    cd GeoLogis
    ```

2.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

3.  **Lancer le service ML (FastAPI)** :
    ```bash
    cd src/ml_service
    uvicorn app.main:app --reload
    ```

4.  **Lancer l'application web (Django)** :
    ```bash
    cd src/django-app
    python manage.py migrate
    python manage.py runserver
    ```

## 👥 Contributeurs

Ce projet a été développé par une équipe dédiée :
*   **Fatima**
*   **Hazel**
*   **Sarah**
*   **Lohan**

---
