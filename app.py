import streamlit as st

from data_analysis import data_analysis_page
from real_estate_search import real_estate_search_page


def home_page():
    st.title("不動産情報")
    st.markdown("""このアプリケーションは [不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/) から取得したデータを利用しています。""")
    st.write("左のサイドバーから目的のページを選択してください。")

# サイドバーにページ選択用のラジオボタンを作成
pages = {
    "トップページ": home_page,
    "不動産データ検索": real_estate_search_page,
    "不動産データ分析": data_analysis_page
}

page = st.sidebar.radio("ページ選択", list(pages.keys()))

# 選択されたページの関数を呼び出して表示
pages[page]() 