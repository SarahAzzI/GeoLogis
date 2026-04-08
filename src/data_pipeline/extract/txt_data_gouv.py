import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
df = pd.read_csv(BASE_DIR / 'flatfiles' / 'communes-france-2025.csv')

pd.options.display.max_columns = None

df = df.drop(df.columns[[0,4,5,8,9,10,11,14,15,16,17,18,19,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46]], axis=1)

print(df.columns)

CITIES_DATAFRAME = df