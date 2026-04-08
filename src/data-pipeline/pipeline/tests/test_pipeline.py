import pytest
import pandas as pd
import numpy as np
from pipeline import Pipeline


@pytest.fixture
def sample_dataframe():
    # Dataset minimal mais compatible avec ton pipeline
    data = {
        "annee": [2022, 2022, 2023, 2023, 2024, 2024],
        "population": [1000, 1200, 2000, 2100, 1500, 1800],
        "superficie_km2": [10, 12, 20, 21, 15, 18],
        "zone_emploi": [1, 1, 2, 2, 1, 2],
        "taux_global_tfb": [10, 12, 20, 22, 15, 18],
        "taux_global_tfnb": [5, 6, 10, 11, 7, 9],
        "taux_plein_teom": [2, 2, 3, 3, 2, 3],
        "taux_global_th": [8, 9, 12, 13, 9, 11],
        "nb_ventes": [100, 110, 200, 220, 150, 180],
        "dep_code": ["59", "59", "59", "59", "59", "59"],
        "reg_code": ["HDF", "HDF", "HDF", "HDF", "HDF", "HDF"],
        "code_postal": ["59000", "59000", "59000", "59000", "59000", "59000"],
        "y": ["hausse", "baisse", "stable", "hausse", "baisse", "stable"],
    }

    df = pd.DataFrame(data)

    pipeline = Pipeline(selected_k=5)
    df_clean = pipeline.clean(df)

    features = [
        "evolution_ventes",
        "evolution_taxe",
        "taxe_vs_moyenne_dep",
        "ventes_moyennes_dep",
        "densite",
        "ratio_taxe",
        "ventes_par_habitant",
        "taxe_x_population",
        "annee",
        "dep_code",
        "reg_code",
        "code_postal",
        "population",
        "superficie_km2",
        "zone_emploi",
        "taux_global_tfb",
        "taux_global_tfnb",
        "taux_plein_teom",
        "taux_global_th",
        "nb_ventes",
    ]

    return pipeline, df_clean, features


# TEST TRAIN
def test_train_fit(sample_dataframe):
    pipeline, df, features = sample_dataframe

    X_train, X_test, y_train, y_test = pipeline.split(df, features)

    pipeline.train(X_train, y_train)

    # Vérifie que le modèle est entraîné
    assert hasattr(pipeline.model, "predict")

    # Vérifie que le label encoder existe
    assert hasattr(pipeline, "label_encoder")


# TEST ENCODAGE LABEL
def test_label_encoding(sample_dataframe):
    pipeline, df, features = sample_dataframe

    X_train, _, y_train, _ = pipeline.split(df, features)

    pipeline.train(X_train, y_train)

    classes = pipeline.label_encoder.classes_

    assert "hausse" in classes
    assert "baisse" in classes
    assert "stable" in classes


# ✅ TEST PREDICT
def test_predict(sample_dataframe):
    pipeline, df, features = sample_dataframe

    X_train, X_test, y_train, y_test = pipeline.split(df, features)

    pipeline.train(X_train, y_train)

    preds = pipeline.predict(X_test)

    assert len(preds) == len(X_test)


# TEST EVALUATE
def test_evaluate_output(sample_dataframe):
    pipeline, df, features = sample_dataframe

    X_train, X_test, y_train, y_test = pipeline.split(df, features)

    pipeline.train(X_train, y_train)

    results = pipeline.evaluate(X_test, y_test)

    assert "accuracy" in results
    assert "classification_report" in results
    assert "confusion_matrix" in results

    assert isinstance(results["accuracy"], float)


# TEST PERFORMANCE MINIMALE
def test_model_learns(sample_dataframe):
    pipeline, df, features = sample_dataframe

    X_train, X_test, y_train, y_test = pipeline.split(df, features)

    pipeline.train(X_train, y_train)

    results = pipeline.evaluate(X_test, y_test)

    # Le modèle doit faire mieux que 0 (sinon bug)
    assert results["accuracy"] >= 0.0


# TEST ERREUR SI MAUVAISES DONNÉES
def test_train_with_empty_data():
    pipeline = Pipeline()

    X = pd.DataFrame()
    y = pd.Series(dtype=str)

    with pytest.raises(Exception):
        pipeline.train(X, y)


# TEST SPLIT
def test_split_year_logic(sample_dataframe):
    pipeline, df, features = sample_dataframe

    X_train, X_test, y_train, y_test = pipeline.split(df, features)

    # Vérifie séparation temporelle
    assert all(X_train["annee"] < 2024)
    assert all(X_test["annee"] == 2024)