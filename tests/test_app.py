import pytest
from streamlit.testing.v1 import AppTest
import pandas as pd
import db


@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch, tmp_path):
    # テストごとに一時的なSQLite DBを使用するようにDB_PATHを書き換える
    test_db = tmp_path / "test_app_worldcup.db"
    monkeypatch.setattr(db, "DB_PATH", str(test_db))

    # pd.read_csvのモック
    dummy_csv = pd.DataFrame(
        {
            "date": ["2022-12-18"],
            "home_team": ["Argentina"],
            "away_team": ["France"],
            "home_score": [3],
            "away_score": [3],
            "tournament": ["FIFA World Cup"],
        }
    )
    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: dummy_csv)

    # API接続設定を未設定（モック/フォールバックルート）に強制
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)


def test_app_load():
    db.init_sqlite_db()

    # AppTest を使って app.py をシミュレート起動
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    assert not at.exception
    assert any("2026 World Cup AI Predictor" in md.value for md in at.markdown)


def test_app_click_predict_button():
    db.init_sqlite_db()

    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()

    # セレクトボックス(Team A と Team B)に異なるチームを選択
    at.selectbox[0].select("Mexico").run()
    at.selectbox[1].select("South Africa").run()

    # 「AI予想を実行する」ボタンをクリック
    at.button[0].click().run()

    assert not at.exception
    assert any(
        "予想プロセスが完了しました！" in success.value for success in at.success
    )
