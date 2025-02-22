from pathlib import Path
from typing import Optional

import duckdb
import streamlit as st


class BaseAnalyzer:
    """不動産分析の基底クラス"""
    
    def __init__(self):
        self.data_file = Path(__file__).parent / "data" / "data.parquet"
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """セッション状態の初期化（サブクラスでオーバーライド）"""
        pass
    
    def _load_data(self) -> Optional[duckdb.DuckDBPyRelation]:
        """データの読み込み"""
        try:
            return duckdb.sql(f"SELECT * FROM '{self.data_file}'")
        except FileNotFoundError:
            st.error(f"{self.data_file} が見つかりません。ファイルパスを確認してください。")
        except Exception as e:
            st.error(f"データ読み込み中にエラーが発生しました: {e}")
        return None
    
    def run(self) -> None:
        """アプリケーションのメイン実行部分（サブクラスでオーバーライド）"""
        pass 