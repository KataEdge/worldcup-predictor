import pytest
from unittest.mock import MagicMock, patch
from graph import (
    get_tactical_modifier,
    get_stadium_modifier,
    calc_node,
    debate_agent_a_node,
    debate_agent_b_node,
    debate_rebuttal_b_node,
    debate_synthesizer_node,
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
    assert get_stadium_modifier("Brazil", "possession", "standard", "Brazil") == pytest.approx(1.10)
    assert get_stadium_modifier("Germany", "press", "standard", "Brazil") == pytest.approx(1.0)

    # 2. 高地デバフ (標高2,200m。CONMEBOL/メキシコ以外は -10%)
    assert get_stadium_modifier("Germany", "press", "altitude", "USA") == pytest.approx(0.90)
    assert get_stadium_modifier("Brazil", "possession", "altitude", "USA") == pytest.approx(1.0)

    # 3. 人工芝 (ポゼッションスタイルは +5% バフ、それ以外は -5% デバフ)
    assert get_stadium_modifier("Spain", "possession", "turf", "USA") == pytest.approx(1.05)
    assert get_stadium_modifier("Germany", "press", "turf", "USA") == pytest.approx(0.95)

    # 4. 酷暑 (欧州+東アジア勢は -5% デバフ)
    assert get_stadium_modifier("Germany", "press", "heat", "USA") == pytest.approx(0.95)
    assert get_stadium_modifier("Brazil", "possession", "heat", "USA") == pytest.approx(1.0)


def test_calc_node():
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
        "team_a_modifier": 1.0,
        "team_b_modifier": 1.0,
        "h2h_history": [],
    }

    result = calc_node(state)
    assert "prob_team_a_win" in result
    assert "prob_team_b_win" in result
    assert "prob_draw" in result
    assert "expected_goals_a" in result
    assert "expected_goals_b" in result

    total_prob = result["prob_team_a_win"] + result["prob_team_b_win"] + result["prob_draw"]
    assert total_prob == pytest.approx(1.0, rel=1e-2)


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
    res_rebuttal_b = debate_rebuttal_b_node(state)
    assert "Germany 担当記者 (最後)" in res_rebuttal_b["debate_history"][2]["agent"]

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

    # 1. debate_agent_a_node / debate_agent_b_node の LLM 呼び出しモック化
    mock_llm_response = MagicMock()
    mock_llm_response.content = "Mocked LLM Speech Content"
    
    with patch("graph.ChatGoogleGenerativeAI.invoke", return_value=mock_llm_response):
        res_a = debate_agent_a_node(state)
        assert res_a["debate_history"][0]["content"] == "Mocked LLM Speech Content"

        state["debate_history"] = res_a["debate_history"]
        res_b = debate_agent_b_node(state)
        assert res_b["debate_history"][-1]["content"] == "Mocked LLM Speech Content"
        
        state["debate_history"] = res_b["debate_history"]
        res_rebuttal_b = debate_rebuttal_b_node(state)
        assert res_rebuttal_b["debate_history"][-1]["content"] == "Mocked LLM Speech Content"

    # 2. debate_synthesizer_node の LLM (with_structured_output) モック化
    mock_structured_llm = MagicMock()
    mock_output_obj = MagicMock()
    mock_output_obj.agent_analysis = "Mocked Analyst Summary"
    mock_output_obj.team_a_modifier = 1.15
    mock_output_obj.team_b_modifier = 0.85
    mock_structured_llm.invoke.return_value = mock_output_obj
    mock_structured_llm.return_value = mock_output_obj

    with patch("graph.ChatGoogleGenerativeAI.with_structured_output", return_value=mock_structured_llm):
        res_synth = debate_synthesizer_node(state)
        assert res_synth["agent_analysis"] == "Mocked Analyst Summary"
        assert res_synth["team_a_modifier"] == 1.15
        assert res_synth["team_b_modifier"] == 0.85


def test_debate_nodes_exception_handling(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
    state: WorldCupState = {
        "team_a": "Brazil", "team_b": "Germany", "team_a_base_elo": 2000, "team_b_base_elo": 1900,
        "team_a_avg_goals": 2, "team_b_avg_goals": 1.5, "team_a_market_value": 1000, "team_b_market_value": 800,
        "team_a_tactics": "possession", "team_b_tactics": "press", "team_a_pk_rating": 4, "team_b_pk_rating": 5,
        "stadium_name": "MetLife Stadium", "stadium_env": "standard", "debate_history": []
    }

    # 例外発生時の挙動を検証
    with patch("graph.ChatGoogleGenerativeAI.invoke", side_effect=Exception("LLM Timeout")):
        res_a = debate_agent_a_node(state)
        assert "エラー" in res_a["debate_history"][0]["content"]

        state["debate_history"] = [{"agent": "Brazil 担当", "content": "hello"}]
        res_b = debate_agent_b_node(state)
        assert "エラー" in res_b["debate_history"][-1]["content"]

        res_rebuttal = debate_rebuttal_b_node(state)
        assert "エラー" in res_rebuttal["debate_history"][-1]["content"]

    with patch("graph.ChatGoogleGenerativeAI.with_structured_output", side_effect=Exception("LLM Structure Error")):
        res_synth = debate_synthesizer_node(state)
        assert "エラー" in res_synth["agent_analysis"]


def test_create_graph():
    # StateGraph のコンパイルが正常に行われ、Runnableオブジェクトが返るか確認
    app = create_graph()
    assert app is not None
    assert hasattr(app, "invoke") or hasattr(app, "stream")


def test_simulate_tournament_monte_carlo():
    # TEAMS_DATAのサブセットを利用してトーナメントをシミュレート
    # 48チームすべてのモックデータを準備
    mock_teams = db.TEAMS_DATA[:48]
    
    # 2回シミュレーションを実行してコードパスを検証
    results = simulate_tournament_monte_carlo(mock_teams, num_simulations=2)
    assert "Mexico" in results
    assert "winner" in results["Mexico"]
    assert 0.0 <= results["Mexico"]["winner"] <= 1.0
