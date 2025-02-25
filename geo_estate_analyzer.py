import unicodedata
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
            st.session_state.filtered_df = None
            st.session_state.filtered_geojson = None
            st.session_state.markers = []
            st.session_state.reset_clicked = False
            st.session_state.selected_price_category = "すべて"  # 価格区分の初期値
            st.session_state.selected_floor_plans = ["すべて"]  # 間取りの初期値（リストに変更）

    def _display_filter_options(self):
        """価格区分と間取りのフィルタリングオプションを表示"""
        col1, col2 = st.columns(2)
        
        with col1:
            # 価格情報区分のオプション
            price_categories = ["すべて", "不動産取引価格情報", "成約価格情報"]
            # 値変更時に処理を実行しないよう、key パラメータを追加
            st.session_state.selected_price_category = st.selectbox(
                "価格情報区分",
                options=price_categories,
                index=price_categories.index(st.session_state.get("selected_price_category", "すべて")),
                key="price_category_select"
            )
        
        with col2:
            # 間取りのオプション
            floor_plans = ["すべて", 
                "1R", "1K", "1LDK", "2LDK", "3DK", "3LDK", "2DK", "1DK", 
                "1LDK+S", "オープンフロア", "2K", "4LDK", "2LDK+S", 
                "スタジオ", "1DK+S", "2DK+S", "4DK+S", "3LDK+S", "3K", 
                "4LDK+S", "5LDK", "4DK", "3DK+S", "メゾネット", "1K+S", 
                "3LK", "1LK", "2K+S", "1R+S", "7LDK", "2LK+S", "4K", 
                "1LD+S", "5DK", "5K", "6LDK", "5LDK+S", "3K+S", "6LDK+S"
            ]
            
            # デフォルト値の取得
            default_floor_plans = st.session_state.get("selected_floor_plans", ["すべて"])
            
            # multiselectを使用して複数選択を可能にする
            st.session_state.selected_floor_plans = st.multiselect(
                "間取り（複数選択可）",
                options=floor_plans,
                default=default_floor_plans,
                key="floor_plan_multiselect"
            )
            
            # "すべて"が選択されている場合は他の選択を無視する
            if "すべて" in st.session_state.selected_floor_plans and len(st.session_state.selected_floor_plans) > 1:
                st.session_state.selected_floor_plans = ["すべて"]
                st.rerun()

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
            
            # データ取得後にフィルタリングを適用
            self._apply_filters()
            
            self._update_markers()

        except Exception as e:
            st.error(f"データの取得中にエラーが発生しました: {str(e)}")

    def _apply_filters(self):
        """選択された価格区分と間取りに基づいてデータをフィルタリング"""
        if st.session_state.df is None or st.session_state.df.empty:
            return
        
        filtered_df = st.session_state.df.copy()
        
        # 価格情報区分フィルター
        if st.session_state.selected_price_category != "すべて":
            filtered_df = filtered_df[filtered_df['price_category'] == st.session_state.selected_price_category]
        
        # 間取りフィルター (複数選択対応)
        if "すべて" not in st.session_state.selected_floor_plans and st.session_state.selected_floor_plans:
            # 選択された間取りを全て正規化
            normalized_selections = [unicodedata.normalize('NFKC', fp) for fp in st.session_state.selected_floor_plans]
            
            # いずれかの選択肢に一致する行をフィルタリング
            filtered_df = filtered_df[filtered_df['floor_plan'].apply(
                lambda x: unicodedata.normalize('NFKC', x) in normalized_selections
            )]
        
        # フィルタリングされたデータフレームを保存
        st.session_state.filtered_df = filtered_df
        
        # GeoJSONのフィルタリング（マーカー表示用）
        if isinstance(st.session_state.geojson_data, dict) and 'features' in st.session_state.geojson_data:
            filtered_features = []
            
            # 間取り選択の正規化（複数選択対応）
            normalized_floor_plans = None
            if "すべて" not in st.session_state.selected_floor_plans and st.session_state.selected_floor_plans:
                normalized_floor_plans = [unicodedata.normalize('NFKC', fp) for fp in st.session_state.selected_floor_plans]
            
            for feature in st.session_state.geojson_data['features']:
                include_feature = True
                properties = feature.get('properties', {})
                
                # 価格情報区分フィルター
                if st.session_state.selected_price_category != "すべて":
                    if properties.get('price_information_category_name_ja') != st.session_state.selected_price_category:
                        include_feature = False
                
                # 間取りフィルター（複数選択対応）
                if normalized_floor_plans:
                    feature_floor_plan = properties.get('floor_plan_name_ja', '')
                    if feature_floor_plan:
                        normalized_feature_floor_plan = unicodedata.normalize('NFKC', feature_floor_plan)
                        if normalized_feature_floor_plan not in normalized_floor_plans:
                            include_feature = False
                    else:
                        include_feature = False
                
                if include_feature:
                    filtered_features.append(feature)
            
            # フィルタリングされたGeoJSONを保存
            filtered_geojson = st.session_state.geojson_data.copy()
            filtered_geojson['features'] = filtered_features
            st.session_state.filtered_geojson = filtered_geojson
        else:
            st.session_state.filtered_geojson = st.session_state.geojson_data

    def _update_markers(self):
        """マーカー情報の更新"""
        geojson_data = st.session_state.get('filtered_geojson', st.session_state.geojson_data)
        
        if isinstance(geojson_data, dict) and 'features' in geojson_data:
            st.session_state.markers = []
            for feature in geojson_data['features']:
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
        st.write("地図をクリックして「物件を検索」をクリックしてください")

        # UI要素の表示
        render_location_inputs(st.session_state)
        zoom_level, (from_date, to_date) = render_control_panel()
        
        # フィルタリングオプションの表示
        self._display_filter_options()
        
        clear_data_clicked, search_clicked = render_action_buttons()

        # メイン処理実行有無のフラグをセッションに記録
        if "should_process_data" not in st.session_state:
            st.session_state.should_process_data = False

        # アクションの処理
        if clear_data_clicked:
            st.session_state.reset_clicked = True
            st.session_state.should_process_data = False
            self._initialize_session_state()
            st.rerun()  # 状態をクリアするために再実行

        if search_clicked:
            # 検索ボタンクリック時にフラグを設定
            st.session_state.should_process_data = True
        
        # フラグがオンの場合のみデータ処理を実行    
        if st.session_state.should_process_data and st.session_state.geojson_data is None:
            with st.spinner("データを検索中..."):
                self._handle_data_fetch(zoom_level, from_date, to_date)
        
        # 既存のデータがある場合は再フィルタリングのみ適用
        elif st.session_state.should_process_data and st.session_state.geojson_data is not None:
            if search_clicked:
                with st.spinner("データを更新中..."):
                    self._handle_data_fetch(zoom_level, from_date, to_date)
        
        # データの表示（データがある場合のみ）
        if st.session_state.should_process_data:
            self._display_data()
        
        # 地図は常に表示
        self._display_map(zoom_level)

    def _display_data(self):
        """データとグラフの表示"""
        if st.session_state.geojson_data is not None:
            # フィルタリングされたデータフレームを使用
            display_df = st.session_state.get('filtered_df', st.session_state.df)
            
            if display_df is not None and not display_df.empty:
                st.subheader("検索結果")
                
                # 利用可能な列を確認
                available_columns = [
                    'period',
                    'price',
                    'area',
                    'price_per_area',
                    'price_category',  # 価格帯の列を追加
                    'floor_plan'       # 間取りの列を追加
                ]
                
                # 列名を日本語に変換
                column_names = {
                    'period': '期間',
                    'price': '価格（万円）',
                    'area': '面積（㎡）',
                    'price_per_area': '単価（万円/㎡）',
                    'price_category': '価格帯',  # 価格帯の日本語名
                    'floor_plan': '間取り'       # 間取りの日本語名
                }
                
                # 表示するデータフレームを整形
                display_columns = [col for col in available_columns if col in display_df.columns]
                formatted_df = display_df[display_columns].copy()
                formatted_df = formatted_df.rename(columns={col: column_names.get(col, col) for col in display_columns})
                
                # 数値データを整形
                if 'price' in display_df.columns:
                    formatted_df['価格（万円）'] = formatted_df['価格（万円）'].round(0).astype(int)
                if 'price_per_area' in display_df.columns:
                    formatted_df['単価（万円/㎡）'] = formatted_df['単価（万円/㎡）'].round(1)
                
                st.dataframe(
                    formatted_df,
                    hide_index=True,
                    use_container_width=True
                )

            # グラフ表示（フィルタリングされたデータを使用）
            if (display_df is not None and 
                not display_df.empty and 
                'price_per_area' in display_df.columns and
                not display_df['price_per_area'].isna().all()):
                
                fig = px.box(
                    display_df,
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

        # タイル範囲の矩形を表示
        from real_estate_data_processor import GeoJsonDownloader
        downloader = GeoJsonDownloader()
        x, y = downloader.latlon_to_tile(st.session_state.input_lat, st.session_state.input_lng, zoom_level)
        south, west, north, east = downloader.get_tile_bounds(x, y, zoom_level)
        
        # 矩形の座標を設定
        bounds = [[south, west], [north, east]]
        folium.Rectangle(
            bounds=bounds,
            color='red',
            weight=2,
            fill=False,
            popup=f'Tile: x={x}, y={y}, zoom={zoom_level}'
        ).add_to(m)

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

def geo_estate_analyzer():
    """アプリケーションのエントリーポイント"""
    analyzer = GeoEstateAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    geo_estate_analyzer()
