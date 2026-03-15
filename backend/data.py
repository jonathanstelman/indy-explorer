import os
import pandas as pd
from models import Resort

RESORTS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'resorts.csv')


def load_resorts() -> list[Resort]:
    df = pd.read_csv(RESORTS_CSV, na_values=[''], keep_default_na=False)
    df = df.where(pd.notna(df), other=None)
    return [Resort(**row) for row in df.to_dict(orient='records')]
