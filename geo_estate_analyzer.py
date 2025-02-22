from datetime import datetime, timedelta

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium

from components.ui_components import (
    render_action_buttons,
    render_control_panel,
    render_location_inputs,
)


class GeoEstateAnalyzer:
    def __init__(self):
        self._initialize_session_state()
        
    def _initialize_session_state(self):
        """セッション状態の初期化"""
        if 'locations' not in st.session_state or st.session_state.get('reset_clicked', False):
            st.session_state.locations = []
            st.session_state.input_lat = 35.691953
            st.session_state.input_lng = 139.781719
            st.session_state.geojson_data = None
            st.session_state.df = None
            st.session_state.markers = []
            st.session_state.reset_clicked = False

    def _handle_data_fetch(self, zoom_level, from_date, to_date):
        """データ取得処理"""
        try:
            from real_estate_data_processor import GeoJsonDownloader, GeoJsonProcessor
            
            downloader = GeoJsonDownloader()
            st.session_state.geojson_data = downloader.get_geojson(
                lat=st.session_state.input_lat,
                lon=st.session_state.input_lng,
                zoom=zoom_level,
                from_date=from_date,
                to_date=to_date
            )

            processor = GeoJsonProcessor()
            st.session_state.df = processor.process_geojson(st.session_state.geojson_data)
            self._update_markers()
            st.rerun()

        except Exception as e:
            st.error(f"データの取得中にエラーが発生しました: {str(e)}")

    def _update_markers(self):
        """マーカー情報の更新"""
        if isinstance(st.session_state.geojson_data, dict) and 'features' in st.session_state.geojson_data:
            st.session_state.markers = []
            for feature in st.session_state.geojson_data['features']:
                if feature['geometry']['type'] == 'Point':
                    lng, lat = feature['geometry']['coordinates']
                    properties = feature['properties']
                    popup_content = '<br>'.join([
                        f"<b>{k}</b>: {v}" for k, v in properties.items()
                    ])
                    st.session_state.markers.append({
                        'lat': lat,
                        'lng': lng,
                        'popup': popup_content
                    })

    def run(self):
        """アプリケーションのメイン実行部分"""
        st.title("不動産データ分析マップ")
        st.write("地図をクリックして緯度経度を取得")

        # UI要素の表示
        render_location_inputs(st.session_state)
        zoom_level, (from_date, to_date) = render_control_panel()
        clear_data_clicked, search_clicked = render_action_buttons()

        # アクションの処理
        if clear_data_clicked:
            st.session_state.reset_clicked = True
            self._initialize_session_state()
            st.rerun()
        
        if search_clicked:
            self._handle_data_fetch(zoom_level, from_date, to_date)

        # データの表示
        self._display_data()
        self._display_map(zoom_level)

    def _display_data(self):
        """データとグラフの表示"""
        if st.session_state.geojson_data is not None:
            st.json(st.session_state.geojson_data)

            if (st.session_state.df is not None and 
                not st.session_state.df.empty and 
                not st.session_state.df['price_per_area'].isna().all()):
                
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

    def _display_map(self, zoom_level):
        """地図の表示"""
        m = folium.Map(
            location=[st.session_state.input_lat, st.session_state.input_lng],
            zoom_start=zoom_level,
            control_scale=True,
            zoom_control=True
        )

        marker_cluster = folium.plugins.MarkerCluster(
            options={
                'maxClusterRadius': 30,
                'disableClusteringAtZoom': 16,
                'spiderfyOnMaxZoom': True,
                'showCoverageOnHover': True,
                'zoomToBoundsOnClick': True
            }
        ).add_to(m)

        # マーカーの表示
        if 'markers' in st.session_state:
            for marker_data in st.session_state.markers:
                folium.Marker(
                    location=[marker_data['lat'], marker_data['lng']],
                    popup=folium.Popup(marker_data['popup'], max_width=300),
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(marker_cluster)

        # 地図の表示とクリックイベントの処理
        map_data = st_folium(
            m,
            height=600,
            width="100%",
            returned_objects=["last_clicked"],
            key="map",
            use_container_width=True
        )

        if map_data['last_clicked']:
            st.session_state.input_lat = map_data['last_clicked']['lat']
            st.session_state.input_lng = map_data['last_clicked']['lng']
            st.rerun()

def geo_estate_analyzer():
    """アプリケーションのエントリーポイント"""
    analyzer = GeoEstateAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    geo_estate_analyzer()
