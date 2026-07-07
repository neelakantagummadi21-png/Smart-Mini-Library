# Testing notes (Smart-Mini-Library)

## What was verified without running the server
- Flask app structure in `app.py`:
  - SQLite schema creation + seeding (sample books + demo user)
  - Routes exist for: `/`, `/login`, `/logout`, `/search`, `/recommendations`, `/book/<id>`, `/progress/<id>`, `/summarize`
  - Deterministic “AI-like” functions are self-contained (no external API calls)

- Template variable consistency was checked by reading templates:
  - `templates/base.html` uses `user` for auth state.
  - `templates/index.html` expects `top_books`.
  - `templates/search.html` expects `query`, `results`, `ai_resources`.
  - `templates/recommendations.html` expects `query`, `recommendations`.
  - `templates/book.html` expects `book`, `percent`.
  - `templates/summarize.html` expects `summary`, `input_text`.

## What could not be executed automatically in this environment
Attempts to run CLI commands failed due to command-separator / executable-resolution issues in the current tool shell (PowerShell syntax errors around `&&`, `&`, and `python` availability).

## How to run the app locally (manual)
1. `cd Smart-Mini-Library`
2. Create venv: `python -m venv .venv` then activate
3. Install: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Test flows:
   - Open `http://127.0.0.1:5000/`
   - Login with `demo` / `demo123`
   - Use Search, Recommendations, open a Book and update Progress, then Summarize.

