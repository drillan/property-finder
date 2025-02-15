import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# 定数
DEFAULT_DISTRICTS = [
    "浅草橋",
    "柳橋",
    "岩本町",
    "東神田",
    "神田和泉町",
    "日本橋堀留町",
    "日本橋茅場町",
    "日本橋蛎殻町",
    "日本橋人形町",
    "日本橋馬喰町",
    "日本橋久松町",
    "日本橋室町",
    "日本橋箱崎町",
    "日本橋本町",
    "日本橋大伝馬町",
    "日本橋富沢町",
    "日本橋横山町",
    "東日本橋",
    "日本橋浜町",
    "日本橋兜町",
    "日本橋小網町",
    "日本橋中洲",
    "日本橋小舟町",
    "日本橋小伝馬町",
    "神田富山町",
    "神田神保町",
    "神田佐久間町",
    "神田多町",
    "神田司町",
    "神田練塀町",
    "神田錦町",
    "内神田",
    "神田淡路町",
    "神田駿河台",
    "西神田",
    "東神田",
    "神田三崎町",
    "神田和泉町",
    "神田小川町",
    "神田須田町",
    "外神田",
    "神田猿楽町",
    "神田東松下町",
    "神田東紺屋町",
    "神田鍛冶町",
    "神田美土代町",
]

LIMIT_ROWS = 10000  # データ抽出時の行数制限

def get_sorted_unique_values(rel, column) -> list:
    """
    指定されたカラムからDataFrameのユニークな値をソート済みで取得する。
    """
    try:
        if column in rel.columns:
            unique_df = rel.project(column).distinct().order(column).df()
            return unique_df[column].tolist()
    except Exception as e:
        st.error(f"Error retrieving unique values for {column}: {e}")
    return []

def apply_in_filter(rel, column, values):
    """
    指定されたカラムに対してINフィルタを適用する。
    valuesが空でなければフィルタを適用し、そうでなければそのままのrelationを返す。
    """
    if values:
        values_str = ", ".join(f"'{v}'" for v in values)
        return rel.filter(f"{column} IN ({values_str})")
    return rel

def filter_used_mansions(rel):
    """
    "中古マンション等" のみを抽出したrelationを返す。
    """
    if "Type" in rel.columns:
        return rel.filter("Type = '中古マンション等'")
    st.info("データに 'Type'(種類) カラムが見つかりません。")
    return rel

def compute_tradeprice_per_area(rel):
    """
    取引価格(TradePrice)と面積(Area)から面積当たりの取引価格(TradePricePerArea)を計算する。
    """
    if "TradePrice" in rel.columns and "Area" in rel.columns:
        return rel.project("*, TradePrice / Area as TradePricePerArea")
    st.info("取引価格(TradePrice)または面積(Area)のカラムが見つかりません。")
    return rel

def render_treemap_chart(df):
    """
    Treemapチャートを描画するヘルパー関数
    """
    fig_treemap = px.treemap(
        df,
        path=["Municipality", "DistrictName"],
        title="件数"
    )
    st.plotly_chart(fig_treemap)

def render_bar_chart_chart(df):
    """
    棒グラフチャートを描画するヘルパー関数
    """
    fig_bar = px.bar(df, x="地区名", y="件数", title="地区ごとの件数")
    st.plotly_chart(fig_bar)

def plot_district_count_charts(rel):
    """
    Treemapと棒グラフで地区ごとの件数を表示する。
    """
    st.subheader("地区ごとの件数")
    st.markdown("### 表示するチャートを選択してください")
    col1, col2 = st.columns(2)
    treemap_selected = col1.checkbox("Treemap", value=True)
    bar_selected = col2.checkbox("棒グラフ", value=True)
    
    if treemap_selected:
        if "Municipality" in rel.columns and "DistrictName" in rel.columns:
            st.subheader("市区町村・地区ごとの件数")
            treemap_df = rel.df()
            render_treemap_chart(treemap_df)
        else:
            st.info("データに 'Municipality' または 'DistrictName' カラムが見つかりません。")
    
    if bar_selected:
        if "DistrictName" in rel.columns:
            st.subheader("地区ごとの件数")
            district_counts_rel = rel.aggregate("COUNT(*) AS 件数, DistrictName AS 地区名", "DistrictName")\
                                     .order("件数 DESC")
            district_counts_df = district_counts_rel.df()
            render_bar_chart_chart(district_counts_df)
        else:
            st.info("データに 'DistrictName' カラムが見つかりません。")

def draw_tradeprice_box_chart(filtered_rel):
    """
    フィルタ済みrelationから箱ひげ図（TradePricePerAreaの分布）を描画する。
    """
    rel_to_plot = filtered_rel
    if "Period" in filtered_rel.columns:
        # 集約クエリを使用して、Periodの範囲を効率的に取得する
        period_range_df = filtered_rel.aggregate("MIN(Period) as min_period, MAX(Period) as max_period").df()
        min_period = period_range_df["min_period"].iloc[0]
        max_period = period_range_df["max_period"].iloc[0]
        try:
            if isinstance(min_period, pd.Timestamp):
                min_period = min_period.to_pydatetime()
            if isinstance(max_period, pd.Timestamp):
                max_period = max_period.to_pydatetime()
        except Exception as e:
            st.error(f"Error converting Timestamp: {e}")
        selected_period_range = st.slider(
            "Periodでフィルタリング",
            min_value=min_period,
            max_value=max_period,
            value=(min_period, max_period)
        )
        # 新しい変数にフィルタを適用
        rel_to_plot = filtered_rel.filter(
            f"Period >= '{selected_period_range[0]}' AND Period <= '{selected_period_range[1]}'"
        )
        
    box_df = rel_to_plot.limit(LIMIT_ROWS).df()

    group_by_options = ["DistrictName"]
    if "Period" in box_df.columns:
        group_by_options.append("Period")
    
    selected_group_by = st.radio(
        "箱ひげ図のグループ化カラムを選択してください",
        options=group_by_options,
        index=0
    )
    
    fig_box = px.box(
        box_df,
        y="TradePricePerArea",
        x=selected_group_by,
        title=f"{selected_group_by}ごとの面積当たりの取引価格分布"
    )
    st.plotly_chart(fig_box)

def draw_tradeprice_time_series_chart(filtered_rel, available_districts):
    """
    フィルタ済みrelationから時系列の箱ひげ図（地区ごとのTradePricePerAreaの時系列分布）を描画する。
    """
    if "Period" not in filtered_rel.columns:
        st.info("データに 'Period' カラムが見つかりません。")
        return

    available_ts_districts = available_districts if available_districts else DEFAULT_DISTRICTS
    selected_line_districts = st.multiselect(
        "線グラフ用の地区を選択してください",
        options=available_ts_districts,
        default=["日本橋横山町", "東日本橋"]
    )
    ts_rel = apply_in_filter(filtered_rel, "DistrictName", selected_line_districts)
    ts_rel = ts_rel.order("Period")
    line_df = ts_rel.limit(LIMIT_ROWS).df()
    if not line_df.empty:
        fig_time_series = px.box(
            line_df,
            x="Period",
            y="TradePricePerArea",
            color="DistrictName",
            title=f"地区ごとの面積当たりの取引価格の時系列分布 ({', '.join(selected_line_districts)})"
        )
        st.plotly_chart(fig_time_series)
    else:
        st.info(f"選択された地区({', '.join(selected_line_districts)})のデータがありません。")

def plot_tradeprice_area_charts(rel):
    """
    全体の面積当たりの取引価格の箱ひげ図と、期間別の時系列箱ひげ図を表示する。
    また、間取り(FloorPlan)および建物構造(Structure)によるフィルタも適用可能とする。
    """
    if "DistrictName" not in rel.columns or "TradePricePerArea" not in rel.columns:
        st.info("データに 'DistrictName' または 'TradePricePerArea' カラムが見つかりません。")
        return

    st.subheader("面積当たりの取引価格")
    unique_districts = get_sorted_unique_values(rel, "DistrictName")
    selected_districts = st.multiselect(
        "地区を選択してください",
        options=unique_districts if unique_districts else DEFAULT_DISTRICTS,
        default=DEFAULT_DISTRICTS
    )
    if not selected_districts:
        st.info("少なくとも1つの地区を選択してください。")
        return

    filtered_rel = apply_in_filter(rel, "DistrictName", selected_districts)
    
    if "FloorPlan" in rel.columns:
        unique_floorplans = get_sorted_unique_values(rel, "FloorPlan")
        selected_floorplans = st.multiselect(
            "間取りを選択してください",
            options=unique_floorplans,
            default=unique_floorplans
        )
        filtered_rel = apply_in_filter(filtered_rel, "FloorPlan", selected_floorplans)
        
    if "Structure" in rel.columns:
        unique_structures = get_sorted_unique_values(rel, "Structure")
        selected_structures = st.multiselect(
            "建物構造を選択してください",
            options=unique_structures,
            default=unique_structures
        )
        filtered_rel = apply_in_filter(filtered_rel, "Structure", selected_structures)
    
    st.write("【箱ひげ図】")
    draw_tradeprice_box_chart(filtered_rel)
    
    st.write("【時系列箱ひげ図】")
    draw_tradeprice_time_series_chart(filtered_rel, selected_districts)

def data_analysis_page():
    st.title("不動産データ分析")
    data_file = "data/data.parquet"
    try:
        # DuckDBを利用してrelationオブジェクトを取得する
        rel = duckdb.sql(f"SELECT * FROM '{data_file}'")
        rel = filter_used_mansions(rel)
        rel = compute_tradeprice_per_area(rel)
        st.write("※ 以降のデータは中古マンション等のみとする")
        plot_district_count_charts(rel)
        plot_tradeprice_area_charts(rel)
    except FileNotFoundError:
        st.error(f"{data_file} が見つかりません。ファイルパスを確認してください。")
    except Exception as e:
        st.error(f"データ読み込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    data_analysis_page()
