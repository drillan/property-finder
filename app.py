from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

import search_params  # 追加: search_paramsモジュールのインポート

data_dir = Path(__file__).parent / "data"
data_file = str(data_dir / "data.parquet")


def load_data() -> duckdb.DuckDBPyRelation:
    return duckdb.sql(f"SELECT * FROM read_parquet('{data_file}')")


@st.fragment
def init() -> None:
    st.title("不動産データ検索")
    return load_data()


data = init()


@st.fragment
def search():
    params = search_params.render_search_parameters()  # パラメータを別モジュールから取得
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
        if params.get("fr_date") != "2010-03-31" and params.get("to_date") != "2024-06-30":
            conditions.append(f"Period >= '{params['fr_date']}' AND Period <= '{params['to_date']}'")
            filter_count += 1

        # ベースとなるクエリ生成（全件取得）
        base_query = f"SELECT * FROM read_parquet('{data_file}')"
        # 条件がある場合はWHERE句を追加
        if conditions:
            full_query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            full_query = base_query

        filtered_data = duckdb.sql(full_query)
        st.write(f"フィルタ数: {filter_count}")
        st.dataframe(filtered_data.to_df())


search()
