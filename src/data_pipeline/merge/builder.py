import pandas as pd
from pathlib import Path
from ingestion import DataIngestion


class DatasetBuilder:

    SEUIL = 0.03

    def __init__(self, ingestion: DataIngestion):
        self.ing = ingestion
        self._df: pd.DataFrame | None = None

    def build(self, years: list[int] = list(range(2020, 2026))) -> pd.DataFrame:
        # DVF agrégé — lecture des fichiers déjà calculés
        df_dvf = self.ing.load_dvf_aggregated(years)

        # Communes
        df_comm = self.ing.load_communes(years)
        df_dvf["code_commune"] = df_dvf["code_commune"].astype(str).str.zfill(5)
        df_comm["code_insee"] = df_comm["code_insee"].astype(str).str.zfill(5)
        df = df_dvf.merge(
            df_comm,
            left_on=["code_commune", "annee"],
            right_on=["code_insee", "annee"],
            how="left",
        )

        # Taxes foncières
        df_taxes = self.ing.load_taxes()
        df["dep_code"] = df["dep_code"].astype(str).str.zfill(2)
        df_taxes["dept"] = df_taxes["dept"].astype(str).str.zfill(2)
        df["annee"] = df["annee"].astype(int)
        df_taxes["annee_cible"] = df_taxes["annee_cible"].astype(int)
        df = df.merge(
            df_taxes[["dept", "annee_cible", "taux_global_tfb", "taux_global_tfnb", "taux_plein_teom", "taux_global_th"]],
            left_on=["dep_code", "annee"],
            right_on=["dept", "annee_cible"],
            how="left",
        )


        df = self._aggregate_commune(df)
        df = self._label_target(df)

        # Emploi
        df_emploi = self.ing.load_emploi()
        regions_valides = df["reg_nom"].dropna().unique()
        df_emploi = df_emploi[df_emploi["reg_nom"].isin(regions_valides)].reset_index(drop=True)
        df = df.merge(df_emploi, on="reg_nom", how="left")

        # OSM
        df_osm = self.ing.load_osm()
        df = df.merge(df_osm, left_on="reg_nom", right_on="region", how="left")

        # Ajout du taux d'inflation 
        inflation = self.ing.load_inflation()
        df["taux_inflation"] = df["annee"].map(inflation)

        self._df = df
        return df

    def save(self, path: Path | str = "raw/csv_full_post.csv") -> None:
        if self._df is None:
            raise RuntimeError("Appelez build() avant save()")
        self._df.to_csv(path, index=False, sep=";", encoding="utf-8")
        print(f"Dataset sauvegardé : {path} — {self._df.shape}")

    def _aggregate_commune(self, df: pd.DataFrame) -> pd.DataFrame:
        agg = (
            df.groupby(["annee", "code_commune"], dropna=False)
            .agg(
                prix_m2=("prix_m2", "mean"),
                dep_code=("dep_code", "first"),
                dep_nom=("dep_nom", "first"),
                reg_code=("reg_code", "first"),
                reg_nom=("reg_nom", "first"),
                code_postal=("code_postal", "first"),
                population=("population", "sum"),
                superficie_km2=("superficie_km2", "sum"),
                zone_emploi=("zone_emploi", "first"),
                taux_global_tfb=("taux_global_tfb", "mean"),
                taux_global_tfnb=("taux_global_tfnb", "mean"),
                taux_plein_teom=("taux_plein_teom", "mean"),
                taux_global_th=("taux_global_th", "mean"),
                nb_ventes=("nb_ventes", "sum"),
            )
            .reset_index()
            .sort_values(["code_commune", "annee"])
        )
        agg["variation"] = agg.groupby("code_commune")["prix_m2"].pct_change(fill_method=None)
        return agg[agg["annee"] != 2020].reset_index(drop=True)

    def _label_target(self, df: pd.DataFrame) -> pd.DataFrame:
        def trend(x):
            if pd.isna(x):
                return None
            if x > self.SEUIL:
                return "hausse"
            elif x < -self.SEUIL:
                return "baisse"
            return "stable"

        df["y"] = df["variation"].apply(trend)
        return df