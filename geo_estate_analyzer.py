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

    # リセットボタンを追加
    col1, col2 = st.columns(2)
    with col1:
        if st.button("マーカーをリセット", key="reset_button"):
            st.session_state.markers = []
            st.rerun()
    with col2:
        if st.button('マーカーを更新', key="update_button"):
            st.rerun()

    # コントロールをメインページに配置
    col_zoom, col_quarter = st.columns(2)
    
    with col_zoom:
        # ズームレベルのスライダー
        zoom_level = st.slider(
            "ズームレベル",
            min_value=10,  # より広域から
            max_value=18,  # より詳細まで
            value=14,
            help="地図のズームレベルを選択"
        )

    with col_quarter:
        # 四半期の範囲スライダー
        current_year = datetime.now().year
        quarters = [f"{year}{quarter}" for year in range(2010, current_year + 1) 
                   for quarter in range(1, 5)]
        
        default_from_idx = len(quarters) - 12  # デフォルトは直近5四半期前から
        default_to_idx = len(quarters) - 1    # 最新の四半期まで
        
        selected_range = st.select_slider(
            "四半期範囲",
            options=quarters,
            value=(quarters[default_from_idx], quarters[default_to_idx]),
            help="データを取得する四半期範囲を選択（例：20101は2010年第1四半期）"
        )
        from_date, to_date = selected_range

    # 地図の作成（東京を中心に）
    m = folium.Map(
        location=[35.691953, 139.781719],
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
        
        # 新しい位置情報を追加
        new_location = {'lat': lat, 'lng': lng}
        if new_location not in st.session_state.locations:
            st.session_state.locations.append(new_location)
        
        # クリックした位置の情報を表示
        col1, col2 = st.columns(2)
        with col1:
            st.write("緯度", f"{lat:.6f}")
        with col2:
            st.write("経度", f"{lng:.6f}")

        # GeoJsonDownloaderの結果を表示
        try:
            from real_estate_data_processor import GeoJsonDownloader
            downloader = GeoJsonDownloader()
            geojson_data = downloader.get_geojson(
                lat=lat,
                lon=lng,
                zoom=zoom_level,
                from_date=from_date,  # 四半期コード（例：20101）
                to_date=to_date      # 四半期コード（例：20234）
            )
            
            # GeoJSONデータをJSONとして表示
            st.json(geojson_data)

            # GeoJSONデータをDataFrameに変換
            from real_estate_data_processor import GeoJsonProcessor
            processor = GeoJsonProcessor()
            df = processor.process_geojson(geojson_data)

            # 箱ひげ図の作成と表示
            if not df.empty and not df['price_per_area'].isna().all():
                fig = px.box(
                    df,
                    x='period',  # periodをx軸に設定
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
                    xaxis_tickangle=45  # x軸のラベルを45度傾ける
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # セッション状態にマーカー情報を初期化
            if 'markers' not in st.session_state:
                st.session_state.markers = []

            # GeoJSONの各フィーチャーをマーカーとして追加
            if isinstance(geojson_data, dict) and 'features' in geojson_data:
                for feature in geojson_data['features']:
                    if feature['geometry']['type'] == 'Point':
                        lng, lat = feature['geometry']['coordinates']
                        properties = feature['properties']
                        
                        # プロパティから表示用のポップアップ内容を作成
                        popup_content = '<br>'.join([
                            f"<b>{k}</b>: {v}" for k, v in properties.items()
                        ])
                        
                        # マーカー情報をセッションに保存
                        marker_info = {
                            'lat': lat,
                            'lng': lng,
                            'popup': popup_content
                        }
                        if marker_info not in st.session_state.markers:
                            st.session_state.markers.append(marker_info)
                            # 新しいマーカーを地図に直接追加
                            folium.Marker(
                                location=[lat, lng],
                                popup=folium.Popup(popup_content, max_width=300),
                                icon=folium.Icon(color='red', icon='info-sign')
                            ).add_to(marker_cluster)  # マーカーをクラスターに追加
                
                # 地図を再読み込みするためのボタン
                if st.button('マーカーを更新'):
                    st.rerun()

        except Exception as e:
            st.error(f"GeoJsonデータの取得中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    geo_estate_analyzer()
