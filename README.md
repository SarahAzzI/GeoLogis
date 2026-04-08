# GeoLogis: Real Estate Analysis and Prediction Platform

**GeoLogis** is a data processing and prediction solution for the real estate market. The project combines a robust data pipeline, a Machine Learning (ML) service based on FastAPI, and a modern user interface developed with Django and Tailwind CSS. It enables the extraction of data, its transformation, and the provision of accurate predictions on property values and market trends.

## 🏗️ Project Architecture

The GeoLogis architecture is divided into three main components, each with a specific responsibility in the data lifecycle:

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Data Pipeline** | Python, Pandas, Scikit-learn | Data extraction, transformation, cleaning, and model training. |
| **ML Service** | FastAPI, SQLAlchemy | REST API providing endpoints for model interaction. |
| **Django App** | Django, Tailwind CSS | Web interface allowing users to visualize data and interact with the models. |

## 🚀 Key Features

*   **Geographic Data Extraction**: Dedicated scripts for retrieving data from the OpenStreetMap API to enrich real estate analyses.
*   **Machine Learning Pipeline**: An automated system for data preprocessing, model training (XGBoost, Scikit-learn), and saving trained models.
*   **Prediction API Service**: A high-performance FastAPI offering endpoints for:
    *   Property tax estimation.
    *   Prediction of real estate market conditions (whether the market is stable, increasing, or decreasing).
    *   Analysis of inflation rates and communal data.
*   **Intuitive User Interface**: A Django dashboard integrating interactive maps and prediction forms.

## 📁 Repository Structure

```text
GeoLogis/
├── src/
│   ├── data-pipeline/    # ETL scripts and experimentation notebooks
│   ├── django-app/       # Main web application (Django)
│   └── ml_service/       # Machine Learning API (FastAPI)
├── static/               # Static files and geographic resources
├── flatfiles/            # Storage for raw and processed data
├── requirements.txt      # Global project dependencies
```

## 🛠️ Installation and Configuration

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/FatimaUY/GeoLogis.git
    cd GeoLogis
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch the ML service (FastAPI)**:
    ```bash
    cd src/ml_service
    uvicorn app.main:app --reload
    ```

4.  **Launch the web application (Django)**:
    ```bash
    cd src/django-app
    python manage.py migrate
    python manage.py runserver
    ```

## 🧪 Testing

The project uses `pytest` to ensure code quality.


## 👥 Contributors

This project was developed by a dedicated team:
*   **Fatima**
*   **Hazel**
*   **Sarah**
*   **Lohan**
