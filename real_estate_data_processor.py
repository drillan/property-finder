import json
import logging
import os
import time
import unicodedata
from dataclasses import dataclass, field
from itertools import product
from math import cos, floor, log, pi, radians, sin, tan
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import streamlit as st
from requests.exceptions import RequestException

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """データ設定を管理するデータクラス"""
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent / "data")
    RAW_DATA_DIR: Path = field(
        default_factory=lambda: Path(__file__).parent / "data" / "raw_data"
    )
    API_URL: str = "https://www.reinfolib.mlit.go.jp/ex-api/external/XIT001"
    GEOJSON_API_URL: str = "https://www.reinfolib.mlit.go.jp/ex-api/external/XPT001"
    
    CITIES: List[str] = field(default_factory=lambda: [
        "13102",  # 中央区
        "13106",  # 台東区
        "13101",  # 千代田区
    ])
    YEARS: List[str] = field(default_factory=lambda: [str(year) for year in range(2010, 2025)])
    
    COLUMN_TYPES: Dict[str, List[str]] = field(default_factory=lambda: {
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
    })

class DataDownloader:
    """データのダウンロードを担当するクラス"""
    def __init__(self, config: DataConfig = DataConfig()):
        self.config = config
        self.subscription_key = self._get_subscription_key()
        self.config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_subscription_key() -> str:
        """サブスクリプションキーの取得"""
        try:
            return st.secrets["OCP_APIM_SUBSCRIPTION_KEY"]
        except KeyError:
            logger.error("Subscription key not found in secrets")
            raise ValueError("APIサブスクリプションキーが設定されていません")

    def get_data(self, year: str, city: str, area: str = "13") -> pd.DataFrame:
        """APIからデータを取得"""
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
        params = {"year": year, "area": area, "city": city}
        
        try:
            response = requests.get(self.config.API_URL, headers=headers, params=params)
            response.raise_for_status()
            return pd.DataFrame(response.json()["data"])
        except RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def store_data(self) -> None:
        """データをダウンロードしてParquet形式で保存"""
        for year, city in product(self.config.YEARS, self.config.CITIES):
            output_file = self.config.RAW_DATA_DIR / f"{year}-{city}.parquet"
            
            if output_file.exists():
                logger.info(f"Skipping existing file for year: {year}, city: {city}")
                continue
                
            try:
                logger.info(f"Downloading data for year: {year}, city: {city}")
                df = self.get_data(year=year, city=city)
                df.to_parquet(output_file)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Failed to download data for year {year}, city {city}: {e}")

class DataFormatter:
    """データの整形を担当するクラス"""
    def __init__(self, config: DataConfig = DataConfig()):
        self.config = config

    def cast_series(self, df: pd.DataFrame, col_name: str) -> pd.Series:
        """列の型変換を行う"""
        try:
            if col_name in self.config.COLUMN_TYPES["float"]:
                return (df[col_name]
                       .replace({"戦前": np.nan, " ": np.nan, "": np.nan})
                       .str.replace("年", "", regex=False)
                       .astype(float))
            
            if col_name in self.config.COLUMN_TYPES["date"]:
                return (df[col_name]
                       .str.replace("年第", "Q", regex=False)
                       .str.replace("四半期", "", regex=False)
                       .apply(lambda x: pd.Period(x, freq="Q").end_time))
            
            if col_name in self.config.COLUMN_TYPES["normalize"]:
                return df[col_name].map(lambda x: unicodedata.normalize("NFKC", x))
            
            return df[col_name]
        except Exception as e:
            logger.error(f"Error casting column {col_name}: {e}")
            raise

    def format_data(self) -> None:
        """全データの整形と保存"""
        try:
            all_files = list(self.config.RAW_DATA_DIR.glob("*.parquet"))
            if not all_files:
                logger.warning("No files found in raw_data folder")
                return
            
            df = pd.concat([pd.read_parquet(file) for file in all_files], ignore_index=True)
            processed_series = [self.cast_series(df, col) for col in df.columns]
            formatted_df = pd.concat(processed_series, axis=1)
            
            final_file = self.config.BASE_DIR / "data.parquet"
            formatted_df.to_parquet(final_file)
            logger.info(f"Formatted data saved to {final_file}")
        except Exception as e:
            logger.error(f"Error formatting data: {e}")
            raise

class GeoJsonDownloader:
    """地理データのダウンロードを担当するクラス"""
    def __init__(self, config: DataConfig = DataConfig()):
        self.config = config
        self.subscription_key = DataDownloader._get_subscription_key()

    @staticmethod
    def latlon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """緯度経度をタイル座標に変換"""
        n = 2**zoom
        lat_rad = radians(lat)
        x = floor(n * ((lon + 180) / 360))
        y = floor(n * (1 - (log(tan(lat_rad) + 1 / cos(lat_rad)) / pi)) / 2)
        return x, y

    def get_geojson(
        self, 
        lat: float, 
        lon: float, 
        zoom: int, 
        *,
        from_date: int,
        to_date: int,
    ) -> dict:
        """指定された座標のGeoJSONデータを取得
        
        Args:
            lat: 緯度
            lon: 経度
            zoom: ズームレベル
            from_date: 開始日（形式：YYYYQ、例：20101は2010年第1四半期）
            to_date: 終了日（形式：YYYYQ、例：20244は2024年第4四半期）
        """
        try:
            headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
            x, y = self.latlon_to_tile(lat, lon, zoom)
            
            params = {
                "response_format": "geojson",
                "z": zoom,
                "x": x,
                "y": y,
                "from": from_date,
                "to": to_date,
            }
            
            response = requests.get(self.config.GEOJSON_API_URL, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Failed to fetch GeoJSON data: {e}")
            raise

class GeoJsonProcessor:
    """GeoJSONデータを処理してDataFrameに変換するクラス"""
    
    @staticmethod
    def _convert_price(price_str: str) -> float:
        """価格文字列を数値に変換（例：'1,300万円' -> 13000000.0）
        
        Args:
            price_str: 価格文字列（例：'1,300万円'）
            
        Returns:
            float: 変換後の数値
        """
        try:
            # カンマと'万円'を除去
            cleaned = price_str.replace(',', '').replace('万円', '')
            if not cleaned:
                return np.nan
            return float(cleaned) * 10000
        except (ValueError, AttributeError):
            return np.nan

    @staticmethod
    def _convert_area(area_str: str) -> float:
        """面積文字列を数値に変換（例：'15㎡' -> 15.0）
        
        Args:
            area_str: 面積文字列（例：'15㎡'）
            
        Returns:
            float: 変換後の数値
        """
        try:
            # '㎡'を除去
            cleaned = area_str.replace('㎡', '')
            if not cleaned:
                return np.nan
            return float(cleaned)
        except (ValueError, AttributeError):
            return np.nan

    def process_geojson(self, geojson_data: dict) -> pd.DataFrame:
        """GeoJSONデータをDataFrameに変換
        
        Args:
            geojson_data: GeoJSONデータ
            
        Returns:
            pd.DataFrame: 変換後のDataFrame
        """
        features = geojson_data.get('features', [])
        processed_data = []
        
        for feature in features:
            properties = feature.get('properties', {})
            coordinates = feature.get('geometry', {}).get('coordinates', [])
            
            # 価格と面積を先に計算
            price = self._convert_price(properties.get('u_transaction_price_total_ja', ''))
            area = self._convert_area(properties.get('u_area_ja', ''))
            
            # 単位面積あたりの価格を計算（どちらかがnanの場合はnanになる）
            price_per_area = np.nan if pd.isna(price) or pd.isna(area) or area == 0 else price / area
            
            processed_feature = {
                # 位置情報
                'longitude': coordinates[0] if coordinates else np.nan,
                'latitude': coordinates[1] if coordinates else np.nan,
                
                # 時期と地域情報
                'period': properties.get('point_in_time_name_ja', ''),
                'prefecture': properties.get('prefecture_name_ja', ''),
                'city': properties.get('city_name_ja', ''),
                'district': properties.get('district_name_ja', ''),
                'city_code': properties.get('city_code', ''),
                'district_code': properties.get('district_code', ''),
                
                # 取引情報
                'price': price,
                'area': area,
                'price_per_area': price_per_area,  # 追加：単位面積あたりの価格
                'price_per_sqm': properties.get('u_transaction_price_unit_price_square_meter_ja', ''),
                'price_per_tsubo': properties.get('u_unit_price_per_tsubo_ja', ''),
                'transaction_type': properties.get('transaction_contents_name_ja', ''),
                
                # 建物情報
                'structure': properties.get('building_structure_name_ja', ''),
                'floor_plan': properties.get('floor_plan_name_ja', ''),
                'total_floor_area': properties.get('u_building_total_floor_area_ja', ''),
                'construction_year': properties.get('u_construction_year_ja', ''),
                
                # 土地情報
                'land_shape': properties.get('land_shape_name_ja', ''),
                'land_frontage': properties.get('u_land_frontage_ja', ''),
                
                # 道路情報
                'front_road_direction': properties.get('front_road_azimuth_name_ja', ''),
                'front_road_width': properties.get('u_front_road_width_ja', ''),
                'front_road_type': properties.get('front_road_type_name_ja', ''),
                
                # 取引カテゴリ
                'price_category': properties.get('price_information_category_name_ja', '')
            }
            processed_data.append(processed_feature)
            
        return pd.DataFrame(processed_data)

def main() -> None:
    """メイン処理"""
    try:
        st.title("不動産データ分析")
        
        config = DataConfig()
        downloader = DataDownloader(config)
        formatter = DataFormatter(config)
        
        downloader.store_data()
        formatter.format_data()
        logger.info("Data processing completed successfully")
    except Exception as e:
        logger.error(f"Main process failed: {e}")
        raise

if __name__ == "__main__":
    main()
    # geo_json_downloader = GeoJsonDownloader()
    # geo_json = geo_json_downloader.get_geojson(35.691953, 139.781719, 15, from_date=20101, to_date=20244)
    # print(geo_json)