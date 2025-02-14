import os
import time
import unicodedata
from itertools import product
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests


class DataConfig:
    """データ設定を管理するクラス"""
    BASE_DIR = Path(__file__).parent / "data"
    RAW_DATA_DIR = BASE_DIR / "raw_data"
    API_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/XIT001"
    
    CITIES = [
        "13102",  # 中央区
        "13106",  # 台東区
        "13101",  # 千代田区
    ]
    YEARS = [str(year) for year in range(2010, 2025)]
    
    COLUMN_TYPES = {
        "str": [
            "PriceCategory", "Type", "Region", "MunicipalityCode",
            "Prefecture", "Municipality", "DistrictName", "FloorPlan",
            "LandShape", "Use", "Purpose", "Direction", "Classification",
            "CityPlanning", "Renovation", "Remarks",
        ],
        "normalize": ["FloorPlan", "Structure"],
        "float": [
            "TradePrice", "PricePerUnit", "Area", "UnitPrice", "Frontage",
            "TotalFloorArea", "BuildingYear", "Breadth", "CoverageRatio",
            "FloorAreaRatio",
        ],
        "date": ["Period"],
    }

class DataDownloader:
    """データのダウンロードを担当するクラス"""
    def __init__(self):
        self.subscription_key = os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")
        DataConfig.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def get_data(self, year: str, city: str, area: str = "13") -> pd.DataFrame:
        """APIからデータを取得"""
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
        params = {"year": year, "area": area, "city": city}
        
        response = requests.get(DataConfig.API_URL, headers=headers, params=params)
        response.raise_for_status()
        return pd.DataFrame(response.json()["data"])

    def store_data(self):
        """データをダウンロードしてParquet形式で保存"""
        for year, city in product(DataConfig.YEARS, DataConfig.CITIES):
            output_file = DataConfig.RAW_DATA_DIR / f"{year}-{city}.parquet"
            
            if output_file.exists():
                print(f"Skipping existing file for year: {year}, city: {city}")
                continue
                
            print(f"Downloading data for year: {year}, city: {city}")
            df = self.get_data(year=year, city=city)
            df.to_parquet(output_file)
            time.sleep(2)

class DataFormatter:
    """データの整形を担当するクラス"""
    @staticmethod
    def cast_series(df: pd.DataFrame, col_name: str) -> pd.Series:
        """列の型変換を行う"""
        if col_name in DataConfig.COLUMN_TYPES["float"]:
            return (df[col_name]
                   .replace({"戦前": np.nan, " ": np.nan, "": np.nan})
                   .str.replace("年", "", regex=False)
                   .astype(float))
        
        if col_name in DataConfig.COLUMN_TYPES["date"]:
            return (df[col_name]
                   .str.replace("年第", "Q", regex=False)
                   .str.replace("四半期", "", regex=False)
                   .apply(lambda x: pd.Period(x, freq="Q").end_time))
        
        if col_name in DataConfig.COLUMN_TYPES["normalize"]:
            return df[col_name].map(lambda x: unicodedata.normalize("NFKC", x))
        
        return df[col_name]

    def format_data(self):
        """全データの整形と保存"""
        all_files = list(DataConfig.RAW_DATA_DIR.glob("*.parquet"))
        if not all_files:
            print("raw_dataフォルダ内にファイルが見つかりません。")
            return
        
        df = pd.concat([pd.read_parquet(file) for file in all_files], ignore_index=True)
        processed_series = [self.cast_series(df, col) for col in df.columns]
        formatted_df = pd.concat(processed_series, axis=1)
        
        final_file = DataConfig.BASE_DIR / "data.parquet"
        formatted_df.to_parquet(final_file)
        print(f"整形済みデータを {final_file} に保存しました。")

def main():
    """メイン処理"""
    downloader = DataDownloader()
    formatter = DataFormatter()
    
    downloader.store_data()
    formatter.format_data()

if __name__ == "__main__":
    main() 