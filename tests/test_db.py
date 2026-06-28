from db import get_all_teams_data, get_team_base_data


def test_get_all_teams_data():
    teams = get_all_teams_data()
    # チームのデータがリスト形式で存在することを確認
    assert isinstance(teams, list)
    assert len(teams) > 0
    # チームデータの基本構造を確認
    first_team = teams[0]
    assert "name" in first_team
    assert "base_elo" in first_team


def test_get_team_base_data():
    # 存在するチームを指定してデータを取得
    team = get_team_base_data("Brazil")
    assert team is not None
    assert team["name"] == "Brazil"
    assert team["base_elo"] > 1500
