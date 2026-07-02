---
name: run_qa
description: Run full quality assurance checks including Ruff linting, formatting, and pytest tests with code coverage.
---

# Skill: Run QA Checks

Use this skill when you want to verify that all modifications to the python codebase (such as `app.py`, `db.py`, `graph.py`, `state.py`, or `update_db.py`) are correct, correctly formatted, and do not introduce any regressions.

## Steps

1. Run the unified QA verification helper script using the project's virtual environment:
   ```bash
   PYTHONPATH=. .venv/bin/python /Users/mikkatagiri/.gemini/antigravity-ide/brain/3a0979b3-bc00-4454-b301-896de5f334ad/scratch/run_qa.py
   ```
2. Inspect the output report:
   - Ensure the Ruff Lint Check displays "Ruff lint check passed!".
   - Ensure the Ruff Format Check displays "Ruff formatting is correct!".
   - Ensure the Test & Coverage summary displays "All pytest tests passed successfully!" along with the coverage table.
3. If there are failures:
   - For lint/format issues, run `.venv/bin/ruff format .` or `.venv/bin/ruff check --fix .` to automatically fix them.
   - For test failures, inspect the traceback in the report, fix the bugs in the code, and re-run this QA skill.
