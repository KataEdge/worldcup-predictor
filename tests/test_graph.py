import pytest
from unittest.mock import MagicMock, patch
from graph import (
    get_tactical_modifier,
    get_stadium_modifier,
    calc_node,
    debate_agent_a_node,
    debate_agent_b_node,
    debate_rebuttal_a_node,
    debate_rebuttal_b_node,
    debate_synthesizer_node,
    summary_node,
    get_group_stadium_info,
    simulate_match,
    simulate_group_stage,
    create_graph,
    simulate_tournament_monte_carlo,
)
from state import WorldCupState
import db


def test_get_tactical_modifier():
    # 3すくみのアドバンテージ側の検証
    assert get_tactical_modifier("possession", "press") == (1.05, 0.95)
    assert get_tactical_modifier("press", "counter") == (1.05, 0.95)
    assert get_tactical_modifier("counter", "possession") == (1.05, 0.95)

    # 3すくみのディスアドバンテージ側の検証
    assert get_tactical_modifier("press", "possession") == (0.95, 1.05)
    assert get_tactical_modifier("counter", "press") == (0.95, 1.05)
    assert get_tactical_modifier("possession", "counter") == (0.95, 1.05)

    # 相性補正なしの検証
    assert get_tactical_modifier("balanced", "balanced") == (1.0, 1.0)
    assert get_tactical_modifier("possession", "possession") == (1.0, 1.0)


def test_get_stadium_modifier():
    # 1. ホームアドバンテージ (+10%)
    assert get_stadium_modifier(
        "Brazil", "possession", "standard", "Brazil"
    ) == pytest.approx(1.10)
    assert get_stadium_modifier(
        "Germany", "press", "standard", "Brazil"
    ) == pytest.approx(1.0)

    # 2. 高地デバフ
    assert get_stadium_modifier("Germany", "press", "altitude", "USA") == pytest.approx(
        0.90
    )
    assert get_stadium_modifier(
        "Brazil", "possession", "altitude", "USA"
    ) == pytest.approx(1.0)

    # 3. 人工芝
    assert get_stadium_modifier("Spain", "possession", "turf", "USA") == pytest.approx(
        1.05
    )
    assert get_stadium_modifier("Germany", "press", "turf", "USA") == pytest.approx(
        0.95
    )

    # 4. 酷暑
    assert get_stadium_modifier("Germany", "press", "heat", "USA") == pytest.approx(
        0.95
    )
    assert get_stadium_modifier("Brazil", "possession", "heat", "USA") == pytest.approx(
        1.0
    )


def test_calc_node_stadium_and_rest():
    # 様々なスタジアムと休養日数で条件分岐を網羅
    state: WorldCupState = {
        "team_a": "Brazil",
        "team_b": "Germany",
        "team_a_base_elo": 2000.0,
        "team_b_base_elo": 1900.0,
        "team_a_avg_goals": 2.0,
        "team_b_avg_goals": 1.5,
        "team_a_market_value": 1000.0,
        "team_b_market_value": 800.0,
        "team_a_tactics": "possession",
        "team_b_tactics": "press",
        "team_a_pk_rating": 4,
        "team_b_pk_rating": 5,
        "team_a_rest_days": 2,
        "team_b_rest_days": 4,  # rest_a < rest_b
        "stadium_name": "Estadio Azteca (Mexico)",  # host Mexico
        "stadium_env": "altitude",
        "host_country": "Mexico",
        "team_a_modifier": 1.0,
        "team_b_modifier": 1.0,
        "h2h_history": [],
    }

    # case 1: rest_a < rest_b & Azteca (Mexico)
    res = calc_node(state)
    assert res["expected_goals_a"] > 0

    # case 2: rest_b < rest_a & BC Place (Canada)
    state["team_a_rest_days"] = 4
    state["team_b_rest_days"] = 2
    state["stadium_name"] = "BC Place (Vancouver)"
    res = calc_node(state)
    assert res["expected_goals_b"] > 0


def test_summary_node():
    state = {
        "team_a": "Brazil",
        "team_b": "Germany",
        "prob_team_a_win": 0.5,
        "prob_team_b_win": 0.3,
        "prob_draw": 0.2,
        "expected_goals_a": 1.8,
        "expected_goals_b": 1.2,
        "team_a_tactics": "possession",
        "team_b_tactics": "press",
        "team_a_market_value": 1000,
        "team_b_market_value": 800,
        "team_a_pk_rating": 4,
        "team_b_pk_rating": 5,
        "stadium_name": "MetLife Stadium",
        "stadium_env": "standard",
        "agent_analysis": "Discuss summary",
    }
    res = summary_node(state)
    assert "final_summary" in res
    assert "Brazil" in res["final_summary"]


def test_get_group_stadium_info():
    assert get_group_stadium_info("A") == (
        "Estadio Azteca (Mexico City)",
        "altitude",
        "Mexico",
    )
    assert get_group_stadium_info("B") == ("BC Place (Vancouver)", "turf", "Canada")
    assert get_group_stadium_info("C") == (
        "Hard Rock Stadium (Miami)",
        "heat",
        "United States",
    )
    assert get_group_stadium_info("D") == (
        "MetLife Stadium (New York/New Jersey)",
        "standard",
        "United States",
    )
    assert get_group_stadium_info("H") == (
        "NRG Stadium (Houston)",
        "standard",
        "United States",
    )


def test_simulate_match():
    team_a = {"name": "Brazil", "base_elo": 2000, "avg_goals": 2.0, "pk_rating": 4}
    team_b = {"name": "Germany", "base_elo": 1900, "avg_goals": 1.5, "pk_rating": 5}

    # 1. 通常試合 (グループステージ想定)
    score_a, score_b, winner = simulate_match(team_a, team_b, is_knockout=False)
    assert score_a >= 0
    assert score_b >= 0

    # 2. ノックアウト試合 (引き分け時にPKで必ず決着することの検証)
    # Poissonで確実に同点 (期待値0) になるようダミー設定で試合をシミュレート
    with patch("numpy.random.poisson", return_value=1):
        score_a, score_b, winner = simulate_match(team_a, team_b, is_knockout=True)
        assert score_a == 1
        assert score_b == 1
        assert winner in ["Brazil", "Germany"]


def test_simulate_group_stage():
    mock_teams = db.TEAMS_DATA[:48]
    # 全12グループに分けるためにグループ名 (A-L) を設定
    for i, t in enumerate(mock_teams):
        group_letter = chr(ord("A") + (i // 4))
        t["group_name"] = group_letter

    last_match_days = {t["name"]: None for t in mock_teams}

    res = simulate_group_stage(mock_teams, last_match_days)
    assert "all_qualified" in res
    assert len(res["all_qualified"]) == 32  # 32チーム勝ち抜け


def test_debate_nodes_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    state: WorldCupState = {
        "team_a": "Brazil",
        "team_b": "Germany",
        "team_a_base_elo": 2000.0,
        "team_b_base_elo": 1900.0,
        "team_a_avg_goals": 2.0,
        "team_b_avg_goals": 1.5,
        "team_a_market_value": 1000.0,
        "team_b_market_value": 800.0,
        "team_a_tactics": "possession",
        "team_b_tactics": "press",
        "team_a_pk_rating": 4,
        "team_b_pk_rating": 5,
        "team_a_rest_days": 4,
        "team_b_rest_days": 4,
        "stadium_name": "MetLife Stadium",
        "stadium_env": "standard",
        "host_country": "USA",
        "debate_history": [],
    }

    # APIキーが無い場合のモック確認
    res_a = debate_agent_a_node(state)
    assert "Brazil 担当記者" in res_a["debate_history"][0]["agent"]

    state["debate_history"] = res_a["debate_history"]
    res_b = debate_agent_b_node(state)
    assert "Germany 担当記者" in res_b["debate_history"][1]["agent"]

    state["debate_history"] = res_b["debate_history"]
    res_rebuttal_a = debate_rebuttal_a_node(state)
    assert "Brazil 担当記者 (再反論)" in res_rebuttal_a["debate_history"][2]["agent"]

    state["debate_history"] = res_rebuttal_a["debate_history"]
    res_rebuttal_b = debate_rebuttal_b_node(state)
    assert "Germany 担当記者 (最後)" in res_rebuttal_b["debate_history"][3]["agent"]

    res_synth = debate_synthesizer_node(state)
    assert "APIキー未設定" in res_synth["agent_analysis"]


def test_debate_nodes_with_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    state: WorldCupState = {
        "team_a": "Brazil",
        "team_b": "Germany",
        "team_a_base_elo": 2000.0,
        "team_b_base_elo": 1900.0,
        "team_a_avg_goals": 2.0,
        "team_b_avg_goals": 1.5,
        "team_a_market_value": 1000.0,
        "team_b_market_value": 800.0,
        "team_a_tactics": "possession",
        "team_b_tactics": "press",
        "team_a_pk_rating": 4,
        "team_b_pk_rating": 5,
        "team_a_rest_days": 4,
        "team_b_rest_days": 4,
        "stadium_name": "MetLife Stadium",
        "stadium_env": "standard",
        "host_country": "USA",
        "debate_history": [],
    }

    mock_llm_response = MagicMock()
    mock_llm_response.content = "Mocked LLM Speech Content"

    with patch("graph.ChatGoogleGenerativeAI.invoke", return_value=mock_llm_response):
        res_a = debate_agent_a_node(state)
        assert res_a["debate_history"][0]["content"] == "Mocked LLM Speech Content"

        state["debate_history"] = res_a["debate_history"]
        res_b = debate_agent_b_node(state)
        assert res_b["debate_history"][-1]["content"] == "Mocked LLM Speech Content"

        state["debate_history"] = res_b["debate_history"]
        res_rebuttal_a = debate_rebuttal_a_node(state)
        assert (
            res_rebuttal_a["debate_history"][-1]["content"]
            == "Mocked LLM Speech Content"
        )

        state["debate_history"] = res_rebuttal_a["debate_history"]
        res_rebuttal_b = debate_rebuttal_b_node(state)
        assert (
            res_rebuttal_b["debate_history"][-1]["content"]
            == "Mocked LLM Speech Content"
        )

    # structure output mock
    mock_structured_llm = MagicMock()
    mock_output_obj = MagicMock()
    mock_output_obj.agent_analysis = "Mocked Analyst Summary"
    mock_output_obj.team_a_modifier = 1.15
    mock_output_obj.team_b_modifier = 0.85
    mock_structured_llm.invoke.return_value = mock_output_obj
    mock_structured_llm.return_value = mock_output_obj

    with patch(
        "graph.ChatGoogleGenerativeAI.with_structured_output",
        return_value=mock_structured_llm,
    ):
        res_synth = debate_synthesizer_node(state)
        assert res_synth["agent_analysis"] == "Mocked Analyst Summary"


def test_debate_nodes_exception_handling(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    state: WorldCupState = {
        "team_a": "Brazil",
        "team_b": "Germany",
        "team_a_base_elo": 2000,
        "team_b_base_elo": 1900,
        "team_a_avg_goals": 2,
        "team_b_avg_goals": 1.5,
        "team_a_market_value": 1000,
        "team_b_market_value": 800,
        "team_a_tactics": "possession",
        "team_b_tactics": "press",
        "team_a_pk_rating": 4,
        "team_b_pk_rating": 5,
        "stadium_name": "MetLife Stadium",
        "stadium_env": "standard",
        "debate_history": [],
    }

    with patch(
        "graph.ChatGoogleGenerativeAI.invoke", side_effect=Exception("LLM Timeout")
    ):
        res_a = debate_agent_a_node(state)
        assert "エラー" in res_a["debate_history"][0]["content"]

        state["debate_history"] = [{"agent": "Brazil 担当", "content": "hello"}]
        res_b = debate_agent_b_node(state)
        assert "エラー" in res_b["debate_history"][-1]["content"]

        res_rebuttal_a = debate_rebuttal_a_node(state)
        assert "エラー" in res_rebuttal_a["debate_history"][-1]["content"]

        res_rebuttal_b = debate_rebuttal_b_node(state)
        assert "エラー" in res_rebuttal_b["debate_history"][-1]["content"]

    with patch(
        "graph.ChatGoogleGenerativeAI.with_structured_output",
        side_effect=Exception("LLM Structure Error"),
    ):
        res_synth = debate_synthesizer_node(state)
        assert "エラー" in res_synth["agent_analysis"]


def test_create_graph():
    app = create_graph()
    assert app is not None


def test_simulate_tournament_monte_carlo():
    mock_teams = db.TEAMS_DATA[:48]
    # グループ名割り当て
    for i, t in enumerate(mock_teams):
        t["group_name"] = chr(ord("A") + (i // 4))

    results = simulate_tournament_monte_carlo(mock_teams, num_simulations=2)
    assert "Mexico" in results
    assert "winner" in results["Mexico"]
