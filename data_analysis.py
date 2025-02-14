import pandas as pd
import plotly.express as px
import streamlit as st


def data_analysis_page():
    st.title("不動産データ分析")
    st.write("ここに不動産データ分析に関する詳細な内容やグラフ、解析結果などを記述してください。") 
    
    data_file = "data/data.parquet"
    try:
        df = pd.read_parquet(data_file)
        # まずは全データの 'Type'(種類) ごとの件数を棒グラフで表示
        if "Type" in df.columns:
            st.subheader("種類ごとの件数")
            # 全データから 'Type'(種類) 列の件数を集計
            type_counts = df["Type"].value_counts().reset_index()
            type_counts.columns = ["種類", "件数"]
            fig = px.bar(type_counts, x="種類", y="件数", title="種類ごとの件数")
            st.plotly_chart(fig)
            # 棒グラフ表示後、"中古マンション等" のデータのみ抽出
            df = df[df["Type"] == "中古マンション等"]
            
            # TradePrice / Area の計算で TradePricePerArea 列を追加
            if "TradePrice" in df.columns and "Area" in df.columns:
                df["TradePricePerArea"] = df["TradePrice"] / df["Area"]
            else:
                st.info("取引価格(TradePrice)または面積(Area)のカラムが見つかりません。")
        else:
            st.info("データに 'Type'(種類) カラムが見つかりません。")
        
        st.write("※ 以降のデータは中古マンション等のみとする") 
        # st.subheader("不動産データプレビュー")
        # st.write(df.head())

        # st.subheader("データ概要")
        # st.write(df.describe())
        
        st.subheader("地区ごとの件数")
        # 以前のドロップダウン形式 -> ピル風に変更
        st.markdown("### 表示するチャートを選択してください")
        col1, col2 = st.columns(2)
        treemap_selected = col1.checkbox("Treemap", value=True)
        bar_selected = col2.checkbox("棒グラフ", value=True)
        chart_options = []
        if treemap_selected:
            chart_options.append("Treemap")
        if bar_selected:
            chart_options.append("棒グラフ")
        
        # Treemap: 市区町村と地区ごとの件数を集計して可視化（件数を使用）
        if "Treemap" in chart_options:
            if "Municipality" in df.columns and "DistrictName" in df.columns:
                st.subheader("市区町村・地区ごとの件数")
                # 市区町村と地区ごとに件数を集計
                treemap_data = df.groupby(["Municipality", "DistrictName"]).size().reset_index(name="件数")
                fig_treemap = px.treemap(
                    treemap_data,
                    path=["Municipality", "DistrictName"],
                    values="件数",
                    title="件数"
                )
                st.plotly_chart(fig_treemap)
            else:
                st.info("データに 'Municipality' または 'DistrictName' カラムが見つかりません。")
        
        # 棒グラフ: DistrictNameごとの件数（降順に並べ替え）
        if "棒グラフ" in chart_options:
            if "DistrictName" in df.columns:
                st.subheader("地区ごとの件数")
                district_counts = df["DistrictName"].value_counts().reset_index()
                district_counts.columns = ["地区名", "件数"]
                district_counts = district_counts.sort_values(by="件数", ascending=False)
                fig_bar = px.bar(district_counts, x="地区名", y="件数", title="地区ごとの件数")
                st.plotly_chart(fig_bar)
            else:
                st.info("データに 'DistrictName' カラムが見つかりません。")
        if "DistrictName" in df.columns and "TradePricePerArea" in df.columns:
            st.subheader("面積当たりの取引価格")
            # DistrictNameごとにドロップダウンで表示する地区を選択
            selected_districts = st.multiselect(
                "地区を選択してください",
                options=sorted(df["DistrictName"].unique()),
                default=[
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
            )
            if selected_districts:
                filtered_df = df[df["DistrictName"].isin(selected_districts)]
                # FloorPlanのフィルタがある場合、ドロップダウンで選択
                if "FloorPlan" in df.columns:
                    selected_floorplans = st.multiselect(
                        "間取りを選択してください",
                        options=sorted(df["FloorPlan"].unique()),
                        default=sorted(df["FloorPlan"].unique())
                    )
                    if selected_floorplans:
                        filtered_df = filtered_df[filtered_df["FloorPlan"].isin(selected_floorplans)]
                # Structureのフィルタがある場合、ドロップダウンで選択
                if "Structure" in df.columns:
                    selected_structure = st.multiselect(
                        "建物構造を選択してください",
                        options=sorted(df["Structure"].unique()),
                        default=sorted(df["Structure"].unique())
                    )
                    if selected_structure:
                        filtered_df = filtered_df[filtered_df["Structure"].isin(selected_structure)]
                fig_box = px.box(filtered_df, y="TradePricePerArea", x="DistrictName", title="地区ごとの面積当たりの取引価格分布")
                st.plotly_chart(fig_box)
                if "Period" in filtered_df.columns:
                    # ドロップダウンから線グラフ用のDistrictNameを選択する
                    available_districts = sorted(filtered_df["DistrictName"].unique())
                    selected_line_district = st.selectbox(
                        "線グラフ用の地区を選択してください",
                        options=available_districts,
                        index= available_districts.index("日本橋横山町") if "日本橋横山町" in available_districts else 0
                    )
                    line_df = filtered_df[filtered_df["DistrictName"]==selected_line_district]
                    # 線グラフ用のFloorPlanフィルタを追加
                    if "FloorPlan" in filtered_df.columns:
                        selected_line_floorplans = st.multiselect(
                            "線グラフ用の間取りを選択してください",
                            options=sorted(filtered_df["FloorPlan"].unique()),
                            default=sorted(filtered_df["FloorPlan"].unique())
                        )
                        if selected_line_floorplans:
                            line_df = line_df[line_df["FloorPlan"].isin(selected_line_floorplans)]
                    # 線グラフ用のStructureフィルタを追加
                    if "Structure" in filtered_df.columns:
                        selected_line_structure = st.multiselect(
                            "線グラフ用の建物構造を選択してください",
                            options=sorted(filtered_df["Structure"].unique()),
                            default=sorted(filtered_df["Structure"].unique())
                        )
                        if selected_line_structure:
                            line_df = line_df[line_df["Structure"].isin(selected_line_structure)]
                    line_df = line_df.sort_values(by="Period")
                    if not line_df.empty:
                        fig_line = px.box(line_df, x="Period", y="TradePricePerArea", title=f"地区ごとの面積当たりの取引価格の時系列分布 ({selected_line_district})")
                        st.plotly_chart(fig_line)
                    else:
                        st.info(f"'{selected_line_district}' のデータがありません。")
                else:
                    st.info("データに 'Period' カラムが見つかりません。")
            else:
                st.info("少なくとも1つの地区を選択してください。")
        else:
            st.info("データに 'DistrictName' または 'TradePricePerArea' カラムが見つかりません。")
    except FileNotFoundError:
        st.error(f"{data_file}が見つかりません。ファイルパスを確認してください。")
    except Exception as e:
        st.error(f"データ読み込み中にエラーが発生しました: {e}")
