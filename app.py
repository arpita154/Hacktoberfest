import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import ui
from feedback import STAGE_LABELS, STAGES, gemma_available, get_hint
from grader import ASSIGNMENTS, grade

load_dotenv()
st.set_page_config(page_title="AntiGPT", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")
st.markdown(ui.CSS, unsafe_allow_html=True)
GEMMA = gemma_available()

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "antigpt.db"
LEGACY_JSON = BASE_DIR / "submissions.json"
BUTTON_LABELS = {"hint1": "Get Hint 1", "hint2": "Get Hint 2", "full": "Reveal Full Explanation"}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT NOT NULL,
            assignment TEXT NOT NULL,
            passed INTEGER NOT NULL,
            total INTEGER NOT NULL,
            errors TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("admin", hash_password("admin123"), "admin"),
    )
    conn.commit()
    conn.close()

    if LEGACY_JSON.exists() and not _legacy_rows_loaded():
        migrate_legacy_data()


def _legacy_rows_loaded():
    conn = sqlite3.connect(DB)
    has_rows = conn.execute("SELECT COUNT(*) FROM submissions").fetchone()[0] > 0
    conn.close()
    return has_rows


def migrate_legacy_data():
    if not LEGACY_JSON.exists():
        return
    try:
        rows = json.loads(LEGACY_JSON.read_text(encoding="utf-8"))
        if not rows:
            return
        conn = sqlite3.connect(DB)
        for row in rows:
            conn.execute(
                "INSERT INTO submissions (student, assignment, passed, total, errors) VALUES (?, ?, ?, ?, ?)",
                (
                    row.get("student", "Unknown"),
                    row.get("assignment", "Unknown"),
                    int(row.get("passed", 0)),
                    int(row.get("total", 0)),
                    json.dumps(row.get("errors", [])),
                ),
            )
        conn.commit()
        conn.close()
    except Exception:
        pass


def load():
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT student, assignment, passed, total, errors FROM submissions ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {
            "student": student,
            "assignment": assignment,
            "passed": passed,
            "total": total,
            "errors": json.loads(errors) if errors else [],
        }
        for student, assignment, passed, total, errors in rows
    ]


def save(rows):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM submissions")
    for row in rows:
        conn.execute(
            "INSERT INTO submissions (student, assignment, passed, total, errors) VALUES (?, ?, ?, ?, ?)",
            (
                row.get("student", "Unknown"),
                row.get("assignment", "Unknown"),
                int(row.get("passed", 0)),
                int(row.get("total", 0)),
                json.dumps(row.get("errors", [])),
            ),
        )
    conn.commit()
    conn.close()


def login_user(username: str, password: str):
    if not username or not password:
        return None
    conn = sqlite3.connect(DB)
    user = conn.execute(
        "SELECT username, role FROM users WHERE username = ? AND password_hash = ?",
        (username.strip(), hash_password(password)),
    ).fetchone()
    conn.close()
    return {"username": user[0], "role": user[1]} if user else None


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


init_db()
st.session_state.setdefault("student_name", "Demo Student")
st.session_state.setdefault("hints", [])
st.session_state.setdefault("hint_error", None)
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user", None)


# ------------------------------------------------------------------ auth

def login_page():
    st.title("AntiGPT")
    st.subheader("Sign in")
    st.caption("Use your demo account to access the practice and instructor pages.")
    st.info("Demo login: username = admin, password = admin123")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        user = login_user(username, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid username or password.")


# ------------------------------------------------------------------ sidebar

def render_sidebar():
    with st.sidebar:
        html(ui.sidebar_html(GEMMA))
        st.write("")
        if st.session_state.get("authenticated"):
            st.caption(f"Signed in as: {st.session_state.user['username']}")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.rerun()
        st.write("")
        if st.session_state.get("authenticated"):
            page = st.radio(
                "Navigation",
                ["Practice", "Instructor"],
                label_visibility="collapsed",
                format_func={"Practice": "💻  Practice", "Instructor": "📊  Instructor"}.get,
            )
        html(ui.SIDEBAR_FOOTER)
        return page if st.session_state.get("authenticated") else None


# ------------------------------------------------------------------ practice
def hint_section(a, run):
    html('<div class="ag-h2">Learning assistance</div>')
    hints = st.session_state.hints
    html(ui.steps_html(STAGES, STAGE_LABELS, len(hints)))

    for h in hints:
        with st.container(border=True):
            html(ui.hint_header_html(STAGE_LABELS[h["stage"]], h["source"]))
            st.markdown(h["text"])

    if len(hints) >= len(STAGES):
        st.success("You've seen every hint. Now fix your code and click **Run tests** again.")
        return

    nxt = STAGES[len(hints)]
    label = BUTTON_LABELS[nxt]
    if st.session_state.hint_error:
        st.error(f"Could not get a response from Gemma 4: {st.session_state.hint_error}")
        label = f"Retry — {label}"
    if st.button(label, key=f"hint_btn_{nxt}", type="secondary"):
        source_name = "Gemma 4" if GEMMA else "rule-based hints"
        with st.spinner(f"Generating {STAGE_LABELS[nxt]} with {source_name}…"):
            res = get_hint(a, run["code"], run["results"], nxt, [(h["stage"], h["text"]) for h in hints])
        if res["ok"]:
            hints.append({"stage": nxt, "text": res["text"], "source": res["source"]})
            st.session_state.hint_error = None
        else:
            st.session_state.hint_error = res["error"]
        st.rerun()


def practice():
    st.markdown("## Practice")
    st.caption("Write a function, run the real tests, and use hints only when you're stuck.")
    html(ui.panels_html(GEMMA))

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.text_input("Your name", key="student_name")
        title = st.selectbox("Assignment", list(ASSIGNMENTS), key="assignment")
        a = ASSIGNMENTS[title]
        st.info(a["desc"])
        code = st.text_area("Your code", a["starter"], height=240, key=f"code_{title}")
        if st.button("▶  Run tests", type="primary"):
            with st.spinner("Running tests…"):
                results = grade(code, a)
            st.session_state.run = {"title": title, "code": code, "results": results}
            st.session_state.hints = []
            st.session_state.hint_error = None
            rows = load()
            rows.append({
                "student": st.session_state.student_name,
                "assignment": title,
                "passed": sum(r["passed"] for r in results),
                "total": len(results),
                "errors": [r["error"] or ("Wrong answer" if not r["passed"] else None) for r in results],
            })
            save(rows)

    run = st.session_state.get("run")
    run = run if run and run["title"] == title else None

    with right:
        html('<div class="ag-h2" style="margin-top:0">Test results</div>')
        html(ui.summary_html(run["results"] if run else None))
        if run:
            html(ui.cards_html(run["results"]))
            if run["code"] != code:
                st.warning("You edited the code after this run. Click **Run tests** to re-grade.")

    if run and not all(r["passed"] for r in run["results"]):
        hint_section(a, run)


# ------------------------------------------------------------------ instructor
def instructor():
    st.markdown("## Instructor")
    st.caption("Instructor dashboard for class-wide performance.")
    rows = load()
    if not rows:
        st.info("No submissions yet. Run some tests on the Practice page first.")
        return
    df = pd.DataFrame(rows)
    c1, c2, c3 = st.columns(3)
    c1.metric("Submissions", len(df))
    c2.metric("Students", df.student.nunique())
    c3.metric("Full-marks runs", int((df.passed == df.total).sum()))
    st.subheader("Average score % by assignment")
    st.bar_chart((df.passed / df.total * 100).groupby(df.assignment).mean())
    st.subheader("Most common mistakes in the class")
    errs = [e.split(":")[0] for r in rows for e in r["errors"] if e]
    if errs:
        st.bar_chart(pd.Series(errs).value_counts())
    else:
        st.write("No mistakes recorded yet.")
    st.subheader("All submissions")
    st.dataframe(df[["student", "assignment", "passed", "total"]], width="stretch")


if not st.session_state.get("authenticated"):
    login_page()
else:
    page = render_sidebar()
    if page == "Practice":
        practice()
    elif page == "Instructor":
        instructor()
