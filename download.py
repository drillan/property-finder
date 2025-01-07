import os
import time
from itertools import product
from pathlib import Path

import pandas as pd
import requests

data_dir = Path(__file__).parent / "data" / "raw_data"
url = "https://www.reinfolib.mlit.go.jp/ex-api/external/XIT001"
cities = [
    "13102",  # 中央区
    "13106",  # 台東区
    "13108",  # 江東区
]
years = [str(year) for year in range(2010, 2025)]
subscription_key = os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")
data_dir.mkdir(exist_ok=True)


def get_data(year: str, city: str, area: str = "13") -> pd.DataFrame:
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {
        "year": year,
        "area": area,
        "city": city,
    }
    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    return pd.DataFrame(json_data["data"])


def store_data():
    for year, city in product(years, cities):
        output_file = data_dir / f"{year}-{city}.parquet"
        df = get_data(year=year, city=city)
        df.to_parquet(output_file)
        time.sleep(2)


store_data()
