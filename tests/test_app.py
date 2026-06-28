import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch
import db

def test_app_load():
    # テスト実行前にSQLite DBを初期化し、チーム一覧が読み込める状態にする
    db.init_sqlite_db()

    # AppTest を使って app.py をシミュレート起動
    # タイムアウトを長めに設定
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # アプリケーションロード時に例外（エラー）が発生していないこと
    assert not at.exception
    
    # 画面にタイトルが表示されていることを確認 (st.markdownで表示されているためmarkdownを検証)
    assert any("2026 World Cup AI Predictor" in md.value for md in at.markdown)
