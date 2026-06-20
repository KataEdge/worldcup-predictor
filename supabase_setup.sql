-- テーブルの作成
CREATE TABLE teams (
  name TEXT PRIMARY KEY,
  base_elo NUMERIC NOT NULL,
  avg_goals NUMERIC NOT NULL
);

-- 初期データの挿入
INSERT INTO teams (name, base_elo, avg_goals) VALUES
('Japan', 1600.0, 1.5),
('Brazil', 2000.0, 2.5),
('Germany', 1900.0, 2.0),
('Spain', 1950.0, 2.2);
