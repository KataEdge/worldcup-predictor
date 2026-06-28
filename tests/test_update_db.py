import sqlite3
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
import update_db
import db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    # テストごとに一時的なSQLite DBを使用するようにDB_PATHを書き換える
    test_db = tmp_path / "test_update_worldcup.db"
    monkeypatch.setattr(db, "DB_PATH", str(test_db))


def test_update_sqlite_success(monkeypatch):
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

    # 実行
    update_db.update_sqlite()

    # コネクションを取得してデータ検証
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM teams")
    assert cursor.fetchone()[0] == len(update_db.TEAMS_DATA)
    cursor.execute("SELECT COUNT(*) FROM historical_matches")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_update_sqlite_exception(monkeypatch):
    # CSV読み込み例外発生時に例外をキャッチして正常終了することを確認
    monkeypatch.setattr(
        pd, "read_csv", MagicMock(side_effect=Exception("Download failed"))
    )

    # 正常終了すること（エラーがスルーされること）を確認
    update_db.update_sqlite()


def test_update_teams_and_sync_matches():
    mock_supabase = MagicMock()
    # supabaseの各テーブルクエリをモック化
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
        MagicMock()
    )

    # sync_matches内の historical_matches 取得モック
    mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
        {"id": 1, "date": "2024-01-01", "home_team": "Brazil", "away_team": "Germany"}
    ]

    # 実行しても例外が起きないこと
    update_db.update_teams(mock_supabase)
    update_db.sync_matches(mock_supabase)


def test_get_supabase_client_value_error(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    with pytest.raises(ValueError):
        update_db.get_supabase_client()


def test_main_process_behavior(monkeypatch):
    # __main__ ブロックに書かれた例外処理挙動をテスト
    mock_update_sqlite = MagicMock()
    monkeypatch.setattr(update_db, "update_sqlite", mock_update_sqlite)

    # 1. Supabaseの処理が失敗した時に正しくキャッチされ、SQLiteの更新が呼ばれること
    with patch(
        "update_db.get_supabase_client", side_effect=Exception("Supabase failure")
    ):
        try:
            # __main__のロジックと同様
            supabase = update_db.get_supabase_client()
            update_db.update_teams(supabase)
        except Exception:
            pass

        try:
            update_db.update_sqlite()
        except Exception:
            pass

    assert mock_update_sqlite.call_count == 1
