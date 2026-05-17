import math
import os
import pandas as pd
from models import Resort

RESORTS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'resorts.csv')


def load_resorts() -> list[Resort]:
    df = pd.read_csv(RESORTS_CSV, na_values=[''], keep_default_na=False)
    df = df.where(pd.notna(df), other=None)
    records = df.to_dict(orient='records')
    # pandas represents missing floats as float('nan') after to_dict; convert to None
    cleaned = [
        {k: None if isinstance(v, float) and math.isnan(v) else v for k, v in row.items()}
        for row in records
    ]
    return [Resort(**row) for row in cleaned]
