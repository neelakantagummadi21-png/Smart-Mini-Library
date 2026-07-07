import os
import sqlite3
from datetime import datetime
from typing import List, Optional

from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import hashlib

from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "library.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["TEMPLATES_AUTO_RELOAD"] = True


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(BASE_DIR, exist_ok=True)
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            description TEXT,
            tags TEXT,
            popularity INTEGER DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            percent INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, book_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
        """
    )

    conn.commit()

    # Seed sample data (if empty)
    cur.execute("SELECT COUNT(*) AS c FROM books")
    count = cur.fetchone()["c"]
    if count == 0:
        sample_books = [
            (
                "Clean Code",
                "Robert C. Martin",
                "A practical guide to writing code that is easy to understand and maintain.",
                "programming,software-engineering,clean-code",
                120,
            ),
            (
                "Fluent Python",
                "Luciano Ramalho",
                "Techniques for writing idiomatic Python using modern features and best practices.",
                "python,programming,idioms",
                105,
            ),
            (
                "Design Patterns",
                "Erich Gamma et al.",
                "Common solutions to recurring software design problems.",
                "software-architecture,patterns,design",
                98,
            ),
            (
                "Deep Learning with Python",
                "François Chollet",
                "Learn deep learning concepts and build neural networks using Keras.",
                "ai,deep-learning,python",
                130,
            ),
            (
                "Atomic Habits",
                "James Clear",
                "Create systems and habits for lasting change through small, incremental improvements.",
                "productivity,habits,learning",
                160,
            ),
        ]
        cur.executemany(
            "INSERT INTO books (title, author, description, tags, popularity) VALUES (?, ?, ?, ?, ?)",
            sample_books,
        )
        conn.commit()

    # Seed demo user (if not exists)
    username = "demo"
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone() is None:
        password_hash = generate_password_hash("demo123")
        cur.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.utcnow().isoformat()),
        )
        conn.commit()

    conn.close()


@app.before_request
def before_request():
    g.db = get_db()


@app.teardown_request
def teardown_request(exception=None):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return g.db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    for ch in [",", ".", "!", "?", ";", ":", "-", "_", "/", "\\"]:
        s = s.replace(ch, " ")
    return [t for t in s.split() if t]


def recommend_books(query: str, limit: int = 5):
    # Deterministic “AI-like” recommendation using term overlap.
    terms = set(tokenize(query))
    cur = g.db

    books = cur.execute("SELECT * FROM books").fetchall()
    scored = []
    for b in books:
        blob = " ".join([b["title"], b["author"], b["description"], b["tags"]])
        b_terms = set(tokenize(blob))
        overlap = len(terms.intersection(b_terms))
        # popularity acts as tie-breaker
        score = overlap * 10 + int(b["popularity"] or 0) / 10
        scored.append((score, b))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:limit]]


def build_learning_resources(topic: str) -> dict:
    """Deterministic offline 'AI-like' learning resources for a topic."""
    topic_clean = (topic or "").strip()
    if not topic_clean:
        topic_clean = "machine learning"

    # Small helpers
    def b(title, value):
        return {"title": title, "value": value}

    # Keep content compact (still covers 1–20 sections).
    overview = (
        f"**{topic_clean}** is a field/topic that combines core concepts with practical methods. "
        "Beginner learning focuses on fundamentals and vocabulary; intermediate learning builds hands-on skills; "
        "advanced learning emphasizes design trade-offs, evaluation, and deeper theoretical understanding."
    )
    why = (
        "It matters because it powers modern tools, improves productivity, and helps engineers/analysts "
        "solve real problems with measurable outcomes."
    )
    history = (
        "Over time, the topic evolved from early ideas and manual techniques into scalable methods, "
        "supported by better data, compute, and evaluation frameworks."
    )
    applications = (
        "Real-world applications include building intelligent features in products, automating workflows, "
        "analyzing data at scale, and supporting decision-making in domains like education, healthcare, "
        "finance, and software engineering."
    )

    roadmap = {
        "Beginner": ["Learn key terminology and basic workflow", "Build small projects", "Understand evaluation basics"],
        "Intermediate": ["Implement end-to-end pipelines", "Compare approaches", "Improve reliability and performance"],
        "Advanced": ["Design for constraints (latency, cost, data quality)", "Advanced evaluation & debugging", "Optimization and architecture"],
        "Expert": ["Lead system design & research direction", "Publish/teach and mentor", "Set standards for benchmarks and safety"],
    }

    # Deterministic generic recommendations.
    books = [
        ("Practical Guide to " + topic_clean.title(), "A. Author", "4.5/5", "Beginner–Intermediate", "Good starting structure and examples."),
        ("Engineering " + topic_clean.title(), "B. Researcher", "4.6/5", "Intermediate", "Focuses on real systems and trade-offs."),
        ("Advanced Topics in " + topic_clean.title(), "C. Expert", "4.7/5", "Advanced", "Deep dives and evaluation methods."),
    ]

    papers = [
        ("Foundations of Modern " + topic_clean.title(), "Classic baseline paper", "Introduces the core problem formulation and evaluation."),
        ("A Key Improvement on " + topic_clean.title(), "Influential method paper", "Presents a major performance/quality upgrade with analysis."),
        ("Benchmarking & Best Practices for " + topic_clean.title(), "Benchmark paper", "Defines robust evaluation protocols and failure modes."),
    ]

    courses = [
        ("Coursera", "Search courses for: " + topic_clean),
        ("edX", "Search courses for: " + topic_clean),
        ("Udemy", "Search courses for: " + topic_clean),
        ("NPTEL", "Search courses for: " + topic_clean),
        ("YouTube", "Search: " + topic_clean + " + tutorial"),
    ]

    docs = [
        ("Official docs", "Use the official documentation of the primary libraries/tools in this area."),
        ("Community guides", "Look for maintained guides/tutorials and style references."),
    ]

    github = [
        ("Awesome-curated list", "Search GitHub for 'awesome-' + topic_clean"),
        ("Reference implementations", "Look for repos with benchmarks and docs"),
    ]

    tools = ["Vector DB / indexing", "Notebook + experimentation", "Evaluation harnesses", "Experiment tracking" ]
    frameworks = ["Popular ML/AI framework (latest stable)", "Web framework for integration", "Data processing toolkit"]

    industry = (
        "Companies use these methods to build features like intelligent search, "
        "personalization, automation, and analytics. They rely on evaluation pipelines, "
        "monitoring, and reproducible experiments."
    )

    career = {
        "Required skills": ["Programming", "Data & math basics (as applicable)", "Evaluation and debugging"],
        "Job roles": ["ML/AI Engineer", "Software Engineer (AI),", "Research Engineer", "Data Scientist"],
        "Salary range": "Varies by location; typically higher for specialized ML/AI roles.",
        "Career roadmap": ["Ship small projects", "Grow evaluation depth", "Own system design", "Lead/mentor"],
    }

    interviews = {
        "Basic": [f"What is {topic_clean} in simple terms?", "Explain a core workflow and why it matters."],
        "Intermediate": ["How do you evaluate quality and performance?", "Compare two approaches and justify trade-offs."],
        "Advanced": ["Design a robust system under constraints", "Debug a failing pipeline with metrics & logging"],
    }

    coding_examples = {
        "Python": "# Minimal example (pseudo)\n" 
                  f"topic = '{topic_clean}'\n" 
                  "# tokenize/prepare -> train/compute -> evaluate\n",
        "Java": "// Minimal example (pseudo)\n" 
                 "// load data -> run pipeline -> report metrics\n",
        "SQL": "-- Minimal example\n" 
                "SELECT ... WHERE ...;",
        "JavaScript": "// Minimal example (pseudo)\n" 
                       "// call API / render results\n",
    }

    practice = [
        f"Build a small project around {topic_clean}: dataset -> pipeline -> evaluation.",
        "Write a rubric to compare two approaches quantitatively.",
        "Create unit tests for preprocessing/feature steps.",
    ]

    trends = ["Better evaluation & benchmarks", "Smaller/faster models & efficient inference", "Tool-augmented workflows", "Multimodal systems (where applicable)"]
    similar_topics = ["Data engineering", "Optimization", "Information retrieval", "System design for ML"]

    learning_resources = ["Official docs", "Academic surveys", "Maintainer blogs", "Conference talks", "Open-source repos"]

    daily_challenge = {
        "Coding": f"Implement an evaluation loop for {topic_clean} and log metrics.",
        "Theory": f"Explain how {topic_clean} is evaluated and what can go wrong.",
    }

    summary = (
        f"{topic_clean}: learn fundamentals, build projects, then deepen evaluation and system design. "
        "Use deterministic, measurable progress: metrics, iteration, and reproducible experiments."
    )

    return {
        "topic": topic_clean,
        "sections": {
            1: b("Topic Overview", f"{overview}\n\n{history}\n\n{why}\n\n{applications}"),
            2: b("Latest News (offline preview)", "This demo runs offline, so news is simulated with evergreen trends and benchmark updates."),
            3: b("Learning Roadmap", roadmap),
            4: b("Recommended Books", books),
            5: b("Research Papers", papers),
            6: b("Online Courses", courses),
            7: b("Documentation", docs),
            8: b("GitHub Projects", github),
            9: b("Latest Tools", tools),
            10: b("Latest Frameworks", frameworks),
            11: b("Industry Applications", industry),
            12: b("Career Guidance", career),
            13: b("Interview Questions", interviews),
            14: b("Coding Examples", coding_examples),
            15: b("Practice Questions", practice),
            16: b("Latest Trends", trends),
            17: b("Similar Topics", similar_topics),
            18: b("Learning Resources", learning_resources),
            19: b("Daily Learning Challenge", daily_challenge),
            20: b("Summary", summary),
        },
    }


def summarize_article(text: str, max_sentences: int = 3) -> str:

    # Simple extractive summary: rank sentences by term frequency.
    if not text:
        return ""

    # Split sentences (naive)
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return ""

    words = [w for w in tokenize(text) if len(w) > 2]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    def score_sentence(sent: str) -> int:
        s_words = [w for w in tokenize(sent) if len(w) > 2]
        return sum(freq.get(w, 0) for w in s_words)

    ranked = sorted(sentences, key=score_sentence, reverse=True)
    picked = ranked[:max_sentences]

    # Preserve original order
    order_index = {s: i for i, s in enumerate(sentences)}
    picked.sort(key=lambda s: order_index.get(s, 0))
    return ". ".join(picked).strip() + ("." if picked else "")


@app.route("/")
def home():
    u = current_user()
    top_books = g.db.execute("SELECT * FROM books ORDER BY popularity DESC LIMIT 5").fetchall()
    return render_template("index.html", user=u, top_books=top_books)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = g.db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid credentials"), 401

        session["user_id"] = user["id"]
        return redirect(url_for("home"))

    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))


@app.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return redirect(url_for("home"))

    # Smart search: match in title/author/tags; deterministic rank by overlap + popularity.
    terms = set(tokenize(q))
    books = g.db.execute("SELECT * FROM books").fetchall()
    scored = []
    for b in books:
        blob = " ".join([b["title"], b["author"], b["tags"], b["description"]])
        b_terms = set(tokenize(blob))
        overlap = len(terms.intersection(b_terms))
        score = overlap * 10 + int(b["popularity"] or 0) / 10
        if overlap > 0 or (q.lower() in (b["title"] or "").lower()):
            scored.append((score, b))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [b for _, b in scored][:10]

    u = current_user()
    ai_resources = build_learning_resources(q)
    return render_template("search.html", user=u, query=q, results=results, ai_resources=ai_resources)



@app.route("/recommendations", methods=["GET"])
def recommendations():
    q = request.args.get("q", "").strip()
    if not q:
        q = "machine learning python"

    recs = recommend_books(q, limit=5)
    u = current_user()
    return render_template("recommendations.html", user=u, query=q, recommendations=recs)


@app.route("/book/<int:book_id>")
def book_details(book_id: int):
    u = current_user()
    book = g.db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        return redirect(url_for("home"))

    progress_row = None
    percent = 0
    if u:
        progress_row = g.db.execute(
            "SELECT * FROM user_progress WHERE user_id = ? AND book_id = ?",
            (u["id"], book_id),
        ).fetchone()
        percent = int(progress_row["percent"]) if progress_row else 0

    return render_template("book.html", user=u, book=book, percent=percent)


@app.route("/progress/<int:book_id>", methods=["POST"])
def update_progress(book_id: int):
    u = current_user()
    if not u:
        return redirect(url_for("login"))

    percent = request.form.get("percent", "0").strip()
    try:
        percent_i = max(0, min(100, int(percent)))
    except ValueError:
        percent_i = 0

    g.db.execute(
        """
        INSERT INTO user_progress (user_id, book_id, percent, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, book_id) DO UPDATE SET
            percent = excluded.percent,
            updated_at = excluded.updated_at
        """,
        (u["id"], book_id, percent_i, datetime.utcnow().isoformat()),
    )
    g.db.commit()

    return redirect(url_for("book_details", book_id=book_id))


@app.route("/summarize", methods=["GET", "POST"])
def summarize():
    u = current_user()
    summary = None
    input_text = ""
    if request.method == "POST":
        input_text = request.form.get("text", "")
        max_sentences = int(request.form.get("max_sentences", "3"))
        summary = summarize_article(input_text, max_sentences=max_sentences)

    return render_template("summarize.html", user=u, summary=summary, input_text=input_text)


def _stable_hash(s: str) -> int:
    if s is None:
        s = ""
    # Deterministic across runs.
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def generate_svg_cover_data_uri(topic: str) -> str:
    """Create a deterministic SVG cover and return it as a data URI."""
    t = (topic or "").strip() or "learning"
    h = _stable_hash(t)
    hue1 = h % 360
    hue2 = (h // 7) % 360
    hue3 = (h // 13) % 360
    initials = "".join([w[0].upper() for w in t.split() if w])[:3] or "AI"
    # Keep it simple and fast.
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='900' height='540' viewBox='0 0 900 540'>
      <defs>
        <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0%' stop-color='hsl({hue1},90%,55%)'/>
          <stop offset='50%' stop-color='hsl({hue2},90%,50%)'/>
          <stop offset='100%' stop-color='hsl({hue3},90%,45%)'/>
        </linearGradient>
        <filter id='noise'>
          <feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/>
          <feColorMatrix type='matrix' values='1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .08 0'/>
        </filter>
      </defs>
      <rect width='900' height='540' rx='34' fill='url(#g)'/>
      <rect width='900' height='540' rx='34' filter='url(#noise)' opacity='0.35'/>
      <circle cx='720' cy='130' r='120' fill='rgba(255,255,255,0.10)'/>
      <circle cx='740' cy='160' r='70' fill='rgba(0,0,0,0.08)'/>
      <g font-family='ui-sans-serif, system-ui, Segoe UI, Roboto, Arial' fill='white'>
        <text x='60' y='120' font-size='20' opacity='0.9'>Smart Mini Library</text>
        <text x='60' y='190' font-size='64' font-weight='800'>"{initials}"</text>
        <text x='60' y='250' font-size='22' opacity='0.95'>{t}</text>
      </g>
      <g>
        <path d='M70 360 C 180 300, 300 430, 420 370 S 650 350, 830 410' stroke='rgba(255,255,255,0.35)' stroke-width='10' fill='none' stroke-linecap='round'/>
      </g>
    </svg>"""
    import base64

    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"



        # Use existing recommender.
        recs = recommend_books(m, limit=5)
        if not recs:
            return "I couldn't find matching books. Try a different topic (e.g., Python, design patterns, deep learning)."
        lines = ["Here are some books I recommend:"]
        for b in recs:
            lines.append(f"- {b['title']} by {b['author']} (popularity {b['popularity']})")
        lines.append("\nTip: click a book to update your progress.")
        return "\n".join(lines)

    if "summarize" in lower or "summary" in lower:
        # If message includes text after colon, summarize that; else ask for input.
        parts = m.split(":", 1)
        text = parts[1].strip() if len(parts) > 1 else ""
        if not text:
            return "Paste text after a colon. Example: summarize: Your article text here..."
        return "Summary:\n" + summarize_article(text, max_sentences=3)

    # Default: learning roadmap / AI-like resources.
    resources = build_learning_resources(m)
    topic = resources.get("topic")
    sections = resources.get("sections")
    overview = sections[1]["value"] if sections and 1 in sections else ""
    roadmap = sections[3]["value"] if sections and 3 in sections else {}
    # Render a concise actionable answer.
    lines = [f"Learning roadmap for: {topic}", "", "Quick overview:", overview, "", "Roadmap:"]
    if isinstance(roadmap, dict):
        for lvl in ["Beginner", "Intermediate", "Advanced", "Expert"]:
            items = roadmap.get(lvl, [])
            if items:
                lines.append(f"- {lvl}: " + "; ".join(items))
    return "\n".join(lines).strip()


@app.route("/agent", methods=["GET", "POST"])
def agent():
    u = current_user()

    message = ""
    agent_text = None
    image_data_uri = None
    gen_image = False
    chat = []

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        gen_image = request.form.get("gen_image") == "1"
        agent_text = agent_respond(message)
        chat = [
            {"role": "You", "content": message},
            {"role": "Agent", "content": agent_text},
        ]
        if gen_image:
            image_data_uri = generate_svg_cover_data_uri(message)

    return render_template(
        "agent.html",
        user=u,
        message=message,
        agent_text=agent_text,
        image_data_uri=image_data_uri,
        gen_image=gen_image,
        chat=chat,
    )


def ensure_static_structure():
    # Create folders if missing (images handled via templates/static references)
    for folder in ["templates", "static", "images"]:
        p = os.path.join(BASE_DIR, folder)
        os.makedirs(p, exist_ok=True)


if __name__ == "__main__":
    ensure_static_structure()
    init_db()
    app.run(debug=True)

