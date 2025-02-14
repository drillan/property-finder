from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

data_dir = Path(__file__).parent / "data"
data_file = str(data_dir / "data.parquet")


def load_data() -> duckdb.DuckDBPyRelation:
    return duckdb.sql(f"SELECT * FROM read_parquet('{data_file}')")


@st.fragment
def init() -> None:
    st.title("不動産データ検索")
    return load_data()


data = init()


def make_or_cond_query(col_name: str, items: list) -> str:
    n = len(items)
    if n == 0:
        return "SELECT * FROM filtered_data"
    elif n == 1:
        return f"SELECT * FROM filtered_data WHERE {col_name} = '{items[0]}'"
    elif n > 1:
        return "SELECT * FROM filtered_data WHERE " + " OR ".join(
            [f"{col_name} = '{item}'" for item in items]
        )


@st.fragment
def search():
    price_category = st.multiselect(
        label="取引の種類",
        options=['不動産取引価格情報', '成約価格情報'],
    )
    type_ = st.multiselect(
        label="種類",
        options=["中古マンション等", "宅地(土地と建物)", "宅地(土地)"],
    )
    region = st.multiselect(label="地区", options=["住宅地", "工業地", "商業地"])
    municipality = st.multiselect(
        label="市区町村名",
        options=["台東区", "千代田区", "中央区"],
    )
    districtName = st.multiselect(
        label="地区名",
        options=[
            "小島",
            "上野",
            "駒形",
            "台東",
            "千束",
            "日本堤",
            "根岸",
            "東浅草",
            "東上野",
            "三ノ輪",
            "竜泉",
            "三筋",
            "浅草橋",
            "橋場",
            "北上野",
            "秋葉原",
            "浅草",
            "今戸",
            "蔵前",
            "鳥越",
            "松が谷",
            "元浅草",
            "池之端",
            "下谷",
            "上野桜木",
            "入谷",
            "雷門",
            "清川",
            "寿",
            "西浅草",
            "花川戸",
            "柳橋",
            "谷中",
            "上野公園",
            "有明",
            "永代",
            "清澄",
            "北砂",
            "新大橋",
            "高橋",
            "常盤",
            "平野",
            "深川",
            "三好",
            "森下",
            "大島",
            "亀戸",
            "豊洲",
            "枝川",
            "扇橋",
            "木場",
            "猿江",
            "潮見",
            "新木場",
            "富岡",
            "古石場",
            "冬木",
            "越中島",
            "塩浜",
            "東雲",
            "白河",
            "新砂",
            "東陽",
            "東砂",
            "牡丹",
            "南砂",
            "毛利",
            "石島",
            "千石",
            "辰巳",
            "福住",
            "門前仲町",
            "千田",
            "佐賀",
            "住吉",
            "海辺",
            "日本橋堀留町",
            "新富",
            "日本橋茅場町",
            "日本橋蛎殻町",
            "日本橋人形町",
            "日本橋馬喰町",
            "日本橋久松町",
            "日本橋室町",
            "晴海",
            "勝どき",
            "日本橋箱崎町",
            "日本橋本町",
            "銀座",
            "入船",
            "明石町",
            "日本橋大伝馬町",
            "日本橋富沢町",
            "日本橋横山町",
            "東日本橋",
            "湊",
            "日本橋浜町",
            "築地",
            "新川",
            "佃",
            "京橋",
            "月島",
            "日本橋",
            "日本橋兜町",
            "日本橋小網町",
            "日本橋中洲",
            "八丁堀",
            "日本橋小舟町",
            "八重洲",
            "日本橋小伝馬町",
            "豊海町",
            "日本橋本石町",
            "青海",
            "若洲",
        ],
    )
    trade_price = st.slider(
        label="取引価格",
        min_value=1200,
        max_value=32000000000,
        value=(1200, 32000000000),
        step=10000,
    )
    price_per_unit = st.slider(
        label="坪単価",
        min_value=24000,
        max_value=60000000,
        value=(1200, 60000000),
        step=10000,
    )
    floor_plan = st.multiselect(
        label="間取り",
        options=[
            "1R",
            "1K",
            "1LDK",
            "2LDK",
            "3DK",
            "3LDK",
            "2DK",
            "1DK",
            "1LDK+S",
            "オープンフロア",
            "2K",
            "4LDK",
            "2LDK+S",
            "スタジオ",
            "1DK+S",
            "2DK+S",
            "4DK+S",
            "3LDK+S",
            "3K",
            "4LDK+S",
            "5LDK",
            "4DK",
            "3DK+S",
            "メゾネット",
            "1K+S",
            "3LK",
            "1LK",
            "2K+S",
            "1R+S",
            "7LDK",
            "2LK+S",
            "4K",
            "1LD+S",
            "5DK",
            "5K",
            "6LDK",
            "5LDK+S",
            "3K+S",
            "6LDK+S",
        ],
    )
    area = st.slider(
        label="面積（平方メートル）",
        min_value=10,
        max_value=1000,
        value=(10, 1000),
        step=1,
    )
    unit_price = st.slider(
        label="取引価格（平方メートル単価）",
        min_value=7400,
        max_value=18000000,
        value=(7400, 18000000),
        step=1,
    )
    land_shape = st.multiselect(
        label="土地の形状",
        options=[
            "長方形",
            "不整形",
            "ほぼ長方形",
            "ほぼ正方形",
            "ほぼ整形",
            "ほぼ台形",
            "台形",
            "袋地等",
            "正方形",
        ],
    )
    frontage = st.slider(
        label="間口",
        min_value=0,
        max_value=1000,
        value=(0, 1000),
        step=1,
    )
    total_floor_area = st.slider(
        label="延床面積（平方メートル）",
        min_value=5,
        max_value=1000,
        value=(5, 1000),
        step=1,
    )
    building_year = st.slider(
        label="建築年",
        min_value=1946,
        max_value=2025,
        value=(1946, 2025),
        step=1,
    )
    structure = st.multiselect(
        label="建物の構造",
        options=[
            "SRC",
            "RC",
            "鉄骨造",
            "木造",
            "ブロック造",
            "軽量鉄骨造",
            "RC、ブロック造",
            "SRC、RC",
            "RC、鉄骨造",
            "RC、木造",
            "鉄骨造、木造",
            "RC、軽量鉄骨造",
            "RC、鉄骨造、木造",
            "ブロック造、軽量鉄骨造",
            "SRC、鉄骨造",
            "木造、軽量鉄骨造",
        ],
    )
    direction = st.multiselect(
        label="前面道路：方位",
        options=["西", "南東", "南", "東", "南西", "北", "北西", "接面道路無", "北東"],
    )
    classification = st.multiselect(
        label="前面道路：種類",
        options=[
            "区道",
            "都道",
            "私道",
            "国道",
            "道路",
            "公道",
            "町道",
            "道道",
            "村道",
            "林道",
            "市道",
            "農道",
            "区画街路",
            "県道",
        ],
    )
    breadth = st.slider(
        label="前面道路：幅員（m）",
        min_value=1,
        max_value=99,
        value=(1, 99),
        step=1,
    )
    city_planning = st.multiselect(
        label="都市計画",
        options=[
            "商業地域",
            "近隣商業地域",
            "準工業地域",
            "第１種住居地域",
            "第１種中高層住居専用地域",
            "第２種中高層住居専用地域",
            "工業地域",
            "第２種住居地域",
            "準住居地域",
            "工業専用地域",
            "第１種低層住居専用地域",
            "第２種低層住居専用地域",
        ],
    )
    coverage_ratio = st.slider(
        label="建蔽率（%）",
        min_value=50,
        max_value=90,
        value=(50, 90),
        step=10,
    )
    floor_area_ratio = st.slider(
        label="容積率（%）",
        min_value=100,
        max_value=1300,
        value=(10, 1300),
        step=10,
    )
    fr_date = st.date_input(label="取引時点: From", value="2010-03-31")
    to_date = st.date_input(label="取引時点: To", value="2024-06-30")
    renovation = st.multiselect(
        label="改装",
        options=["未改装", "改装済み"],
    )
    remarks = st.multiselect(
        label="取引の事情等",
        options=[
            "調停・競売等、私道を含む取引",
            "調停・競売等",
            "隣地の購入",
            "隣地の購入、私道を含む取引",
            "私道を含む取引",
            "関係者間取引",
            "その他事情有り",
            "関係者間取引、私道を含む取引",
            "隣地の購入、関係者間取引",
            "隣地の購入、関係者間取引、私道を含む取引",
        ],
    )

    if st.button("Search"):
        filtered_data = data
        filter_count = 0
        if price_category:
            filtered_data = duckdb.sql(make_or_cond_query("PriceCategory", price_category))
            filter_count += 1
        if type_:
            filtered_data = duckdb.sql(make_or_cond_query("Type", type_))
            filter_count += 1
        if region:
            filtered_data = duckdb.sql(make_or_cond_query("Region", region))
            filter_count += 1
        if municipality:
            filtered_data = duckdb.sql(make_or_cond_query("Municipality", municipality))
            filter_count += 1
        if districtName:
            filtered_data = duckdb.sql(make_or_cond_query("DistrictName", districtName))
            filter_count += 1
        if trade_price != (1200, 32000000000):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE TradePrice >= {trade_price[0]} AND TradePrice <= {trade_price[1]}"
            )
            filter_count += 1
        if price_per_unit != (1200, 60000000):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE PricePerUnit >= {price_per_unit[0]} AND PricePerUnit <= {price_per_unit[1]}"
            )
            filter_count += 1
        if floor_plan:
            filtered_data = duckdb.sql(make_or_cond_query("FloorPlan", floor_plan))
            filter_count += 1
        if area != (10, 1000):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE Area >= {area[0]} AND Area <= {area[1]}"
            )
            filter_count += 1
        if unit_price != (7400, 18000000):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE UnitPrice >= {unit_price[0]} AND UnitPrice <= {unit_price[1]}"
            )
            filter_count += 1
        if land_shape:
            filtered_data = duckdb.sql(make_or_cond_query("LandShape", land_shape))
            filter_count += 1
        if frontage != (0, 1000):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE Frontage >= {frontage[0]} AND Frontage <= {frontage[1]}"
            )
            filter_count += 1
        if total_floor_area != (5, 1000):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE TotalFloorArea >= {total_floor_area[0]} AND TotalFloorArea <= {total_floor_area[1]}"
            )
            filter_count += 1
        if building_year != (1946, 2025):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE BuildingYear >= {building_year[0]} AND BuildingYear <= {building_year[1]}"
            )
            filter_count += 1
        if structure:
            filtered_data = duckdb.sql(make_or_cond_query("Structure", structure))
            filter_count += 1
        if direction:
            filtered_data = duckdb.sql(make_or_cond_query("Direction", direction))
            filter_count += 1
        if classification:
            filtered_data = duckdb.sql(
                make_or_cond_query("Classification", classification)
            )
            filter_count += 1
        if breadth != (1, 99):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE Breadth >= {breadth[0]} AND Breadth <= {breadth[1]}"
            )
            filter_count += 1
        if city_planning:
            filtered_data = duckdb.sql(
                make_or_cond_query("CityPlanning", city_planning)
            )
            filter_count += 1
        if coverage_ratio != (50, 90):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE CoverageRatio >= {coverage_ratio[0]} AND CoverageRatio <= {coverage_ratio[1]}"
            )
            filter_count += 1
        if floor_area_ratio != (10, 1300):
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE FloorAreaRatio >= {floor_area_ratio[0]} AND FloorAreaRatio <= {floor_area_ratio[1]}"
            )
            filter_count += 1
        if fr_date != "2010-03-31" and to_date != "2024-06-30":
            filtered_data = duckdb.sql(
                f"SELECT * FROM filtered_data WHERE Period >= '{fr_date}' AND Period <= '{to_date}'"
            )
            filter_count += 1
        if renovation:
            filtered_data = duckdb.sql(make_or_cond_query("Renovation", renovation))
            filter_count += 1
        if remarks:
            filtered_data = duckdb.sql(make_or_cond_query("Remarks", remarks))
            filter_count += 1

        st.write(f"フィルタ数: {filter_count}")
        st.dataframe(filtered_data.to_df())


search()
