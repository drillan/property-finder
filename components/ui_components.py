from datetime import datetime

import streamlit as st


def render_location_inputs(session_state):
    """緯度経度入力コンポーネントを表示"""
    col_lat, col_lng = st.columns(2)
    with col_lat:
        session_state.input_lat = st.number_input(
            "緯度",
            value=session_state.input_lat,
            min_value=-90.0,
            max_value=90.0,
            format="%.6f",
            help="緯度を入力（例：35.691953）",
            key="input_lat_field"
        )
    with col_lng:
        session_state.input_lng = st.number_input(
            "経度",
            value=session_state.input_lng,
            min_value=-180.0,
            max_value=180.0,
            format="%.6f",
            help="経度を入力（例：139.781719）",
            key="input_lng_field"
        )

def render_control_panel():
    """ズームと期間選択のコントロールパネルを表示"""
    col_zoom, col_quarter = st.columns(2)
    
    with col_zoom:
        zoom_level = st.slider(
            "ズームレベル",
            min_value=10,
            max_value=18,
            value=14,
            help="地図のズームレベルを選択"
        )

    with col_quarter:
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
    
    return zoom_level, selected_range

def render_action_buttons():
    """アクションボタンを表示"""
    col1, col2 = st.columns(2)
    reset_clicked = False
    fetch_clicked = False
    
    with col1:
        if st.button("データをリセット", key="reset_button"):
            reset_clicked = True
    with col2:
        if st.button('データを取得', key="fetch_button"):
            fetch_clicked = True
            
    return reset_clicked, fetch_clicked 