# World Cup Predictor - Workspace Rules for AI Agents

Welcome! This workspace contains a 2026 World Cup AI Predictor application that runs Monte Carlo simulations and multi-agent debates (using LangGraph) to analyze football matches.

Please adhere to the following rules and specifications when working in this codebase.

---

## 🛠️ Technology Stack

- **Backend Logic**: Python 3.12+ (Virtual environment is located at `.venv/`)
- **Agent Orchestration**: LangGraph, LangChain, and Google Generative AI (Gemini 2.5/1.5)
- **Database**: SQLite (`worldcup.db` for local operations) & Supabase integration (`db.py`, `update_db.py`)
- **Frontend UI**: Streamlit (`app.py`)
- **Testing & Quality**: `pytest` for tests, `ruff` for linting and code formatting

---

## 🏗️ Core Architecture & Flow

The predictor works through a multi-agent debate workflow:
1. **Debate Agent A Node**: Initial argument for Team A (Home).
2. **Debate Agent B Node**: Initial argument & rebuttal for Team B (Away).
3. **Rebuttal A Node**: Rebuttal argument from Team A.
4. **Rebuttal B Node**: Final rebuttal argument from Team B.
5. **Debate Synthesizer Node**: Synthesizes the debate history.
6. **Summary Node**: Translates findings into tactical modifiers.
7. **Calc Node**: Calculates actual expected goals ($xG$), probabilities, and win/draw distributions.

---

## 🚨 Guidelines & Constraints

### 1. Code Quality & Formatting
- **Linting & Formatting**: Always run `ruff check` and `ruff format` before completing your changes.
- **Imports**: Ensure `PYTHONPATH=.` is set when running scripts or testing, so Python can resolve imports like `db.py` and `graph.py` from the root of the project.

### 2. Testing Constraints
- All tests must pass before you finish execution.
- Tests are located in the `tests/` directory. Run tests using:
  ```bash
  PYTHONPATH=. .venv/bin/pytest
  ```
- Coverage can be checked with `pytest-cov`.

### 3. Graceful LLM Failures (Crucial)
- The LangGraph nodes depend on `GOOGLE_API_KEY` for LLM debate output.
- **Rule**: If the environment variable `GOOGLE_API_KEY` is missing or empty, all LangGraph nodes **MUST** fall back to mock or default values instead of crashing. This ensures tests and offline simulations always complete successfully.

### 4. Database Seeding & Schema Changes
- Local data is stored in `worldcup.db`.
- Schema setup can be seen in `supabase_setup.sql` and `update_schema.sql`.
- If you edit team ratings or add features, make sure `db.py` queries are aligned and `tests/test_db.py` is updated.
