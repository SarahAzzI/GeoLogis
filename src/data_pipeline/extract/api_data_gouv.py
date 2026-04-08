import requests
import pandas as pd


DVF_API_URL = (
    "https://tabular-api.data.gouv.fr/api/resources/"
    "d7933994-2c66-4131-a4da-cf7cd18040a4/data/"
)


def fetch_data(page_size=100, max_calls=50):

    data = []
    page = 1

    while page <= max_calls: 

        resp = requests.get(DVF_API_URL, params={"page": page, "page_size": page_size}, timeout=30)
        
        if resp.status_code == 200:
            response_data = resp.json()           
            rows = response_data.get("data", [])
            if not rows:
                break
            data.extend(rows)
        else:
            print(f"Erreur : {resp.status_code}")
            print(resp.text)
            break

        page += 1                               

    df = pd.DataFrame(data)

    df.to_csv("raw/immo_data2.csv", index=False)
    print("Données sauvegardées dans immo_data.csv")
    return df