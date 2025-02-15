import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


def plot_type_counts(rel):
    """
    Plot type counts and filter data for "中古マンション等".
    rel は DuckDBPyRelation オブジェクトとする
    """
    if "Type" in rel.columns:
        st.subheader("種類ごとの件数")
        # relation の groupby と aggregate を使って集計
        type_counts_rel = (
            rel.aggregate("COUNT(*) AS 件数, Type AS 種類", "Type")
               .order("件数 DESC")
        )
        type_counts_df = type_counts_rel.df()
        fig = px.bar(type_counts_df, x="種類", y="件数", title="種類ごとの件数")
        st.plotly_chart(fig)
        # filter() を使って "中古マンション等" に絞り込み
        filtered_rel = rel.filter("Type = '中古マンション等'")
        return filtered_rel
    else:
        st.info("データに 'Type'(種類) カラムが見つかりません。")
        return rel


def compute_tradeprice_per_area(rel):
    """
    Compute TradePricePerArea as TradePrice / Area.
    rel は DuckDBPyRelation オブジェクトとする
    """
    if "TradePrice" in rel.columns and "Area" in rel.columns:
        # select() で全列(*)に加え新規計算列を追加する
        new_rel = rel.project("*, TradePrice / Area as TradePricePerArea")
        return new_rel
    else:
        st.info("取引価格(TradePrice)または面積(Area)のカラムが見つかりません。")
        return rel


def plot_district_count_charts(rel):
    """
    Display district counts using Treemap and Bar Chart options.
    rel は DuckDBPyRelation オブジェクトとする
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
    
    # Treemap Chart
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
    
    # Bar Chart
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
    Display overall TradePricePerArea box plot and a time-series (Period-based) box plot 
    with additional filters for FloorPlan and Structure.
    rel は DuckDBPyRelation オブジェクトとする
    """
    if "DistrictName" in rel.columns and "TradePricePerArea" in rel.columns:
        st.subheader("面積当たりの取引価格")
        # unique な DistrictName を取得
        data_df = rel.df()
        unique_districts = sorted(set(data_df["DistrictName"])) if "DistrictName" in data_df else []
        
        selected_districts = st.multiselect(
            "地区を選択してください",
            options=unique_districts,
            default=[
                "浅草橋", "柳橋", "岩本町", "東神田", "神田和泉町",
                "日本橋堀留町", "日本橋茅場町", "日本橋蛎殻町", "日本橋人形町",
                "日本橋馬喰町", "日本橋久松町", "日本橋室町", "日本橋箱崎町",
                "日本橋本町", "日本橋大伝馬町", "日本橋富沢町", "日本橋横山町",
                "東日本橋", "日本橋浜町", "日本橋兜町", "日本橋小網町",
                "日本橋中洲", "日本橋小舟町", "日本橋小伝馬町", "神田富山町",
                "神田神保町", "神田佐久間町", "神田多町", "神田司町",
                "神田練塀町", "神田錦町", "内神田", "神田淡路町",
                "神田駿河台", "西神田", "東神田", "神田三崎町",
                "神田和泉町", "神田小川町", "神田須田町", "外神田",
                "神田猿楽町", "神田東松下町", "神田東紺屋町", "神田鍛冶町",
                "神田美土代町",
            ]
        )
        if selected_districts:
            # 複数条件は filter() を順次チェーン
            filtered_rel = rel.filter(
                "DistrictName IN ({})".format(
                    ", ".join("'" + d + "'" for d in selected_districts)
                )
            )
            # FloorPlanフィルタ
            if "FloorPlan" in rel.columns:
                data_df = rel.df()
                unique_floorplans = sorted(set(data_df["FloorPlan"])) if "FloorPlan" in data_df else []
                selected_floorplans = st.multiselect(
                    "間取りを選択してください",
                    options=unique_floorplans,
                    default=unique_floorplans
                )
                if selected_floorplans:
                    filtered_rel = filtered_rel.filter(
                        "FloorPlan IN ({})".format(
                            ", ".join("'" + fp + "'" for fp in selected_floorplans)
                        )
                    )
            # Structureフィルタ
            if "Structure" in rel.columns:
                data_df = rel.df()
                unique_structures = sorted(set(data_df["Structure"])) if "Structure" in data_df else []
                selected_structure = st.multiselect(
                    "建物構造を選択してください",
                    options=unique_structures,
                    default=unique_structures
                )
                if selected_structure:
                    filtered_rel = filtered_rel.filter(
                        "Structure IN ({})".format(
                            ", ".join("'" + s + "'" for s in selected_structure)
                        )
                    )
            box_df = filtered_rel.df()
            fig_box = px.box(box_df, y="TradePricePerArea", x="DistrictName", title="地区ごとの面積当たりの取引価格分布")
            st.plotly_chart(fig_box)
            
            # 時系列分析（Period カラム）の箱ひげ図
            data_df = filtered_rel.df()
            if "Period" in data_df:
                available_districts = sorted(set(data_df["DistrictName"]))
                default_index = available_districts.index("日本橋横山町") if "日本橋横山町" in available_districts else 0
                selected_line_district = st.selectbox(
                    "線グラフ用の地区を選択してください",
                    options=available_districts,
                    index=default_index
                )
                line_rel = filtered_rel.filter("DistrictName = '{}'".format(selected_line_district))
                # 時系列用 FloorPlanフィルタ
                if "FloorPlan" in rel.columns:
                    unique_line_floorplans = sorted(set(filtered_rel.df()["FloorPlan"]))
                    selected_line_floorplans = st.multiselect(
                        "線グラフ用の間取りを選択してください",
                        options=unique_line_floorplans,
                        default=unique_line_floorplans
                    )
                    if selected_line_floorplans:
                        line_rel = line_rel.filter(
                            "FloorPlan IN ({})".format(
                                ", ".join("'" + fp + "'" for fp in selected_line_floorplans)
                            )
                        )
                # 時系列用 Structureフィルタ
                if "Structure" in rel.columns:
                    unique_line_structures = sorted(set(filtered_rel.df()["Structure"]))
                    selected_line_structure = st.multiselect(
                        "線グラフ用の建物構造を選択してください",
                        options=unique_line_structures,
                        default=unique_line_structures
                    )
                    if selected_line_structure:
                        line_rel = line_rel.filter(
                            "Structure IN ({})".format(
                                ", ".join("'" + s + "'" for s in selected_line_structure)
                            )
                        )
                line_rel = line_rel.order("Period")
                line_df = line_rel.df()
                # 結果が存在するかの簡易チェック: DataFrameが空でないかを確認
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
        # duckdb.sql でリレーションオブジェクトを取得（DataFrame への変換は行わない）
        rel = duckdb.sql(f"SELECT * FROM '{data_file}'")
        
        # Plot type counts and filter data for "中古マンション等"
        rel = plot_type_counts(rel)
        # Compute TradePricePerArea
        rel = compute_tradeprice_per_area(rel)
        
        st.write("※ 以降のデータは中古マンション等のみとする")
        
        # Display district charts (Treemap and Bar Chart)
        plot_district_count_charts(rel)
        
        # Display TradePricePerArea analysis with overall and time series charts
        plot_tradeprice_area_charts(rel)
        
    except FileNotFoundError:
        st.error(f"{data_file} が見つかりません。ファイルパスを確認してください。")
    except Exception as e:
        st.error(f"データ読み込み中にエラーが発生しました: {e}")


if __name__ == "__main__":
    data_analysis_page()
