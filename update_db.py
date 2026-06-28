import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

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
        raise ValueError("Supabase URL or Key not set")
    return create_client(url, key)


def update_teams(supabase: Client):
    print("Updating teams table on Supabase...")
    # 一旦既存のデータをクリアして再挿入
    supabase.table("teams").delete().neq("name", "").execute()

    # バルクインサート
    response = supabase.table("teams").insert(TEAMS_DATA).execute()
    print(f"Inserted {len(response.data)} teams to Supabase.")


def sync_matches(supabase: Client):
    print("Fetching matches from GitHub (martj42/international_results)...")
    url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
    try:
        df = pd.read_csv(url)
    except Exception as e:
        print(f"Failed to download match results: {e}")
        return

    print(f"Total matches in dataset: {len(df)}")

    # 日付型に変換
    df["date"] = pd.to_datetime(df["date"])

    # 2018年以降のデータをフィルタ
    df = df[df["date"] >= "2018-01-01"]

    # 出場48チームの名前のリスト
    team_names = {t["name"] for t in TEAMS_DATA}

    # 両チームが出場48チームに含まれる試合のみを抽出
    filtered_df = df[
        df["home_team"].isin(team_names) & df["away_team"].isin(team_names)
    ]

    # まだ行われていない未消化の試合（スコアがNaN）を除外する
    filtered_df = filtered_df.dropna(subset=["home_score", "away_score"])
    print(
        f"Filtered matches (both teams in World Cup, since 2018, played): {len(filtered_df)}"
    )

    # Supabaseに送るための辞書型リストを作成
    matches_to_insert = []
    for _, row in filtered_df.iterrows():
        matches_to_insert.append(
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "home_score": int(row["home_score"]),
                "away_score": int(row["away_score"]),
                "tournament": row["tournament"],
            }
        )

    # 一旦既存のデータをクリア
    supabase.table("historical_matches").delete().neq("id", -1).execute()

    # データを分割してインサート (Supabaseの制限対策)
    chunk_size = 500
    for i in range(0, len(matches_to_insert), chunk_size):
        chunk = matches_to_insert[i : i + chunk_size]
        supabase.table("historical_matches").insert(chunk).execute()

    print(f"Synchronized {len(matches_to_insert)} matches to Supabase.")


def update_sqlite():
    print("Updating local SQLite database...")
    import sqlite3
    from db import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create/Clean teams table
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
    cursor.execute("DELETE FROM teams")

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
    print(f"Updated {len(TEAMS_DATA)} teams in SQLite.")

    # Create/Clean historical_matches table
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
    cursor.execute("DELETE FROM historical_matches")

    print("Fetching matches from GitHub for SQLite...")
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
        print(f"Failed to download or sync matches for SQLite: {e}")

    conn.close()


if __name__ == "__main__":
    # 1. Try Supabase
    try:
        print("Attempting to update Supabase...")
        supabase = get_supabase_client()
        update_teams(supabase)
        sync_matches(supabase)
        print("Supabase update completed successfully.")
    except Exception as e:
        print(f"Supabase update skipped/failed: {e}")

    # 2. Update SQLite
    try:
        update_sqlite()
        print("Local SQLite database update completed successfully.")
    except Exception as e:
        print(f"Local SQLite update failed: {e}")
