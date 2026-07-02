import os
import pytest
from graph import create_graph
import db

# Check if API Key is available
has_google_api_key = bool(os.environ.get("GOOGLE_API_KEY"))


@pytest.mark.skipif(
    not has_google_api_key,
    reason="Requires GOOGLE_API_KEY for real LLM prompt verification",
)
def test_japan_vs_brazil_prompt_regression():
    # 1. Arrange
    team_a = "Japan"
    team_b = "Brazil"

    team_a_data = db.get_team_base_data(team_a)
    team_b_data = db.get_team_base_data(team_b)

    goals_a = db.get_weighted_avg_goals(team_a, team_a_data.get("avg_goals", 1.0))
    goals_b = db.get_weighted_avg_goals(team_b, team_b_data.get("avg_goals", 1.0))
    h2h = db.get_h2h_matches(team_a, team_b)

    initial_state = {
        "team_a": team_a,
        "team_b": team_b,
        "team_a_base_elo": float(team_a_data["base_elo"]),
        "team_b_base_elo": float(team_b_data["base_elo"]),
        "team_a_avg_goals": float(goals_a),
        "team_b_avg_goals": float(goals_b),
        "team_a_market_value": float(team_a_data.get("market_value", 50.0)),
        "team_b_market_value": float(team_b_data.get("market_value", 50.0)),
        "team_a_tactics": team_a_data.get("tactics_style", "balanced"),
        "team_b_tactics": team_b_data.get("tactics_style", "balanced"),
        "team_a_pk_rating": int(team_a_data.get("pk_rating", 3)),
        "team_b_pk_rating": int(team_b_data.get("pk_rating", 3)),
        "team_a_rest_days": 4,
        "team_b_rest_days": 4,
        "stadium_name": "MetLife Stadium (New York/New Jersey)",
        "stadium_env": "standard",
        "host_country": "United States",
        "h2h_history": h2h,
        "debate_history": [],
        "agent_analysis": "",
        "team_a_modifier": 1.0,
        "team_b_modifier": 1.0,
        "prob_team_a_win": 0.0,
        "prob_team_b_win": 0.0,
        "prob_draw": 0.0,
        "expected_goals_a": 0.0,
        "expected_goals_b": 0.0,
        "final_summary": "",
        "error_message": None,
    }

    # 2. Act
    app = create_graph()
    final_state = app.invoke(initial_state)

    # 3. Assert
    # Verify that the modifiers returned by the judge are within the expected [0.8, 1.2] range
    assert 0.8 <= final_state["team_a_modifier"] <= 1.2, (
        f"Team A modifier {final_state['team_a_modifier']} out of bounds!"
    )
    assert 0.8 <= final_state["team_b_modifier"] <= 1.2, (
        f"Team B modifier {final_state['team_b_modifier']} out of bounds!"
    )

    # Verify debate history is populated (should have multiple dialogue entries)
    assert len(final_state["debate_history"]) > 0

    # Verify judge tactical analysis text
    assert final_state["agent_analysis"] != ""
    assert isinstance(final_state["agent_analysis"], str)

    # Verify calculated expectation bounds
    assert 0.0 <= final_state["prob_team_a_win"] <= 1.0
    assert 0.0 <= final_state["prob_team_b_win"] <= 1.0
    assert 0.0 <= final_state["prob_draw"] <= 1.0
    assert (
        pytest.approx(
            final_state["prob_team_a_win"]
            + final_state["prob_team_b_win"]
            + final_state["prob_draw"]
        )
        == 1.0
    )

    assert final_state["expected_goals_a"] >= 0.0
    assert final_state["expected_goals_b"] >= 0.0
