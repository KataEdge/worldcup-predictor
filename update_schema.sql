-- teamsテーブルの再構築
DROP TABLE IF EXISTS teams CASCADE;
CREATE TABLE teams (
  name TEXT PRIMARY KEY,
  base_elo NUMERIC NOT NULL,
  avg_goals NUMERIC NOT NULL,
  group_name TEXT NOT NULL,
  market_value NUMERIC NOT NULL DEFAULT 50,
  tactics_style TEXT NOT NULL DEFAULT 'balanced'
);

-- 歴史的対戦データおよび2026年大会の試合データを格納するテーブル
DROP TABLE IF EXISTS historical_matches CASCADE;
CREATE TABLE historical_matches (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_score INT NOT NULL,
  away_score INT NOT NULL,
  tournament TEXT NOT NULL
);
