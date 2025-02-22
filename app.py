import streamlit as st

from data_analysis import DataAnalyzer
from geo_estate_analyzer import GeoEstateAnalyzer
from real_estate_search import SearchAnalyzer


def home_page():
    st.title("不動産情報")
    st.markdown("""このアプリケーションは [不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/) から取得したデータを利用しています。""")
    st.write("左のサイドバーから目的のページを選択してください。")

def main():
    pages = {
        "トップページ": home_page,
        "データ検索": lambda: SearchAnalyzer().run(),
        "データ分析": lambda: DataAnalyzer().run(),
        "位置情報によるデータ分析": lambda: GeoEstateAnalyzer().run()
    }

    page = st.sidebar.radio("ページ選択", list(pages.keys()))
    pages[page]()

if __name__ == "__main__":
    main() 