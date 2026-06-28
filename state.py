from typing import TypedDict, Optional, List, Dict, Any


class WorldCupState(TypedDict):
    # User Input
    team_a: str
    team_b: str

    # Base Data (from Supabase)
    team_a_base_elo: float
    team_b_base_elo: float
    team_a_avg_goals: float
    team_b_avg_goals: float
    team_a_market_value: float
    team_b_market_value: float
    team_a_tactics: str
    team_b_tactics: str
    team_a_pk_rating: int
    team_b_pk_rating: int
    team_a_rest_days: Optional[int]
    team_b_rest_days: Optional[int]
    stadium_name: str
    stadium_env: str
    h2h_history: List[Dict[str, Any]]

    # Agent Analysis & Debate
    debate_history: List[Dict[str, str]]  # [{"agent": "...", "content": "..."}]
    agent_analysis: str
    team_a_modifier: float
    team_b_modifier: float

    # Model Calculation Results
    prob_team_a_win: float
    prob_team_b_win: float
    prob_draw: float
    expected_goals_a: float
    expected_goals_b: float

    # Final Output
    final_summary: str
    error_message: Optional[str]
