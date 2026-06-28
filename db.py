import os
import sqlite3
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worldcup.db")

TEAMS_DATA = [
    # Group A
    {
        "name": "Mexico",
        "base_elo": 1820,
        "avg_goals": 1.6,
        "group_name": "A",
        "market_value": 220,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "South Africa",
        "base_elo": 1580,
        "avg_goals": 1.1,
        "group_name": "A",
        "market_value": 25,
        "tactics_style": "counter",
        "pk_rating": 3,
    },
    {
        "name": "South Korea",
        "base_elo": 1800,
        "avg_goals": 1.5,
        "group_name": "A",
        "market_value": 170,
        "tactics_style": "counter",
        "pk_rating": 3,
    },
    {
        "name": "Czechia",
        "base_elo": 1720,
        "avg_goals": 1.3,
        "group_name": "A",
        "market_value": 140,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    # Group B
    {
        "name": "Canada",
        "base_elo": 1700,
        "avg_goals": 1.4,
        "group_name": "B",
        "market_value": 180,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    {
        "name": "Bosnia and Herzegovina",
        "base_elo": 1640,
        "avg_goals": 1.2,
        "group_name": "B",
        "market_value": 55,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Qatar",
        "base_elo": 1680,
        "avg_goals": 1.3,
        "group_name": "B",
        "market_value": 20,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Switzerland",
        "base_elo": 1880,
        "avg_goals": 1.5,
        "group_name": "B",
        "market_value": 280,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    # Group C
    {
        "name": "Brazil",
        "base_elo": 2030,
        "avg_goals": 2.2,
        "group_name": "C",
        "market_value": 1100,
        "tactics_style": "possession",
        "pk_rating": 4,
    },
    {
        "name": "Morocco",
        "base_elo": 1910,
        "avg_goals": 1.6,
        "group_name": "C",
        "market_value": 350,
        "tactics_style": "counter",
        "pk_rating": 4,
    },
    {
        "name": "Haiti",
        "base_elo": 1510,
        "avg_goals": 1.1,
        "group_name": "C",
        "market_value": 15,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Scotland",
        "base_elo": 1680,
        "avg_goals": 1.3,
        "group_name": "C",
        "market_value": 220,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    # Group D
    {
        "name": "United States",
        "base_elo": 1850,
        "avg_goals": 1.7,
        "group_name": "D",
        "market_value": 330,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    {
        "name": "Paraguay",
        "base_elo": 1750,
        "avg_goals": 1.1,
        "group_name": "D",
        "market_value": 130,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Australia",
        "base_elo": 1760,
        "avg_goals": 1.4,
        "group_name": "D",
        "market_value": 45,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Türkiye",
        "base_elo": 1770,
        "avg_goals": 1.4,
        "group_name": "D",
        "market_value": 320,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    # Group E
    {
        "name": "Germany",
        "base_elo": 1920,
        "avg_goals": 1.9,
        "group_name": "E",
        "market_value": 850,
        "tactics_style": "press",
        "pk_rating": 5,
    },
    {
        "name": "Curaçao",
        "base_elo": 1450,
        "avg_goals": 1.0,
        "group_name": "E",
        "market_value": 15,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Côte d'Ivoire",
        "base_elo": 1730,
        "avg_goals": 1.3,
        "group_name": "E",
        "market_value": 280,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Ecuador",
        "base_elo": 1820,
        "avg_goals": 1.3,
        "group_name": "E",
        "market_value": 260,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    # Group F
    {
        "name": "Netherlands",
        "base_elo": 1980,
        "avg_goals": 2.0,
        "group_name": "F",
        "market_value": 720,
        "tactics_style": "possession",
        "pk_rating": 2,
    },
    {
        "name": "Japan",
        "base_elo": 1930,
        "avg_goals": 1.8,
        "group_name": "F",
        "market_value": 310,
        "tactics_style": "counter",
        "pk_rating": 2,
    },
    {
        "name": "Sweden",
        "base_elo": 1840,
        "avg_goals": 1.6,
        "group_name": "F",
        "market_value": 270,
        "tactics_style": "counter",
        "pk_rating": 3,
    },
    {
        "name": "Tunisia",
        "base_elo": 1620,
        "avg_goals": 1.1,
        "group_name": "F",
        "market_value": 45,
        "tactics_style": "counter",
        "pk_rating": 3,
    },
    # Group G
    {
        "name": "Belgium",
        "base_elo": 1950,
        "avg_goals": 1.8,
        "group_name": "G",
        "market_value": 560,
        "tactics_style": "possession",
        "pk_rating": 3,
    },
    {
        "name": "Egypt",
        "base_elo": 1740,
        "avg_goals": 1.2,
        "group_name": "G",
        "market_value": 120,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Iran",
        "base_elo": 1810,
        "avg_goals": 1.4,
        "group_name": "G",
        "market_value": 45,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "New Zealand",
        "base_elo": 1480,
        "avg_goals": 1.0,
        "group_name": "G",
        "market_value": 25,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    # Group H
    {
        "name": "Spain",
        "base_elo": 2050,
        "avg_goals": 2.1,
        "group_name": "H",
        "market_value": 1000,
        "tactics_style": "possession",
        "pk_rating": 2,
    },
    {
        "name": "Cabo Verde",
        "base_elo": 1590,
        "avg_goals": 1.1,
        "group_name": "H",
        "market_value": 25,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Saudi Arabia",
        "base_elo": 1650,
        "avg_goals": 1.2,
        "group_name": "H",
        "market_value": 30,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Uruguay",
        "base_elo": 1950,
        "avg_goals": 1.7,
        "group_name": "H",
        "market_value": 480,
        "tactics_style": "counter",
        "pk_rating": 3,
    },
    # Group I
    {
        "name": "France",
        "base_elo": 2080,
        "avg_goals": 2.2,
        "group_name": "I",
        "market_value": 1250,
        "tactics_style": "possession",
        "pk_rating": 4,
    },
    {
        "name": "Senegal",
        "base_elo": 1830,
        "avg_goals": 1.4,
        "group_name": "I",
        "market_value": 230,
        "tactics_style": "counter",
        "pk_rating": 3,
    },
    {
        "name": "Iraq",
        "base_elo": 1610,
        "avg_goals": 1.2,
        "group_name": "I",
        "market_value": 15,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Norway",
        "base_elo": 1780,
        "avg_goals": 1.5,
        "group_name": "I",
        "market_value": 420,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    # Group J
    {
        "name": "Argentina",
        "base_elo": 2100,
        "avg_goals": 2.2,
        "group_name": "J",
        "market_value": 950,
        "tactics_style": "possession",
        "pk_rating": 5,
    },
    {
        "name": "Algeria",
        "base_elo": 1720,
        "avg_goals": 1.3,
        "group_name": "J",
        "market_value": 160,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Austria",
        "base_elo": 1820,
        "avg_goals": 1.5,
        "group_name": "J",
        "market_value": 240,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    {
        "name": "Jordan",
        "base_elo": 1600,
        "avg_goals": 1.2,
        "group_name": "J",
        "market_value": 15,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    # Group K
    {
        "name": "Portugal",
        "base_elo": 2020,
        "avg_goals": 2.0,
        "group_name": "K",
        "market_value": 980,
        "tactics_style": "possession",
        "pk_rating": 4,
    },
    {
        "name": "DR Congo",
        "base_elo": 1560,
        "avg_goals": 1.1,
        "group_name": "K",
        "market_value": 60,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Uzbekistan",
        "base_elo": 1620,
        "avg_goals": 1.2,
        "group_name": "K",
        "market_value": 35,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Colombia",
        "base_elo": 1960,
        "avg_goals": 1.6,
        "group_name": "K",
        "market_value": 360,
        "tactics_style": "counter",
        "pk_rating": 4,
    },
    # Group L
    {
        "name": "England",
        "base_elo": 2040,
        "avg_goals": 2.0,
        "group_name": "L",
        "market_value": 1300,
        "tactics_style": "press",
        "pk_rating": 3,
    },
    {
        "name": "Croatia",
        "base_elo": 1940,
        "avg_goals": 1.5,
        "group_name": "L",
        "market_value": 320,
        "tactics_style": "counter",
        "pk_rating": 5,
    },
    {
        "name": "Ghana",
        "base_elo": 1550,
        "avg_goals": 1.1,
        "group_name": "L",
        "market_value": 120,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
    {
        "name": "Panama",
        "base_elo": 1630,
        "avg_goals": 1.2,
        "group_name": "L",
        "market_value": 12,
        "tactics_style": "balanced",
        "pk_rating": 3,
    },
]


def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL", "")
    key: str = os.environ.get("SUPABASE_KEY", "")
    if url and not url.startswith("http"):
        url = f"https://{url}.supabase.co"
    if not url or not key:
        raise ValueError("Supabase credentials not set or invalid")
    return create_client(url, key)


def get_sqlite_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite_db():
    """
    Local SQLite DB を初期化し、テーブル作成・初期データの挿入を行います。
    """
    try:
        conn = get_sqlite_conn()
        cursor = conn.cursor()

        # teams テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                name TEXT PRIMARY KEY,
                base_elo REAL,
                avg_goals REAL,
                group_name TEXT,
                market_value REAL,
                tactics_style TEXT,
                pk_rating INTEGER
            )
        """)

        # historical_matches テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_score INTEGER,
                away_score INTEGER,
                tournament TEXT
            )
        """)

        # teams テーブルが空なら初期データ挿入
        cursor.execute("SELECT COUNT(*) FROM teams")
        if cursor.fetchone()[0] == 0:
            print("Initializing local SQLite teams data...")
            for team in TEAMS_DATA:
                cursor.execute(
                    """
                    INSERT INTO teams (name, base_elo, avg_goals, group_name, market_value, tactics_style, pk_rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        team["name"],
                        team["base_elo"],
                        team["avg_goals"],
                        team["group_name"],
                        team["market_value"],
                        team["tactics_style"],
                        team["pk_rating"],
                    ),
                )
            conn.commit()

        # historical_matches テーブルが空ならCSVから同期
        cursor.execute("SELECT COUNT(*) FROM historical_matches")
        if cursor.fetchone()[0] == 0:
            print("Initializing local SQLite historical matches data...")
            url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
            try:
                df = pd.read_csv(url)
                df["date"] = pd.to_datetime(df["date"])
                df = df[df["date"] >= "2018-01-01"]

                team_names = {t["name"] for t in TEAMS_DATA}
                filtered_df = df[
                    df["home_team"].isin(team_names) & df["away_team"].isin(team_names)
                ]
                filtered_df = filtered_df.dropna(subset=["home_score", "away_score"])

                for _, row in filtered_df.iterrows():
                    cursor.execute(
                        """
                        INSERT INTO historical_matches (date, home_team, away_team, home_score, away_score, tournament)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            row["date"].strftime("%Y-%m-%d"),
                            row["home_team"],
                            row["away_team"],
                            int(row["home_score"]),
                            int(row["away_score"]),
                            row["tournament"],
                        ),
                    )
                conn.commit()
                print(f"Synchronized {len(filtered_df)} matches to local SQLite.")
            except Exception as e:
                print(f"Failed to fetch historical matches from internet: {e}")

        conn.close()
    except Exception as e:
        print(f"SQLite initialization failed: {e}")


def get_team_base_data(team_name: str) -> dict:
    """
    teams テーブルからチームの基礎データを取得します。Supabaseが使えなければSQLiteを使用します。
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("teams").select("*").eq("name", team_name).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        print(
            f"Supabase fetch error for team {team_name}: {e}. Falling back to SQLite."
        )

    return get_team_base_data_sqlite(team_name)


def get_team_base_data_sqlite(team_name: str) -> dict:
    try:
        init_sqlite_db()
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams WHERE name = ?", (team_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception as e:
        print(f"SQLite fetch error: {e}")
    # 最終フォールバック
    for team in TEAMS_DATA:
        if team["name"] == team_name:
            return team
    return {
        "name": team_name,
        "base_elo": 1500.0,
        "avg_goals": 1.0,
        "group_name": "A",
        "market_value": 50.0,
        "tactics_style": "balanced",
        "pk_rating": 3,
    }


def calc_weighted_goals(matches: list, team_name: str, fallback_value: float) -> float:
    total_weighted_goals = 0.0
    total_weight = 0.0
    for m in matches:
        goals = m["home_score"] if m["home_team"] == team_name else m["away_score"]
        tourney = m["tournament"].lower()
        if "world cup" in tourney and "qualification" not in tourney:
            weight = 4.0
        elif any(
            x in tourney
            for x in [
                "copa américa",
                "copa america",
                "euro",
                "african cup",
                "asian cup",
                "gold cup",
            ]
        ):
            weight = 2.0
        elif "qualification" in tourney or "qualifiers" in tourney:
            weight = 1.5
        else:
            weight = 1.0

        total_weighted_goals += goals * weight
        total_weight += weight

    if total_weight > 0:
        return total_weighted_goals / total_weight
    return fallback_value


def get_weighted_avg_goals(team_name: str, fallback_value: float) -> float:
    """
    historical_matches テーブルから、試合重要度に基づいた加重平均得点力を動的に計算します。
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("historical_matches")
            .select("*")
            .or_(f"home_team.eq.{team_name},away_team.eq.{team_name}")
            .execute()
        )

        matches = response.data
        if matches:
            return calc_weighted_goals(matches, team_name, fallback_value)
    except Exception as e:
        print(
            f"Supabase fetch error for weighted avg goals of {team_name}: {e}. Falling back to SQLite."
        )

    return get_weighted_avg_goals_sqlite(team_name, fallback_value)


def get_weighted_avg_goals_sqlite(team_name: str, fallback_value: float) -> float:
    try:
        init_sqlite_db()
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM historical_matches WHERE home_team = ? OR away_team = ?",
            (team_name, team_name),
        )
        rows = cursor.fetchall()
        conn.close()

        matches = [dict(r) for r in rows]
        if matches:
            return calc_weighted_goals(matches, team_name, fallback_value)
    except Exception as e:
        print(f"SQLite weighted avg goals error: {e}")
    return fallback_value


def get_h2h_matches(team_a: str, team_b: str) -> list:
    """
    historical_matches テーブルから2チーム間の過去の対戦データを取得します。
    """
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("historical_matches")
            .select("*")
            .or_(
                f"and(home_team.eq.{team_a},away_team.eq.{team_b}),and(home_team.eq.{team_b},away_team.eq.{team_a})"
            )
            .order("date", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Supabase H2H fetch error: {e}. Falling back to SQLite.")

    return get_h2h_matches_sqlite(team_a, team_b)


def get_h2h_matches_sqlite(team_a: str, team_b: str) -> list:
    try:
        init_sqlite_db()
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM historical_matches 
            WHERE (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
            ORDER BY date DESC
        """,
            (team_a, team_b, team_b, team_a),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"SQLite H2H fetch error: {e}")
    return []


def get_all_teams_data() -> list:
    """
    全48チームのデータを取得します。
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("teams").select("*").execute()
        if response.data:
            return response.data
    except Exception as e:
        print(f"Supabase all teams fetch error: {e}. Falling back to SQLite.")

    return get_all_teams_data_sqlite()


def get_all_teams_data_sqlite() -> list:
    try:
        init_sqlite_db()
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teams")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"SQLite all teams fetch error: {e}")
    return []
