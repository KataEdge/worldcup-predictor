---
name: run_match_simulation
description: Run a terminal-based match simulation between two World Cup teams using the LangGraph engine.
---

# Skill: Run Match Simulation

Use this skill when you need to dry-run or smoke-test a single match prediction between two countries. This checks that SQLite database queries, LangGraph node steps, LLM connectivity (via Gemini), and the final mathematical scoring logic work end-to-end.

## Steps

1. Run the simulation runner script using the project's virtual environment:
   ```bash
   PYTHONPATH=. .venv/bin/python /Users/mikkatagiri/.gemini/antigravity-ide/brain/3a0979b3-bc00-4454-b301-896de5f334ad/scratch/simulate.py --team_a "Japan" --team_b "Brazil"
   ```
2. You can customize the match condition using the following optional flags:
   - `--team_a`: Home team name (e.g. "Japan", "Brazil", "Germany", "Argentina")
   - `--team_b`: Away team name
   - `--stadium`: Stadium name
   - `--stadium_env`: Stadium environment (`standard`, `altitude`, `turf`, or `heat`)
   - `--rest_a`: Rest days for team A (integer, e.g. 2, 3, 4)
   - `--rest_b`: Rest days for team B (integer)

   *Example Command with options:*
   ```bash
   PYTHONPATH=. .venv/bin/python /Users/mikkatagiri/.gemini/antigravity-ide/brain/3a0979b3-bc00-4454-b301-896de5f334ad/scratch/simulate.py --team_a "Germany" --team_b "Spain" --stadium_env "heat" --rest_a 3
   ```
3. Inspect the terminal output:
   - Verify that the base stats, weighted goals, and H2H matches are loaded from the SQLite database.
   - Verify the sports journalist debate arguments are printed under "DEBATE HISTORY".
   - Verify the judge's summary and team score multipliers are printed under "TACTICAL SUMMARY & MODIFIERS".
   - Verify the expected goals, win/draw probabilities, and the final match summary are correctly printed under "FINAL SIMULATION RESULTS".
