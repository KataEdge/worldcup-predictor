import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL", "")
    key: str = os.environ.get("SUPABASE_KEY", "")
    if url and not url.startswith("http"):
        url = f"https://{url}.supabase.co"
    if not url or not key:
        print("Warning: Supabase credentials not found. Using mock client or handling error later.")
        try:
            return create_client(url, key)
        except Exception:
            pass
    return create_client(url, key)

def get_team_base_data(team_name: str) -> dict:
    """
    Supabaseの `teams` テーブルからチームの基礎データを取得します。
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('teams').select('*').eq('name', team_name).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(f"Supabase fetch error: {e}")
        
    return {"name": team_name, "base_elo": 1500.0, "avg_goals": 1.0, "group_name": "A", "market_value": 50.0, "tactics_style": "balanced"}

def get_weighted_avg_goals(team_name: str, fallback_value: float) -> float:
    """
    Supabaseの `historical_matches` テーブルから、試合重要度（W杯: 4.0, 大陸大会: 2.0, 予選: 1.5, その他: 1.0）
    に基づいた加重平均得点力を動的に計算します。
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('historical_matches').select('*').or_(
            f"home_team.eq.{team_name},away_team.eq.{team_name}"
        ).execute()
        
        matches = response.data
        if not matches:
            return fallback_value
            
        total_weighted_goals = 0.0
        total_weight = 0.0
        
        for m in matches:
            goals = m["home_score"] if m["home_team"] == team_name else m["away_score"]
            
            # 重要度の重み付け
            tourney = m["tournament"].lower()
            if "world cup" in tourney and "qualification" not in tourney:
                weight = 4.0
            elif any(x in tourney for x in ["copa américa", "copa america", "euro", "african cup", "asian cup", "gold cup"]):
                weight = 2.0
            elif "qualification" in tourney or "qualifiers" in tourney:
                weight = 1.5
            else:
                weight = 1.0
                
            total_weighted_goals += goals * weight
            total_weight += weight
            
        if total_weight > 0:
            return total_weighted_goals / total_weight
    except Exception as e:
        print(f"Error calculating weighted avg goals for {team_name}: {e}")
        
    return fallback_value

def get_h2h_matches(team_a: str, team_b: str) -> list:
    """
    Supabaseの `historical_matches` テーブルから2チーム間の過去の対戦データを取得します。
    """
    try:
        supabase = get_supabase_client()
        # team_a vs team_b or team_b vs team_a
        response = supabase.table('historical_matches').select('*').or_(
            f"and(home_team.eq.{team_a},away_team.eq.{team_b}),and(home_team.eq.{team_b},away_team.eq.{team_a})"
        ).order('date', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Supabase H2H fetch error: {e}")
    return []

def get_all_teams_data() -> list:
    """
    Supabaseから全48チームのデータを取得します（シミュレーション用）。
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('teams').select('*').execute()
        if response.data:
            return response.data
    except Exception as e:
        print(f"Supabase all teams fetch error: {e}")
    return []
