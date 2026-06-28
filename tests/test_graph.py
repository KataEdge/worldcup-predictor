import pytest
from graph import (
    get_tactical_modifier,
    get_stadium_modifier,
    calc_node,
    debate_agent_a_node,
    debate_agent_b_node,
    debate_rebuttal_b_node,
    debate_synthesizer_node,
)
from state import WorldCupState


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

    # 2. 高地デバフ (標高2,200m。CONMEBOL/メキシコ以外は -10%)
    # ドイツ (デバフ対象) -> 0.90
    assert get_stadium_modifier("Germany", "press", "altitude", "USA") == pytest.approx(
        0.90
    )
    # ブラジル (デバフ対象外) -> 1.0
    assert get_stadium_modifier(
        "Brazil", "possession", "altitude", "USA"
    ) == pytest.approx(1.0)

    # 3. 人工芝 (ポゼッションスタイルは +5% バフ、それ以外は -5% デバフ)
    assert get_stadium_modifier("Spain", "possession", "turf", "USA") == pytest.approx(
        1.05
    )
    assert get_stadium_modifier("Germany", "press", "turf", "USA") == pytest.approx(
        0.95
    )

    # 4. 酷暑 (欧州+東アジア勢は -5% デバフ)
    # ドイツ (欧州勢、デバフ対象) -> 0.95
    assert get_stadium_modifier("Germany", "press", "heat", "USA") == pytest.approx(
        0.95
    )
    # ブラジル (デバフ対象外) -> 1.0
    assert get_stadium_modifier("Brazil", "possession", "heat", "USA") == pytest.approx(
        1.0
    )


def test_calc_node():
    # 最小限の WorldCupState モック
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

    # 確率の合計値がほぼ 1.0 になるか検証
    total_prob = (
        result["prob_team_a_win"] + result["prob_team_b_win"] + result["prob_draw"]
    )
    assert total_prob == pytest.approx(1.0, rel=1e-2)


def test_debate_nodes_without_api_key(monkeypatch):
    # APIキーがない状態をシミュレート
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

    # 1. debate_agent_a_node
    res_a = debate_agent_a_node(state)
    assert "debate_history" in res_a
    assert len(res_a["debate_history"]) == 1
    assert "Brazil 担当記者" in res_a["debate_history"][0]["agent"]

    # 2. debate_agent_b_node
    state["debate_history"] = res_a["debate_history"]
    res_b = debate_agent_b_node(state)
    assert len(res_b["debate_history"]) == 2
    assert "Germany 担当記者" in res_b["debate_history"][1]["agent"]

    # 3. debate_rebuttal_b_node
    state["debate_history"] = res_b["debate_history"]
    res_rebuttal_b = debate_rebuttal_b_node(state)
    assert len(res_rebuttal_b["debate_history"]) == 3
    assert "Germany 担当記者 (最後)" in res_rebuttal_b["debate_history"][2]["agent"]

    # 4. debate_synthesizer_node
    res_synth = debate_synthesizer_node(state)
    assert "agent_analysis" in res_synth
    assert res_synth["team_a_modifier"] == 1.0
    assert res_synth["team_b_modifier"] == 1.0
