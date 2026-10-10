import json
import os

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

DB = "submissions.json"
BUTTON_LABELS = {"hint1": "Get Hint 1", "hint2": "Get Hint 2", "full": "Reveal Full Explanation"}


def load():
    return json.load(open(DB)) if os.path.exists(DB) else []


def save(rows):
    json.dump(rows, open(DB, "w"), indent=2)


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


st.session_state.setdefault("student_name", "Demo Student")
st.session_state.setdefault("hints", [])
st.session_state.setdefault("hint_error", None)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    html(ui.sidebar_html(GEMMA))
    st.write("")
    page = st.radio("Navigation", ["Practice", "Instructor"], label_visibility="collapsed",
                    format_func={"Practice": "💻  Practice", "Instructor": "📊  Instructor"}.get)
    html(ui.SIDEBAR_FOOTER)


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
            rows.append({"student": st.session_state.student_name, "assignment": title,
                         "passed": sum(r["passed"] for r in results), "total": len(results),
                         "errors": [r["error"] or ("Wrong answer" if not r["passed"] else None) for r in results]})
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
    st.caption("Demo view — this app has no login yet, so anyone using it can see this page.")
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


if page == "Practice":
    practice()
else:
    instructor()
