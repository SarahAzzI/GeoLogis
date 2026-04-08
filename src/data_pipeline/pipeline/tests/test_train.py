import pytest
import pandas as pd
from pipeline import Pipeline


@pytest.fixture
def sample_data():
    # Dataset simple
    X = pd.DataFrame({"f1": [1, 2, 3, 4], "f2": [10, 20, 30, 40]})
    y = pd.Series([0, 0, 1, 1])
    return X, y


def test_train_fit_model(sample_data):
    X, y = sample_data

    pipeline = Pipeline(
        target_col="y",
        drop_cols=[],
        bad_dep_codes=[],
        selected_k=2,
        numeric_cols=["f1", "f2"],
        categorical_cols=[],
    )

    pipeline.train(X, y)

    # Vérifie que le modèle existe
    assert hasattr(pipeline, "model")

    # Vérifie que le modèle est entraîné
    assert hasattr(pipeline.model, "predict")


def test_train_model_learns(sample_data):
    X, y = sample_data

    pipeline = Pipeline(
        target_col="y",
        drop_cols=[],
        bad_dep_codes=[],
        selected_k=2,
        numeric_cols=["f1", "f2"],
        categorical_cols=[],
    )

    pipeline.train(X, y)

    preds = pipeline.model.predict(X)

    # Le modèle doit faire mieux que du hasard ici
    assert len(preds) == len(y)
    assert (preds == y).sum() >= 2  # au moins 50% correct


def test_train_with_empty_data():
    pipeline = Pipeline(
        target_col="y",
        drop_cols=[],
        bad_dep_codes=[],
        selected_k=2,
        numeric_cols=["f1", "f2"],
        categorical_cols=[],
    )

    X = []
    y = []

    with pytest.raises(Exception):
        pipeline.train(X, y)


def test_train_with_mismatched_shapes():
    pipeline = Pipeline(
        target_col="y",
        drop_cols=[],
        bad_dep_codes=[],
        selected_k=2,
        numeric_cols=["f1", "f2"],
        categorical_cols=[],
    )

    X = [[1, 2], [3, 4]]
    y = [0]  # taille différente

    with pytest.raises(Exception):
        pipeline.train(X, y)


def test_train_selected_k_feature_selection(sample_data):
    X, y = sample_data

    pipeline = Pipeline(
        target_col="y",
        drop_cols=[],
        bad_dep_codes=[],
        selected_k=1,  # sélection forte
        numeric_cols=["f1", "f2"],
        categorical_cols=[],
    )

    pipeline.train(X, y)

    # Si tu utilises SelectKBest par ex
    if hasattr(pipeline, "selector"):
        assert pipeline.selector.k == 1