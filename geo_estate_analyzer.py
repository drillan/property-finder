from datetime import datetime, timedelta

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium


def geo_estate_analyzer():
    st.title("不動産データ分析マップ")
    st.write("地図をクリックして緯度経度を取得")

    # セッション状態の初期化
    if 'locations' not in st.session_state:
        st.session_state.locations = []
    if 'input_lat' not in st.session_state:
        st.session_state.input_lat = 35.691953
    if 'input_lng' not in st.session_state:
        st.session_state.input_lng = 139.781719
    if 'geojson_data' not in st.session_state:
        st.session_state.geojson_data = None
    if 'df' not in st.session_state:
        st.session_state.df = None

    # コントロールをメインページに配置
    col_zoom, col_quarter = st.columns(2)
    
    # 緯度経度入力欄を追加
    col_lat, col_lng = st.columns(2)
    with col_lat:
        st.session_state.input_lat = st.number_input(
            "緯度",
            value=st.session_state.input_lat,
            min_value=-90.0,
            max_value=90.0,
            format="%.6f",
            help="緯度を入力（例：35.691953）"
        )
    with col_lng:
        st.session_state.input_lng = st.number_input(
            "経度",
            value=st.session_state.input_lng,
            min_value=-180.0,
            max_value=180.0,
            format="%.6f",
            help="経度を入力（例：139.781719）"
        )

    with col_zoom:
        # ズームレベルのスライダー
        zoom_level = st.slider(
            "ズームレベル",
            min_value=10,
            max_value=18,
            value=14,
            help="地図のズームレベルを選択"
        )

    with col_quarter:
        # 四半期の範囲スライダー
        current_year = datetime.now().year
        quarters = [f"{year}{quarter}" for year in range(2010, current_year + 1) 
                   for quarter in range(1, 5)]
        
        default_from_idx = len(quarters) - 12
        default_to_idx = len(quarters) - 1
        
        selected_range = st.select_slider(
            "四半期範囲",
            options=quarters,
            value=(quarters[default_from_idx], quarters[default_to_idx]),
            help="データを取得する四半期範囲を選択（例：20101は2010年第1四半期）"
        )
        from_date, to_date = selected_range

    # リセットボタンを追加
    col1, col2 = st.columns(2)
    with col1:
        if st.button("データをリセット", key="reset_button"):
            st.session_state.markers = []
            st.session_state.geojson_data = None
            st.session_state.df = None
            st.rerun()
    with col2:
        if st.button('データを取得', key="fetch_button"):
            try:
                from real_estate_data_processor import GeoJsonDownloader
                downloader = GeoJsonDownloader()
                st.session_state.geojson_data = downloader.get_geojson(
                    lat=st.session_state.input_lat,
                    lon=st.session_state.input_lng,
                    zoom=zoom_level,
                    from_date=from_date,
                    to_date=to_date
                )

                # GeoJSONデータをDataFrameに変換
                from real_estate_data_processor import GeoJsonProcessor
                processor = GeoJsonProcessor()
                st.session_state.df = processor.process_geojson(st.session_state.geojson_data)

                # マーカー情報を更新
                if isinstance(st.session_state.geojson_data, dict) and 'features' in st.session_state.geojson_data:
                    st.session_state.markers = []  # マーカーをリセット
                    for feature in st.session_state.geojson_data['features']:
                        if feature['geometry']['type'] == 'Point':
                            lng, lat = feature['geometry']['coordinates']
                            properties = feature['properties']
                            popup_content = '<br>'.join([
                                f"<b>{k}</b>: {v}" for k, v in properties.items()
                            ])
                            marker_info = {
                                'lat': lat,
                                'lng': lng,
                                'popup': popup_content
                            }
                            st.session_state.markers.append(marker_info)
                st.rerun()

            except Exception as e:
                st.error(f"データの取得中にエラーが発生しました: {str(e)}")

    # データが存在する場合、JSONと箱ひげ図を表示
    if st.session_state.geojson_data is not None:
        st.json(st.session_state.geojson_data)

        if st.session_state.df is not None and not st.session_state.df.empty and not st.session_state.df['price_per_area'].isna().all():
            fig = px.box(
                st.session_state.df,
                x='period',
                y='price_per_area',
                title='期間ごとの単位面積あたりの価格分布',
                labels={
                    'price_per_area': '単位面積あたりの価格（円/㎡）',
                    'period': '期間'
                },
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                margin=dict(t=50, b=50),
                xaxis_tickangle=45
            )
            st.plotly_chart(fig, use_container_width=True)

    # 地図の作成（入力された緯度経度を中心に）
    m = folium.Map(
        location=[st.session_state.input_lat, st.session_state.input_lng],
        zoom_start=zoom_level,
        control_scale=True,  # スケールを表示
        zoom_control=True    # ズームコントロールを表示
    )

    # MarkerClusterを作成
    marker_cluster = folium.plugins.MarkerCluster(
        options={
            'maxClusterRadius': 30,  # クラスター化する距離の閾値を小さく
            'disableClusteringAtZoom': 16,  # より高いズームレベルでクラスター化を無効化
            'spiderfyOnMaxZoom': True,  # 最大ズーム時にマーカーを展開表示
            'showCoverageOnHover': True,  # クラスターの範囲を表示
            'zoomToBoundsOnClick': True  # クリック時にクラスター内のマーカーが見えるようにズーム
        }
    ).add_to(m)

    # 既存のマーカーを表示
    if 'markers' in st.session_state:
        for marker_data in st.session_state.markers:
            folium.Marker(
                location=[marker_data['lat'], marker_data['lng']],
                popup=folium.Popup(marker_data['popup'], max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)  # マーカーをクラスターに追加

    # 地図の表示とクリックイベントの取得
    map_data = st_folium(
        m,
        height=600,
        width="100%",
        returned_objects=["last_clicked"],
        key="map",
        use_container_width=True
    )

    # クリックイベントの処理
    if map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lng = map_data['last_clicked']['lng']
        
        # 入力フィールドの値を更新
        st.session_state.input_lat = lat
        st.session_state.input_lng = lng
        st.rerun()


if __name__ == "__main__":
    geo_estate_analyzer()
