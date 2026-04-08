import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from xgboost import XGBClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline as SklearnPipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

mlflow.sklearn.autolog()


class Pipeline:
    def __init__(
        self,
        target_col="y",
        drop_cols=None,
        bad_dep_codes=None,
        selected_k=20,
        random_state=42,
        numeric_cols=None,
        categorical_cols=None,
    ):
        self.target_col = target_col
        self.drop_cols = drop_cols or ["dep_nom", "reg_nom", "variation"]
        self.bad_dep_codes = bad_dep_codes or ["2A", "2B"]
        self.selected_k = selected_k
        self.random_state = random_state

        self.categorical_cols = (
            categorical_cols
            if categorical_cols is not None
            else ["dep_code", "reg_code", "code_postal"]
        )

        self.numeric_cols = (
            numeric_cols
            if numeric_cols is not None
            else [
                "annee",
                "population",
                "superficie_km2",
                "zone_emploi",
                "taux_global_tfb",
                "taux_global_tfnb",
                "taux_plein_teom",
                "taux_global_th",
                "nb_ventes",
                "densite",
                "ratio_taxe",
                "ventes_par_habitant",
                "taxe_x_population",
                "evolution_ventes",
                "evolution_taxe",
                "taxe_vs_moyenne_dep",
                "ventes_moyennes_dep",
            ]
        )

        transformers = []
        if self.numeric_cols:
            transformers.append(("num", SimpleImputer(strategy="mean"), self.numeric_cols))
        if self.categorical_cols:
            transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.categorical_cols))

        preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")

        self.model = SklearnPipeline(
            [
                ("preprocessing", preprocessor),
                ("selector", SelectKBest(f_classif, k=self.selected_k)),
                (
                    "classifier",
                    XGBClassifier(
                        random_state=self.random_state,
                        n_estimators=300,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        eval_metric="mlogloss",
                        use_label_encoder=False,
                    ),
                ),
            ]
        )

    def load_csv(self, csv_path: str, sep=";") -> pd.DataFrame:
        return pd.read_csv(csv_path, sep=sep)

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        existing_drop = [c for c in self.drop_cols if c in df.columns]
        df = df.drop(columns=existing_drop)

        if "dep_code" in df.columns:
            df = df[~df["dep_code"].isin(self.bad_dep_codes)]

        df = df.dropna().reset_index(drop=True)
        # Feature engineering ici

        df["densite"] = df["population"] / (df["superficie_km2"] + 1)

        df["ratio_taxe"] = df["taux_global_tfb"] / (df["taux_global_th"] + 1)

        df["ventes_par_habitant"] = df["nb_ventes"] / (df["population"] + 1)

        df["taxe_x_population"] = df["taux_global_tfb"] * (df["population"] + 1)


        df["evolution_ventes"] = df.groupby("code_postal")["nb_ventes"].pct_change()
        df["evolution_taxe"] = df.groupby("code_postal")["taux_global_tfb"].pct_change()

        df["taxe_vs_moyenne_dep"] = df["taux_global_tfb"] / df.groupby("dep_code")["taux_global_tfb"].transform("mean")

        df["ventes_moyennes_dep"] = df.groupby("dep_code")["nb_ventes"].transform("mean")

        return df


    def split(self, df: pd.DataFrame, features, year_col="annee"):
        if year_col not in df.columns:
            raise ValueError(f"Colonne de split '{year_col}' introuvable")

        train_df = df[df[year_col] < 2024]
        test_df = df[df[year_col] == 2024]

        X_train = train_df[features]
        y_train = train_df[self.target_col]
        X_test = test_df[features]
        y_test = test_df[self.target_col]

        return X_train, X_test, y_train, y_test

    def train(self, X_train, y_train):
        if isinstance(X_train, np.ndarray):
            if self.numeric_cols is None:
                self.numeric_cols = [f"col{i}" for i in range(X_train.shape[1])]
            X_train = pd.DataFrame(X_train, columns=self.numeric_cols)

        if isinstance(y_train, (list, np.ndarray)):
            y_train = pd.Series(y_train)

        self.label_encoder = LabelEncoder()
        y_train_encoded = self.label_encoder.fit_transform(y_train)

        self.model.fit(X_train, y_train_encoded)
        return self

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        y_pred = self.model.predict(X_test)
        y_pred = self.label_encoder.inverse_transform(y_pred)
        return {
            "accuracy": accuracy_score(y_test, y_pred),
            "classification_report": classification_report(y_test, y_pred, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, y_pred, labels=["hausse", "baisse", "stable"]),
        }

    def predict(self, X: pd.DataFrame):
        return self.model.predict(X)


if __name__ == "__main__":
    print("Ce module est prévu pour être importé depuis une commande de type 'python train.py'")
