# Smart Mini Library

An AI-powered digital learning platform built using **Python (Flask)**, **HTML**, **CSS**, and **SQLite**.

> Note: AI features in this project are implemented as lightweight, deterministic “AI-like” utilities (no external API calls), so it works out-of-the-box.

## Features

- AI Book Recommendations (simple content-based + popularity fallback)
- Smart Search
- User Login
- Reading Progress Tracking
- Article Summarization (extractive, deterministic)
- Responsive UI

## Technologies

- Python
- Flask
- SQLite
- HTML/CSS

## Setup & Run

### 1) Create/activate virtual environment
**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```powershell
pip install -r requirements.txt
```

### 3) Run the app
```powershell
python app.py
```

Open:
- http://127.0.0.1:5000

## Database

- SQLite database file: `library.db`
- On first run, the app will create tables and seed sample data.

## Project Structure

- `app.py` - Flask server
- `templates/` - HTML templates
- `static/` - CSS/JS/images
- `library.db` - SQLite database
- `images/` - optional image assets

