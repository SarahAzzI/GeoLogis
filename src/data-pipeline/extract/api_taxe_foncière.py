import requests
import pandas as pd
import time
import sys
from ...ml_service.app.model.database import engine

# ------------------------------------------------------------------ #
#  Config                                                              #
# ------------------------------------------------------------------ #
BASE_URL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets"
DATASET  = "fiscalite-locale-des-particuliers"
ANNEES   = [2021, 2022, 2023, 2024]

# Champs exacts confirmés par le JSON brut de l'API
CODE_FIELD  = "insee_com"   # TEXT  → guillemets simples dans WHERE
ANNEE_FIELD = "exercice"    # TEXT  → guillemets simples dans WHERE (pas un int !)

SELECT_FIELDS = [
    "insee_com",          # code INSEE commune (5 chars)
    "exercice",           # année fiscale (string "2021", "2022"...)
    "dep",                # code département
    "libcom",             # libellé commune
    "taux_global_tfb",    # ← taxe foncière bâtie   (feature principale)
    "taux_global_tfnb",   # taxe foncière non bâtie
    "taux_plein_teom",    # taxe enlèvement ordures ménagères
    "taux_global_th",     # taxe d'habitation
]

NUMERIC_COLS = [
    "taux_global_tfb", "taux_global_tfnb",
    "taux_plein_teom", "taux_global_th",
]

# ------------------------------------------------------------------ #
#  Chefs-lieux (COG INSEE 2024)                                       #
# ------------------------------------------------------------------ #
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
    # DOM
    "971": ("97105", "Basse-Terre"),
    "972": ("97209", "Fort-de-France"),
    "973": ("97302", "Cayenne"),
    "974": ("97411", "Saint-Denis"),
    "976": ("97608", "Mamoudzou"),
}

def fetch_record(code_insee: str, annee: int) -> dict | None:
    """
    exercice est un champ TEXT dans ce dataset  →  guillemets simples obligatoires.
    insee_com est aussi TEXT                    →  idem.
    """
    url    = f"{BASE_URL}/{DATASET}/records"
    params = {
        "where":  f"{CODE_FIELD}='{code_insee}' AND {ANNEE_FIELD}='{annee}'",
        "select": ",".join(SELECT_FIELDS),
        "limit":  1,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            print(
                f"  ✗ HTTP {r.status_code} — {code_insee}/{annee}: {r.text[:300]}",
                file=sys.stderr,
            )
            return None
        results = r.json().get("results", [])
        return results[0] if results else None
    except requests.RequestException as e:
        print(f"  ✗ Réseau — {code_insee}/{annee}: {e}", file=sys.stderr)
        return None


def fetch_with_fallback(
    code_insee: str, annee: int
) -> tuple[dict | None, int | None]:
    row = fetch_record(code_insee, annee)
    if row:
        return row, annee

    # Priorité : année-1, année+1, année-2, ...
    fallback_order = []
    for delta in range(1, len(ANNEES) + 1):
        if annee - delta in ANNEES:
            fallback_order.append(annee - delta)
        if annee + delta in ANNEES:
            fallback_order.append(annee + delta)

    for fb_annee in fallback_order:
        row = fetch_record(code_insee, fb_annee)
        if row:
            print(
                f"  ↩ Fallback {code_insee}/{annee} → utilisé {fb_annee}",
                file=sys.stderr,
            )
            return row, fb_annee

    return None, None


if __name__ == "__main__":
    records = []
    total   = len(CHEFS_LIEUX) * len(ANNEES)
    done    = 0

    for annee in ANNEES:
        for dept, (code_insee, nom_commune) in sorted(CHEFS_LIEUX.items()):
            done += 1
            row, annee_src = fetch_with_fallback(code_insee, annee)

            if row:
                row["dept"]         = dept
                row["nom_commune"]  = nom_commune
                row["annee_cible"]  = annee
                row["annee_source"] = annee_src
                row["est_fallback"] = (annee != annee_src)
                records.append(row)
                flag = "↩" if row["est_fallback"] else "✓"
                print(
                    f"  {flag} [{done:>3}/{total}] {dept:>3} | {nom_commune:<25}"
                    f" | {code_insee} | {annee}"
                    + (f" → src:{annee_src}" if row["est_fallback"] else "")
                )
            else:
                print(
                    f"  ✗ [{done:>3}/{total}] {dept:>3} | {nom_commune:<25}"
                    f" | {code_insee} | {annee} → aucune donnée"
                )

            time.sleep(0.15)

    if not records:
        print("\n⚠️  Aucune donnée collectée.")
        sys.exit(1)

    df = pd.DataFrame(records)

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    col_order = [
        "dept", "nom_commune", "insee_com",
        "annee_cible", "annee_source", "est_fallback",
        "taux_global_tfb",   # taxe foncière bâtie  ← feature principale
        "taux_global_tfnb",  # taxe foncière non bâtie
        "taux_plein_teom",   # ordures ménagères
        "taux_global_th",    # taxe d'habitation
    ]
    df = df[[c for c in col_order if c in df.columns]]
    df = df.sort_values(["dept", "annee_cible"]).reset_index(drop=True)

    nb_fallback = int(df["est_fallback"].sum())
    if nb_fallback:
        print(f"\n⚠️  {nb_fallback} ligne(s) avec fallback :")
        print(
            df[df["est_fallback"]][
                ["dept", "nom_commune", "annee_cible", "annee_source"]
            ].to_string(index=False)
        )

    df.to_sql(name="taxe_fonciere", con=engine, if_exists="replace")
