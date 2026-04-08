import pandas as pd
from pathlib import Path


class DataIngestion:
    COLS_COMMUNE = [
        "annee", "code_insee", "nom_standard", "code_postal",
        "dep_code", "dep_nom", "reg_code", "reg_nom",
        "population", "densite", "superficie_km2",
        "latitude_centre", "longitude_centre", "zone_emploi",
    ]

    def __init__(self, base_dir: Path, output_dir: Path = Path("raw")):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def load_dvf_aggregated(self, years: list[int]) -> pd.DataFrame:
        frames = []
        for year in years:
            path = self.output_dir / f"csv_agg_{year}.csv"
            df = pd.read_csv(path, sep=";", low_memory=False)
            frames.append(df)
        return pd.concat(frames, ignore_index=True)

    def load_communes(self, years: list[int]) -> pd.DataFrame:
        BASE_YEAR = 2022
        df_base = None
        frames = []
        for year in years:
            p = self.base_dir / "flatfiles" / "commune_france" / f"communes_france_{year}.csv"
            if p.exists():
                df = pd.read_csv(p, low_memory=False)
            else:
                if df_base is None:
                    df_base = pd.read_csv(
                        self.base_dir / "flatfiles" / "commune_france" / f"communes_france_{BASE_YEAR}.csv",
                        low_memory=False,
                    )
                df = df_base.copy()
            df["annee"] = year
            frames.append(df[self.COLS_COMMUNE])
        return pd.concat(frames, ignore_index=True)

    def load_taxes(self) -> pd.DataFrame:
        path = self.base_dir / "flatfiles" / "taxe_fonciere_chefs_lieux_2021_2024.csv"
        df = pd.read_csv(path)
        df_2025 = df[df["annee_cible"] == 2024].copy()
        df_2025["annee_cible"] = 2025
        df_2020 = df[df["annee_cible"] == 2021].copy()
        df_2020["annee_cible"] = 2020
        return pd.concat([df, df_2025, df_2020], ignore_index=True)

    def load_emploi(self) -> pd.DataFrame:
        path = self.base_dir / "flatfiles" / "nbr_emploi_par_region.csv"
        df = pd.read_csv(path, sep=",", skiprows=3, header=0)
        return df.rename(columns={
            "Unnamed: 0": "reg_nom",
            "Emploi total": "emploi_total",
            "Emploi non salarié": "emploi_non_salarie",
            "Emploi salarié": "emploi_salarie",
            "Agriculture": "part_agriculture",
            "Industrie": "part_industrie",
            "Construction": "part_construction",
            "Tertiaire marchand": "part_tertiaire_marchand",
            "Tertiaire non marchand": "part_tertiaire_non_marchand",
        })

    def load_osm(self) -> pd.DataFrame:
        path = self.base_dir / "flatfiles" / "osm_france.csv"
        df = pd.read_csv(path)
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df = df[df["lat"].between(41.0, 51.5) & df["lon"].between(-5.5, 9.5)]
        df = df.dropna(subset=["lat", "lon"])
        agg = (
            df.groupby(["region", "category"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        path_out = self.output_dir / "csv_osm.csv"
        agg.to_csv(path_out, index=False, sep=";", encoding="utf-8")
        return agg

    def load_inflation(self) -> dict:
        path = self.base_dir / "flatfiles" / "taux_inflation.csv"
        df = pd.read_csv(path, sep=";", parse_dates=["Date"])
        col = [c for c in df.columns if "inflation" in c.lower()][0]
        df = df.rename(columns={col: "taux_inflation"})
        df["annee"] = df["Date"].dt.year
        df["taux_inflation"] = df["taux_inflation"] / 100
        mapping = (
            df.sort_values("Date")
            .groupby("annee")["taux_inflation"]
            .last()
            .to_dict()
        )
        if 2025 not in mapping:
            mapping[2025] = mapping[2024]
        return mapping