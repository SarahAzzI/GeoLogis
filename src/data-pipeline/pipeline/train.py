import logging
import mlflow
import mlflow.sklearn
from pipeline import Pipeline

import matplotlib
matplotlib.use("Agg")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

mlflow.sklearn.autolog()

mlflow.set_experiment("mon_nouvel_experiment")

experiment = mlflow.get_experiment_by_name("mon_nouvel_experiment")
print(experiment.experiment_id)

def main(csv_path="../merge/raw/csv_full_post.csv"):
    with mlflow.start_run(run_name="Pipeline"):
        pipeline = Pipeline(
            target_col="y",
            drop_cols=["dep_nom", "reg_nom", "variation"],
            bad_dep_codes=["2A", "2B"],
            selected_k=20,
        )

        mlflow.log_param("target_col", "y")
        mlflow.log_param("drop_cols", ["dep_nom", "reg_nom", "variation"])
        mlflow.log_param("bad_dep_codes", ["2A", "2B"])
        mlflow.log_param("selected_k", 20)

        logging.info("Chargement des données")
        df = pipeline.load_csv(csv_path)

        logging.info("Nettoyage des données")
        df_clean = pipeline.clean(df)

        features = [
            "taux_inflation",
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

        X_train, X_test, y_train, y_test = pipeline.split(df_clean, features)

        logging.info("Entraînement du modèle")
        pipeline.train(X_train, y_train)

        logging.info("Évaluation du modèle")
        result = pipeline.evaluate(X_test, y_test)

        mlflow.log_metric("accuracy", result["accuracy"])
        mlflow.log_text(result["classification_report"], "classification_report.txt")
        mlflow.log_text(str(result["confusion_matrix"]), "confusion_matrix.txt")
        

        logging.info("Accuracy: %.4f", result["accuracy"])
        logging.info("Classification report:\n%s", result["classification_report"])
        logging.info("Confusion matrix:\n%s", result["confusion_matrix"])

        return pipeline, result


if __name__ == "__main__":
    main()
