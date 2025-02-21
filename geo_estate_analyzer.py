from datetime import datetime, timedelta

import folium
import streamlit as st
from streamlit_folium import st_folium


def geo_estate_analyzer():
    st.title("地図クリックアプリ")
    st.write("地図をクリックして緯度経度を取得")

    # セッション状態の初期化
    if 'locations' not in st.session_state:
        st.session_state.locations = []

    # サイドバーにコントロールを追加
    with st.sidebar:
        # ズームレベルのスライダー
        zoom_level = st.slider(
            "ズームレベル",
            min_value=10,
            max_value=18,
            value=14,
            help="地図のズームレベルを選択"
        )

        # 四半期の範囲スライダー
        current_year = datetime.now().year
        quarters = [f"{year}{quarter}" for year in range(2010, current_year + 1) 
                   for quarter in range(1, 5)]
        
        default_from_idx = len(quarters) - 5  # デフォルトは直近5四半期前から
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
        control_scale=True  # スケールを表示
    )

    # 地図の表示とクリックイベントの取得
    map_data = st_folium(
        m,
        height=600,
        width="100%",
        returned_objects=["last_clicked"],
        key="map"
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
            st.json(geojson_data)
        except Exception as e:
            st.error(f"GeoJsonデータの取得中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    geo_estate_analyzer()
