import sqlite3
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
import db


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    # テストごとに一時的なSQLite DBを使用するようにDB_PATHを書き換える
    test_db = tmp_path / "test_worldcup.db"
    monkeypatch.setattr(db, "DB_PATH", str(test_db))


def test_init_sqlite_db_with_csv_mock(monkeypatch):
    # pd.read_csvをモックしてインターネット通信を避ける
    dummy_csv_data = pd.DataFrame(
        {
            "date": ["2022-12-18", "2018-07-15"],
            "home_team": ["Argentina", "France"],
            "away_team": ["France", "Croatia"],
            "home_score": [3, 4],
            "away_score": [3, 2],
            "tournament": ["FIFA World Cup", "FIFA World Cup"],
        }
    )

    # pandas.read_csvをモック
    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: dummy_csv_data)

    # データベースの初期化を実行
    db.init_sqlite_db()

    # SQLiteの中身を確認
    conn = db.get_sqlite_conn()
    cursor = conn.cursor()

    # チーム数がTEAMS_DATAの数と一致しているか
    cursor.execute("SELECT COUNT(*) FROM teams")
    teams_count = cursor.fetchone()[0]
    assert teams_count == len(db.TEAMS_DATA)

    # 試合数がダミーCSVのうち、TEAMS_DATAに含まれる国同士のもののみインポートされているか
    # 今回のダミーCSVのうち、Argentina, France, CroatiaはすべてTEAMS_DATAに入っているため、2件入るはず
    cursor.execute("SELECT COUNT(*) FROM historical_matches")
    matches_count = cursor.fetchone()[0]
    assert matches_count == 2

    conn.close()


def test_get_supabase_client_value_error(monkeypatch):
    # 環境変数を未設定にしてValueErrorが発生することを確認
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    with pytest.raises(ValueError, match="Supabase credentials not set or invalid"):
        db.get_supabase_client()


def test_get_all_teams_data_from_supabase():
    # Supabaseクライアントのモックを作成
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {
            "name": "MockTeam",
            "base_elo": 1800,
            "avg_goals": 1.5,
            "group_name": "A",
            "market_value": 100,
            "tactics_style": "balanced",
            "pk_rating": 3,
        }
    ]

    # クエリチェーンのモック: supabase.table().select().execute() -> mock_response
    mock_client.table.return_value.select.return_value.execute.return_value = (
        mock_response
    )

    # get_supabase_clientがmock_clientを返すようにパッチ
    with patch("db.get_supabase_client", return_value=mock_client):
        teams = db.get_all_teams_data()
        assert len(teams) == 1
        assert teams[0]["name"] == "MockTeam"


def test_get_team_base_data_from_supabase():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"name": "Brazil", "base_elo": 2000}]
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    with patch("db.get_supabase_client", return_value=mock_client):
        team = db.get_team_base_data("Brazil")
        assert team is not None
        assert team["name"] == "Brazil"
        assert team["base_elo"] == 2000


def test_get_team_base_data_sqlite_fallback():
    # Supabaseが例外を投げた場合にSQLiteへフォールバックするテスト
    with patch("db.get_supabase_client", side_effect=Exception("Supabase Down")):
        db.init_sqlite_db()
        team = db.get_team_base_data("Brazil")
        assert team is not None
        assert team["name"] == "Brazil"


def test_get_weighted_avg_goals_from_supabase():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {
            "date": "2024-01-01",
            "home_team": "Brazil",
            "away_team": "Germany",
            "home_score": 2,
            "away_score": 1,
            "tournament": "Friendly",
        }
    ]
    mock_client.table.return_value.select.return_value.or_.return_value.execute.return_value = mock_response

    with patch("db.get_supabase_client", return_value=mock_client):
        goals = db.get_weighted_avg_goals("Brazil", 1.5)
        # 実際に計算され、フォールバック値ではない値が返るはず
        assert goals != 1.5


def test_get_weighted_avg_goals_sqlite_fallback():
    # Supabaseで例外を投げ、SQLiteのフォールバックを検証
    with patch("db.get_supabase_client", side_effect=Exception("Supabase Error")):
        # ダミーCSVデータを準備してSQLiteにデータをロード
        db.init_sqlite_db()
        goals = db.get_weighted_avg_goals("Brazil", 1.5)
        # SQLiteからデータが読み込まれ、フォールバック値が返る、あるいは計算結果が返る
        assert isinstance(goals, float)


def test_get_h2h_matches_from_supabase():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"home_team": "Brazil", "away_team": "Germany"}]
    mock_client.table.return_value.select.return_value.or_.return_value.order.return_value.execute.return_value = mock_response

    with patch("db.get_supabase_client", return_value=mock_client):
        matches = db.get_h2h_matches("Brazil", "Germany")
        assert len(matches) == 1
        assert matches[0]["home_team"] == "Brazil"


def test_get_h2h_matches_sqlite_fallback():
    with patch("db.get_supabase_client", side_effect=Exception("Supabase Down")):
        db.init_sqlite_db()
        matches = db.get_h2h_matches("Brazil", "Germany")
        assert isinstance(matches, list)


def test_sqlite_conn_error_handling(monkeypatch):
    # 接続作成時に例外を発生させるようにモック
    monkeypatch.setattr(
        sqlite3, "connect", MagicMock(side_effect=Exception("SQLite Connect Error"))
    )

    # 接続失敗時のフォールバック処理を検証
    assert db.get_all_teams_data_sqlite() == []
    assert db.get_weighted_avg_goals_sqlite("Brazil", 1.5) == 1.5
    assert db.get_h2h_matches_sqlite("Brazil", "Germany") == []
