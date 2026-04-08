import requests
import pandas as pd
import io
import os
import time

target_dir = "/Users/sarah/Desktop/brief/GeoLogis/GeoLogis/src/data-pipeline/merge/raw"
os.makedirs(target_dir, exist_ok=True)

CATEGORIES = {
    "admin_sante":      'nwr["amenity"~"townhall|hospital"]',
    "education":        'nwr["amenity"~"school|university|college"]',
    "transports_rails": 'nwr["railway"~"station|subway_entrance"]',
    "commerces_malls":  'nwr["shop"~"supermarket|mall"]',
    "loisirs_verts":    'nwr["leisure"="park"]'
}


REGIONS = [
    "Île-de-France",
    "Auvergne-Rhône-Alpes",
    "Nouvelle-Aquitaine",
    "Occitanie",
    "Hauts-de-France",
    "Grand Est",
    "Provence-Alpes-Côte d'Azur",
    "Normandie",
    "Bretagne",
    "Pays de la Loire",
    "Bourgogne-Franche-Comté",
    "Centre-Val de Loire",
]

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
MAX_RETRIES  = 4
RETRY_DELAY  = 60   
POLITE_DELAY = 15   


def build_query(tag: str, region: str) -> str:
    """Construit une requête Overpass avec geocodeArea pour rester dans les frontières officielles."""
    return f"""
        [out:csv(::id, ::lat, ::lon, "name", "amenity", "railway",
                 "shop", "leisure", "addr:postcode"; true; ",")]
        [timeout:600];
        area["name"="{region}"]["boundary"="administrative"]->.searchArea;
        ({tag}(area.searchArea););
        out center;
    """


def fetch_with_retry(tag: str, region: str, label: str) -> pd.DataFrame | None:
    """Envoie la requête avec gestion des erreurs et des retries."""
    query = build_query(tag, region)

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"   📡 {label} — tentative {attempt}/{MAX_RETRIES}...")
        try:
            r = requests.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=650,
                headers={"Accept-Charset": "utf-8"}
            )

            if r.status_code == 200:
                r.encoding = "utf-8"
                df = pd.read_csv(
                    io.StringIO(r.text),
                    low_memory=False,
                    dtype=str
                )
                if not df.empty and len(df) > 1:  
                    print(f"   ✅ {len(df)} points récupérés.")
                    return df
                else:
                    print(f"   ⚠️  Réponse vide pour {label}.")
                    return None

            elif r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 90))
                print(f"   ⏳ Rate limit (429) — pause {wait}s...")
                time.sleep(wait)

            elif r.status_code == 504:
                print(f"   ⚠️  Serveur surchargé (504) — pause {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

            else:
                print(f"   ❌ Erreur HTTP {r.status_code} — abandon.")
                return None

        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout — pause {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

        except Exception as e:
            print(f"   ❌ Erreur technique : {e}")
            return None

    print(f"   ❌ Échec après {MAX_RETRIES} tentatives — {label} ignoré.")
    return None



all_dfs  = []
failed   = []  

print("🚀 Lancement de l'extraction GeoLogis 2026 (geocodeArea — Frontières officielles)\n")

for cat_name, tag in CATEGORIES.items():
    print(f"\n📂 Catégorie : {cat_name}")
    for region in REGIONS:
        label = f"{cat_name} / {region}"
        df = fetch_with_retry(tag, region, label)

        if df is not None:
            df["category"] = cat_name
            df["region"]   = region
            all_dfs.append(df)
        else:
            failed.append(label)

        time.sleep(POLITE_DELAY)


if failed:
    print(f"\n⚠️  Lots non récupérés ({len(failed)}) :")
    for f in failed:
        print(f"   - {f}")


if not all_dfs:
    print("\n❌ Aucune donnée récupérée.")
else:
    df_final = pd.concat(all_dfs, ignore_index=True)

    
    df_final = df_final.rename(columns={
        "@id":          "osm_id",
        "@lat":         "lat",
        "@lon":         "lon",
        "addr:postcode":"code_postal"
    })

    
    df_final["code_postal"] = (
        df_final["code_postal"]
        .astype(str)
        .str.strip()
        .replace("nan", "")
    )

    
    df_clean = df_final[
        ~df_final["code_postal"].str.startswith("67", na=False)
    ].copy()

    
    df_clean = df_clean.drop_duplicates(subset=["osm_id"])

    
    df_clean["name"] = (
        df_clean["name"]
        .astype(str)
        .str.encode("utf-8", errors="ignore")
        .str.decode("utf-8")
        .replace("nan", "")
    )

    
    output_path = os.path.join(target_dir, "osm_france_2026_strict.csv")
    df_clean.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\n✨ Extraction terminée avec succès !")
    print(f"📊 Total : {len(df_clean)} POI")
    print(f"📁 Fichier : {output_path}")

    
    print("\n📈 Répartition par catégorie :")
    print(df_clean["category"].value_counts().to_string())