import duckdb
import plotly.express as px
import streamlit as st

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


def get_unique_values(rel, column):
    """
    指定されたカラムからDataFrameのユニークな値をソート済みで取得する。
    """
    try:
        if column in rel.columns:
            distinct_rel = rel.project(column).distinct().order(column)
            unique_df = distinct_rel.df()
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


def plot_type_counts(rel):
    """
    "種類ごとの件数" を棒グラフで表示し、"中古マンション等" のみフィルタしたrelationを返す。
    """
    if "Type" in rel.columns:
        st.subheader("種類ごとの件数")
        type_counts_rel = (
            rel.aggregate("COUNT(*) AS 件数, Type AS 種類", "Type")
               .order("件数 DESC")
        )
        type_counts_df = type_counts_rel.df()
        fig = px.bar(type_counts_df, x="種類", y="件数", title="種類ごとの件数")
        st.plotly_chart(fig)
        # "中古マンション等" にフィルタ
        return rel.filter("Type = '中古マンション等'")
    else:
        st.info("データに 'Type'(種類) カラムが見つかりません。")
        return rel


def compute_tradeprice_per_area(rel):
    """
    取引価格(TradePrice)と面積(Area)から面積当たりの取引価格(TradePricePerArea)を計算する。
    """
    if "TradePrice" in rel.columns and "Area" in rel.columns:
        return rel.project("*, TradePrice / Area as TradePricePerArea")
    else:
        st.info("取引価格(TradePrice)または面積(Area)のカラムが見つかりません。")
        return rel


def plot_district_count_charts(rel):
    """
    Treemapと棒グラフで地区ごとの件数を表示する。
    """
    st.subheader("地区ごとの件数")
    st.markdown("### 表示するチャートを選択してください")
    col1, col2 = st.columns(2)
    treemap_selected = col1.checkbox("Treemap", value=True)
    bar_selected = col2.checkbox("棒グラフ", value=True)
    chart_options = []
    if treemap_selected:
        chart_options.append("Treemap")
    if bar_selected:
        chart_options.append("棒グラフ")

    # Treemapチャート
    if "Treemap" in chart_options:
        if "Municipality" in rel.columns and "DistrictName" in rel.columns:
            st.subheader("市区町村・地区ごとの件数")
            treemap_df = rel.df()
            fig_treemap = px.treemap(
                treemap_df,
                path=["Municipality", "DistrictName"],
                title="件数"
            )
            st.plotly_chart(fig_treemap)
        else:
            st.info("データに 'Municipality' または 'DistrictName' カラムが見つかりません。")

    # 棒グラフチャート
    if "棒グラフ" in chart_options:
        if "DistrictName" in rel.columns:
            st.subheader("地区ごとの件数")
            district_counts_rel = rel.aggregate("COUNT(*) AS 件数, DistrictName AS 地区名", "DistrictName").order("件数 DESC")
            district_counts_df = district_counts_rel.df()
            fig_bar = px.bar(district_counts_df, x="地区名", y="件数", title="地区ごとの件数")
            st.plotly_chart(fig_bar)
        else:
            st.info("データに 'DistrictName' カラムが見つかりません。")


def plot_tradeprice_area_charts(rel):
    """
    全体の面積当たりの取引価格の箱ひげ図と、期間別の時系列箱ひげ図を表示する。
    また、間取り(FloorPlan)および建物構造(Structure)によるフィルタも適用可能とする。
    """
    if "DistrictName" in rel.columns and "TradePricePerArea" in rel.columns:
        st.subheader("面積当たりの取引価格")
        unique_districts = get_unique_values(rel, "DistrictName")
        selected_districts = st.multiselect(
            "地区を選択してください",
            options=unique_districts if unique_districts else DEFAULT_DISTRICTS,
            default=DEFAULT_DISTRICTS
        )
        if selected_districts:
            filtered_rel = apply_in_filter(rel, "DistrictName", selected_districts)
            if "FloorPlan" in rel.columns:
                unique_floorplans = get_unique_values(rel, "FloorPlan")
                selected_floorplans = st.multiselect(
                    "間取りを選択してください",
                    options=unique_floorplans,
                    default=unique_floorplans
                )
                filtered_rel = apply_in_filter(filtered_rel, "FloorPlan", selected_floorplans)
            if "Structure" in rel.columns:
                unique_structures = get_unique_values(rel, "Structure")
                selected_structures = st.multiselect(
                    "建物構造を選択してください",
                    options=unique_structures,
                    default=unique_structures
                )
                filtered_rel = apply_in_filter(filtered_rel, "Structure", selected_structures)
            
            box_df = filtered_rel.df()
            fig_box = px.box(
                box_df, y="TradePricePerArea", x="DistrictName",
                title="地区ごとの面積当たりの取引価格分布"
            )
            st.plotly_chart(fig_box)
            
            # 時系列分析（Periodカラム）による箱ひげ図
            data_df = filtered_rel.df()
            if "Period" in data_df.columns:
                available_districts = sorted(set(data_df["DistrictName"]))
                default_index = available_districts.index("日本橋横山町") if "日本橋横山町" in available_districts else 0
                selected_line_district = st.selectbox(
                    "線グラフ用の地区を選択してください",
                    options=available_districts,
                    index=default_index
                )
                line_rel = filtered_rel.filter(f"DistrictName = '{selected_line_district}'")
                if "FloorPlan" in rel.columns:
                    unique_line_floorplans = get_unique_values(filtered_rel, "FloorPlan")
                    selected_line_floorplans = st.multiselect(
                        "線グラフ用の間取りを選択してください",
                        options=unique_line_floorplans,
                        default=unique_line_floorplans
                    )
                    line_rel = apply_in_filter(line_rel, "FloorPlan", selected_line_floorplans)
                if "Structure" in rel.columns:
                    unique_line_structures = get_unique_values(filtered_rel, "Structure")
                    selected_line_structures = st.multiselect(
                        "線グラフ用の建物構造を選択してください",
                        options=unique_line_structures,
                        default=unique_line_structures
                    )
                    line_rel = apply_in_filter(line_rel, "Structure", selected_line_structures)
                line_rel = line_rel.order("Period")
                line_df = line_rel.df()
                if not line_df.empty:
                    fig_line = px.box(
                        line_df, x="Period", y="TradePricePerArea",
                        title=f"地区ごとの面積当たりの取引価格の時系列分布 ({selected_line_district})"
                    )
                    st.plotly_chart(fig_line)
                else:
                    st.info(f"'{selected_line_district}' のデータがありません。")
            else:
                st.info("データに 'Period' カラムが見つかりません。")
        else:
            st.info("少なくとも1つの地区を選択してください。")
    else:
        st.info("データに 'DistrictName' または 'TradePricePerArea' カラムが見つかりません。")


def data_analysis_page():
    st.title("不動産データ分析")
    data_file = "data/data.parquet"
    try:
        # DuckDBを利用してrelationオブジェクトを取得する
        rel = duckdb.sql(f"SELECT * FROM '{data_file}'")
        rel = plot_type_counts(rel)
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
