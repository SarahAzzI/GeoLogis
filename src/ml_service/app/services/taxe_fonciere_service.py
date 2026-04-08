import sys
import pandas as pd
import requests
import time
import logging
from datetime import datetime
from typing import Optional

from ..model.database import engine, SessionLocal
from ..model.taxe_fonciere import TaxeFonciere

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Config - mirrored from api_taxe_foncière.py                       #
# ------------------------------------------------------------------ #
BASE_URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets"
DATASET = "fiscalite-locale-des-particuliers"
ANNEES = [2021, 2022, 2023, 2024]

CODE_FIELD = "insee_com"
ANNEE_FIELD = "exercice"

SELECT_FIELDS = [
    "insee_com",
    "exercice",
    "dep",
    "libcom",
    "taux_global_tfb",
    "taux_global_tfnb",
    "taux_plein_teom",
    "taux_global_th",
]

NUMERIC_COLS = [
    "taux_global_tfb",
    "taux_global_tfnb",
    "taux_plein_teom",
    "taux_global_th",
]

CHEFS_LIEUX = {
    "01": ("01053", "Bourg-en-Bresse"),
    "02": ("02408", "Laon"),
    "03": ("03190", "Moulins"),
    "04": ("04070", "Digne-les-Bains"),
    "05": ("05061", "Gap"),
    "06": ("06088", "Nice"),
    "07": ("07186", "Privas"),
    "08": ("08105", "Charleville-Mézières"),
    "09": ("09122", "Foix"),
    "10": ("10387", "Troyes"),
    "11": ("11069", "Carcassonne"),
    "12": ("12202", "Rodez"),
    "13": ("13055", "Marseille"),
    "14": ("14118", "Caen"),
    "15": ("15014", "Aurillac"),
    "16": ("16015", "Angoulême"),
    "17": ("17300", "La Rochelle"),
    "18": ("18033", "Bourges"),
    "19": ("19272", "Tulle"),
    "21": ("21231", "Dijon"),
    "22": ("22278", "Saint-Brieuc"),
    "23": ("23096", "Guéret"),
    "24": ("24322", "Périgueux"),
    "25": ("25056", "Besançon"),
    "26": ("26362", "Valence"),
    "27": ("27229", "Évreux"),
    "28": ("28085", "Chartres"),
    "29": ("29232", "Quimper"),
    "2A": ("2A004", "Ajaccio"),
    "2B": ("2B033", "Bastia"),
    "30": ("30189", "Nîmes"),
    "31": ("31555", "Toulouse"),
    "32": ("32013", "Auch"),
    "33": ("33063", "Bordeaux"),
    "34": ("34172", "Montpellier"),
    "35": ("35238", "Rennes"),
    "36": ("36044", "Châteauroux"),
    "37": ("37261", "Tours"),
    "38": ("38185", "Grenoble"),
    "39": ("39300", "Lons-le-Saunier"),
    "40": ("40192", "Mont-de-Marsan"),
    "41": ("41018", "Blois"),
    "42": ("42218", "Saint-Étienne"),
    "43": ("43157", "Le Puy-en-Velay"),
    "44": ("44109", "Nantes"),
    "45": ("45234", "Orléans"),
    "46": ("46042", "Cahors"),
    "47": ("47091", "Agen"),
    "48": ("48095", "Mende"),
    "49": ("49007", "Angers"),
    "50": ("50502", "Saint-Lô"),
    "51": ("51108", "Châlons-en-Champagne"),
    "52": ("52121", "Chaumont"),
    "53": ("53130", "Laval"),
    "54": ("54395", "Nancy"),
    "55": ("55029", "Bar-le-Duc"),
    "56": ("56260", "Vannes"),
    "57": ("57463", "Metz"),
    "58": ("58194", "Nevers"),
    "59": ("59350", "Lille"),
    "60": ("60057", "Beauvais"),
    "61": ("61001", "Alençon"),
    "62": ("62160", "Arras"),
    "63": ("63113", "Clermont-Ferrand"),
    "64": ("64445", "Pau"),
    "65": ("65440", "Tarbes"),
    "66": ("66136", "Perpignan"),
    "67": ("67482", "Strasbourg"),
    "68": ("68224", "Colmar"),
    "69": ("69123", "Lyon"),
    "70": ("70550", "Vesoul"),
    "71": ("71270", "Mâcon"),
    "72": ("72181", "Le Mans"),
    "73": ("73065", "Chambéry"),
    "74": ("74010", "Annecy"),
    "75": ("75056", "Paris"),
    "76": ("76540", "Rouen"),
    "77": ("77288", "Melun"),
    "78": ("78646", "Versailles"),
    "79": ("79191", "Niort"),
    "80": ("80021", "Amiens"),
    "81": ("81004", "Albi"),
    "82": ("82121", "Montauban"),
    "83": ("83137", "Toulon"),
    "84": ("84007", "Avignon"),
    "85": ("85191", "La Roche-sur-Yon"),
    "86": ("86194", "Poitiers"),
    "87": ("87085", "Limoges"),
    "88": ("88160", "Épinal"),
    "89": ("89024", "Auxerre"),
    "90": ("90010", "Belfort"),
    "91": ("91228", "Évry-Courcouronnes"),
    "92": ("92012", "Nanterre"),
    "93": ("93008", "Bobigny"),
    "94": ("94028", "Créteil"),
    "95": ("95500", "Cergy"),
    "971": ("97105", "Basse-Terre"),
    "972": ("97209", "Fort-de-France"),
    "973": ("97302", "Cayenne"),
    "974": ("97411", "Saint-Denis"),
    "976": ("97608", "Mamoudzou"),
}

class TaxeFonciereService:
    """Service for taxe foncière data operations."""

    def __init__(self):
        self.total_fetched = 0
        self.total_fallback = 0

    def fetch_record(self, code_insee: str, annee: int) -> Optional[dict]:
        """Fetch a single record from the API."""
        url = f"{BASE_URL}/{DATASET}/records"
        params = {
            "where": f"{CODE_FIELD}='{code_insee}' AND {ANNEE_FIELD}='{annee}'",
            "select": ",".join(SELECT_FIELDS),
            "limit": 1,
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            if r.status_code != 200:
                return None
            results = r.json().get("results", [])
            return results[0] if results else None
        except requests.RequestException as e:
            return None

    def fetch_with_fallback(
        self, code_insee: str, annee: int
    ) -> tuple[Optional[dict], Optional[int]]:
        """Fetch record with fallback to nearby years if not found."""
        row = self.fetch_record(code_insee, annee)
        if row:
            return row, annee

        # Fallback priority: year-1, year+1, year-2, year+2, ...
        fallback_order = []
        for delta in range(1, len(ANNEES) + 1):
            if annee - delta in ANNEES:
                fallback_order.append(annee - delta)
            if annee + delta in ANNEES:
                fallback_order.append(annee + delta)

        for fb_annee in fallback_order:
            row = self.fetch_record(code_insee, fb_annee)
            if row:
                self.total_fallback += 1
                return row, fb_annee

        return None, None

    def fetch_all_data(self) -> pd.DataFrame:
        """Fetch all taxe foncière data for all departments and years."""
        records = []
        total = len(CHEFS_LIEUX) * len(ANNEES)
        done = 0

        for annee in ANNEES:
            for dept, (code_insee, nom_commune) in sorted(CHEFS_LIEUX.items()):
                done += 1
                row, annee_src = self.fetch_with_fallback(code_insee, annee)

                if row:
                    row["dept"] = dept
                    row["nom_commune"] = nom_commune
                    row["annee_cible"] = annee
                    row["annee_source"] = annee_src
                    row["est_fallback"] = annee != annee_src
                    records.append(row)
                    self.total_fetched += 1

                time.sleep(0.15)

        return pd.DataFrame(records) if records else pd.DataFrame()

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean the dataframe."""
        if df.empty:
            return df

        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        col_order = [
            "dept",
            "nom_commune",
            "insee_com",
            "annee_cible",
            "annee_source",
            "est_fallback",
            "taux_global_tfb",
            "taux_global_tfnb",
            "taux_plein_teom",
            "taux_global_th",
        ]
        df = df[[c for c in col_order if c in df.columns]]
        df = df.sort_values(["dept", "annee_cible"]).reset_index(drop=True)

        return df

    def save_to_database(self, df: pd.DataFrame, table_name: str = "taxe_fonciere") -> bool:
        """Save dataframe to database using SQLAlchemy ORM."""
        db = SessionLocal()
        try:
            if df.empty:
                logger.warning("Dataframe is empty, cannot save")
                return False

            logger.info(f"Clearing existing records from {table_name}")
            db.query(TaxeFonciere).delete()
            
            logger.info(f"Creating {len(df)} records from dataframe")
            logger.debug(f"DataFrame columns: {list(df.columns)}")
            
            records = []
            for idx, (_, row) in enumerate(df.iterrows()):
                try:
                    # Extract code_postal if available, otherwise use first 2 digits of insee_com as dept
                    code_postal = row.get("code_postal")
                    if pd.isna(code_postal) or code_postal is None:
                        # Fallback: derive from insee_com (first 2 digits) if not available
                        insee_str = str(row.get("insee_com", "00000"))
                        code_postal = insee_str[:2] + "000"  # Placeholder postal code
                    
                    record = TaxeFonciere(
                        dept=row["dept"],
                        nom_commune=row["nom_commune"],
                        insee_com=row["insee_com"],
                        code_postal=str(code_postal),
                        annee_cible=int(row["annee_cible"]),
                        annee_source=int(row["annee_source"]),
                        est_fallback=bool(row["est_fallback"]),
                        taux_global_tfb=float(row["taux_global_tfb"]) if pd.notna(row["taux_global_tfb"]) else None,
                        taux_global_tfnb=float(row["taux_global_tfnb"]) if pd.notna(row["taux_global_tfnb"]) else None,
                        taux_plein_teom=float(row["taux_plein_teom"]) if pd.notna(row["taux_plein_teom"]) else None,
                        taux_global_th=float(row["taux_global_th"]) if pd.notna(row["taux_global_th"]) else None,
                    )
                    records.append(record)
                except Exception as e:
                    logger.error(f"Error creating record at index {idx}: {e}", exc_info=True)
                    raise
            
            logger.info(f"Adding {len(records)} records to session")
            db.add_all(records)
            db.commit()
            logger.info(f"Successfully saved {len(records)} records to database")
            return True
        except Exception as e:
            logger.error(f"Error in save_to_database: {e}", exc_info=True)
            db.rollback()
            return False
        finally:
            db.close()

    def sync_taxe_fonciere_data(self) -> dict:
        """
        Main orchestration method: fetch, process, and save taxe foncière data.
        Returns a summary of the operation.
        """
        start_time = datetime.now()

        try:
            df = self.fetch_all_data()

            if df.empty:
                return {
                    "success": False,
                    "message": "No data fetched",
                    "records_fetched": 0,
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                }

            df = self.process_dataframe(df)

            nb_fallback = int(df["est_fallback"].sum())

            success = self.save_to_database(df)

            if success:
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Sync completed successfully: {len(df)} records saved in {duration}s")

                return {
                    "success": True,
                    "message": "Data synchronized successfully",
                    "records_fetched": self.total_fetched,
                    "records_saved": len(df),
                    "fallback_count": nb_fallback,
                    "duration_seconds": duration,
                }
            else:
                logger.error("Failed to save data to database - check logs for details")
                return {
                    "success": False,
                    "message": "Failed to save data to database",
                    "records_fetched": self.total_fetched,
                    "duration_seconds": (datetime.now() - start_time).total_seconds(),
                }

        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }
