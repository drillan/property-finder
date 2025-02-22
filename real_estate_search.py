from pathlib import Path
from typing import Optional

import duckdb
import streamlit as st

import search_params  # 追加: search_paramsモジュールのインポート
from base_analyzer import BaseAnalyzer

data_dir = Path(__file__).parent / "data"
data_file = data_dir / "data.parquet"


def load_data() -> duckdb.DuckDBPyRelation:
    return duckdb.sql(f"SELECT * FROM read_parquet('{data_file.as_posix()}')")


@st.fragment
def init() -> None:
    st.title("不動産データ検索")
    load_data()  # 単にデータを読み込むが、返り値は使用しない


@st.fragment
def search():
    params = (
        search_params.render_search_parameters()
    )  # パラメータを別モジュールから取得
    if st.button("Search"):
        conditions = []
        filter_count = 0

        # リスト系パラメータのOR条件生成のヘルパー関数
        def build_or_condition(col_name, items):
            if not items:
                return None
            if len(items) == 1:
                return f"{col_name} = '{items[0]}'"
            return "(" + " OR ".join([f"{col_name} = '{item}'" for item in items]) + ")"

        # 数値レンジ系フィルタ用の条件生成関数
        def build_range_condition(col_name, value, default):
            if value != default:
                return f"{col_name} >= {value[0]} AND {col_name} <= {value[1]}"
            return None

        # リストベースのフィルタ条件（等価比較）の定義
        mapping_list = {
            "price_category": "PriceCategory",
            "type_": "Type",
            "region": "Region",
            "municipality": "Municipality",
            "districtName": "DistrictName",
            "floor_plan": "FloorPlan",
            "land_shape": "LandShape",
            "structure": "Structure",
            "direction": "Direction",
            "classification": "Classification",
            "city_planning": "CityPlanning",
            "renovation": "Renovation",
            "remarks": "Remarks",
        }
        for key, col in mapping_list.items():
            condition = build_or_condition(col, params.get(key))
            if condition:
                conditions.append(condition)
                filter_count += 1

        # 数値レンジ系のフィルタ条件の定義
        mapping_range = {
            "trade_price": ("TradePrice", (1200, 32000000000)),
            "price_per_unit": ("PricePerUnit", (1200, 60000000)),
            "area": ("Area", (10, 1000)),
            "unit_price": ("UnitPrice", (7400, 18000000)),
            "frontage": ("Frontage", (0, 1000)),
            "total_floor_area": ("TotalFloorArea", (5, 1000)),
            "building_year": ("BuildingYear", (1946, 2025)),
            "breadth": ("Breadth", (1, 99)),
            "coverage_ratio": ("CoverageRatio", (50, 90)),
            "floor_area_ratio": ("FloorAreaRatio", (10, 1300)),
        }
        for key, (col, default) in mapping_range.items():
            condition = build_range_condition(col, params.get(key), default)
            if condition:
                conditions.append(condition)
                filter_count += 1

        # 日付フィルタ
        if (
            params.get("fr_date") != "2010-03-31"
            and params.get("to_date") != "2024-06-30"
        ):
            conditions.append(
                f"Period >= '{params['fr_date']}' AND Period <= '{params['to_date']}'"
            )
            filter_count += 1

        # ベースとなるリレーション生成（全件取得）
        base_relation = duckdb.sql(
            f"SELECT * FROM read_parquet('{data_file.as_posix()}')"
        )
        if conditions:
            combined_conditions = " AND ".join(conditions)
            filtered_relation = base_relation.filter(combined_conditions)
        else:
            filtered_relation = base_relation

        st.write(f"フィルタ数: {filter_count}")
        st.dataframe(filtered_relation.to_df())


# --- ここから変更: real_estate_search_page関数の追加 ---
def real_estate_search_page():
    """
    メインから呼び出す不動産検索ページの表示関数です。
    """
    init()  # タイトル表示、データ読み込み
    search()  # 検索機能の実行


class SearchAnalyzer(BaseAnalyzer):
    """検索機能クラス"""
    
    def _build_or_condition(self, col_name: str, items: list) -> Optional[str]:
        """OR条件の生成"""
        if not items:
            return None
        if len(items) == 1:
            return f"{col_name} = '{items[0]}'"
        return "(" + " OR ".join([f"{col_name} = '{item}'" for item in items]) + ")"

    def _build_range_condition(self, col_name: str, value: tuple, default: tuple) -> Optional[str]:
        """範囲条件の生成"""
        if value != default:
            return f"{col_name} >= {value[0]} AND {col_name} <= {value[1]}"
        return None

    def run(self):
        """検索機能の実行"""
        st.title("不動産データ検索")
        
        params = search_params.render_search_parameters()
        if not st.button("Search"):
            return
            
        conditions = []
        filter_count = 0
        
        # ... 検索条件の構築 ...
        
        base_relation = self._load_data()
        if base_relation is None:
            return
            
        if conditions:
            combined_conditions = " AND ".join(conditions)
            filtered_relation = base_relation.filter(combined_conditions)
        else:
            filtered_relation = base_relation

        st.write(f"フィルタ数: {filter_count}")
        st.dataframe(filtered_relation.to_df())


if __name__ == "__main__":
    real_estate_search_page()
# --- ここまで変更 ---
