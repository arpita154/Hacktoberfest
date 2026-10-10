"""Pure HTML/CSS helpers for the Streamlit UI (no Streamlit import, so they are unit-testable)."""
import html
import json

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root { --bg:#0B1020; --side:#0F172A; --card:#111C31; --elev:#17243A; --green:#34D399; --blue:#60A5FA;
        --text:#F1F5F9; --muted:#94A3B8; --ok:#22C55E; --err:#F87171; --warn:#FBBF24; --line:#263449; }
html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox, button { font-family: 'Inter', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
section[data-testid="stSidebar"] { background: var(--side); border-right: 1px solid var(--line); }
.block-container { padding-top: 2rem; max-width: 1200px; }
textarea { font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important; }

.ag-brand { display:flex; gap:12px; align-items:center; margin-bottom:6px; }
.ag-logo { width:40px; height:40px; border-radius:10px; display:grid; place-items:center; font-weight:700;
           font-family:'JetBrains Mono',monospace; color:#0B1020;
           background: linear-gradient(135deg, var(--green), var(--blue)); }
.ag-name { font-size:20px; font-weight:700; color:var(--text); line-height:1.1; }
.ag-tag { font-size:12px; color:var(--muted); }
.ag-badge { display:inline-flex; align-items:center; gap:6px; margin:10px 0 4px; padding:4px 10px; border-radius:999px;
            font-size:12px; font-weight:600; color:var(--blue); background:rgba(96,165,250,.12); border:1px solid rgba(96,165,250,.35); }
.ag-dot { width:7px; height:7px; border-radius:50%; }
.ag-foot { font-size:12px; color:var(--muted); border-top:1px solid var(--line); padding-top:12px; margin-top:16px; line-height:1.8; }

.ag-panels { display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin: 8px 0 18px; }
@media (max-width: 760px) { .ag-panels, .ag-grid { grid-template-columns: 1fr !important; } }
.ag-panel { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; border-left-width:4px; }
.ag-panel h4 { margin:0 0 6px; font-size:15px; display:flex; gap:8px; align-items:center; color:var(--text); }
.ag-panel p { margin:0; color:var(--muted); font-size:13.5px; line-height:1.5; }
.ag-panel .meta { margin-top:10px; font-size:12px; font-weight:600; }
.ag-panel.grade { border-left-color: var(--ok); } .ag-panel.grade .meta { color: var(--ok); }
.ag-panel.ai { border-left-color: var(--blue); } .ag-panel.ai .meta { color: var(--blue); }

.ag-summary { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin:6px 0 14px; }
.ag-summary .top { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:8px; }
.ag-summary .big { font-size:22px; font-weight:700; }
.ag-summary .stats { display:flex; gap:16px; font-size:13px; color:var(--muted); }
.ag-bar { height:8px; background:var(--elev); border-radius:99px; overflow:hidden; margin-top:12px; }
.ag-bar > div { height:100%; border-radius:99px; transition: width .4s; }
.ag-muted { color:var(--muted); }

.ag-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:12px; }
.ag-card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; }
.ag-card.pass { border-color: rgba(34,197,94,.45); } .ag-card.fail { border-color: rgba(248,113,113,.5); }
.ag-card .head { display:flex; align-items:center; gap:8px; font-weight:600; font-size:14px; }
.ag-status { font-size:11px; font-weight:700; letter-spacing:.06em; padding:2px 8px; border-radius:6px; margin-left:auto; }
.pass .ag-status { color:var(--ok); background:rgba(34,197,94,.12); }
.fail .ag-status { color:var(--err); background:rgba(248,113,113,.12); }
.ag-kv { margin-top:10px; font-family:'JetBrains Mono',monospace; font-size:12.5px; display:grid; grid-template-columns:72px 1fr; gap:4px 8px; }
.ag-kv span:nth-child(odd) { color:var(--muted); font-family:'Inter',sans-serif; }
.ag-kv code { background:none; color:var(--text); padding:0; word-break:break-all; }
.ag-card details { margin-top:10px; font-size:12.5px; }
.ag-card summary { cursor:pointer; color:var(--err); }
.ag-card pre { white-space:pre-wrap; background:var(--elev); padding:8px; border-radius:8px; margin:6px 0 0; color:var(--text); }

.ag-steps { display:flex; gap:6px; margin:4px 0 12px; flex-wrap:wrap; }
.ag-step { font-size:12px; font-weight:600; padding:4px 10px; border-radius:999px; border:1px solid var(--line); color:var(--muted); }
.ag-step.done { color:#0B1020; background:var(--green); border-color:var(--green); }
.ag-step.next { color:var(--blue); border-color:var(--blue); }
.ag-hint-lbl { font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--blue); }
.ag-hint-src { font-size:11px; color:var(--muted); }
.ag-h2 { font-size:13px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:18px 0 8px; }
</style>
"""

CHECK = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2.4" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/>'
         '<path d="m8 12 3 3 5-6"/></svg>')
CROSS = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F87171" stroke-width="2.4" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/>'
         '<path d="m15 9-6 6M9 9l6 6"/></svg>')


def esc(v) -> str:
    return html.escape(v if isinstance(v, str) else json.dumps(v, default=repr))


def sidebar_html(gemma_on: bool) -> str:
    dot = "#22C55E" if gemma_on else "#FBBF24"
    status = "Powered by Gemma 4" if gemma_on else "Gemma 4 · add API key to enable"
    return f"""<div class="ag-brand"><div class="ag-logo">A/</div>
<div><div class="ag-name">AntiGPT</div><div class="ag-tag">Learn to think. Don't just copy.</div></div></div>
<div class="ag-badge"><span class="ag-dot" style="background:{dot}"></span>{status}</div>"""


SIDEBAR_FOOTER = """<div class="ag-foot">AI-assisted learning<br>Tests determine your score</div>"""


def panels_html(gemma_on: bool) -> str:
    ai_meta = "Purpose: Learning assistance" + ("" if gemma_on else " · currently rule-based (no API key)")
    return f"""<div class="ag-panels">
<div class="ag-panel grade"><h4>{CHECK} Graded by Real Tests</h4>
<p>Your score is determined by automated tests running against your code in a separate Python process
(5-second time limit). AI explanations cannot change your test results.</p>
<div class="meta">Source of truth: Automated test runner</div></div>
<div class="ag-panel ai"><h4><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2.2"
stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.9 4.6L18.5 9.5l-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9z"/>
<path d="M19 15l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></svg> Explained by Gemma 4</h4>
<p>AI helps you understand failed tests through progressive hints and step-by-step explanations.</p>
<div class="meta">{ai_meta}</div></div></div>"""


def summary_html(results) -> str:
    if results is None:
        return ('<div class="ag-summary"><div class="big ag-muted">Not evaluated yet</div>'
                '<div class="ag-muted" style="font-size:13px;margin-top:4px">Click <b>Run tests</b> to grade your code.</div></div>')
    total = len(results)
    passed = sum(r["passed"] for r in results)
    pct = round(passed / total * 100) if total else 0
    color = "#22C55E" if passed == total else ("#FBBF24" if passed else "#F87171")
    msg = "All tests passed. Great work!" if passed == total else "Some tests failed — use the hints below to find out why."
    return f"""<div class="ag-summary"><div class="top">
<div class="big" style="color:{color}">{passed} of {total} tests passed — {pct}%</div>
<div class="stats"><span>✓ Passed {passed}/{total}</span><span>✕ Failed {total - passed}/{total}</span></div></div>
<div class="ag-bar" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100"><div style="width:{pct}%;background:{color}"></div></div>
<div class="ag-muted" style="font-size:13px;margin-top:8px">{msg}</div></div>"""


def card_html(i: int, r: dict) -> str:
    ok = r["passed"]
    actual = "Error" if r["error"] else esc(r["got"])
    details = ""
    if r["error"]:
        details = f'<details><summary>Error details</summary><pre>{esc(r["error"])}</pre></details>'
    return f"""<div class="ag-card {'pass' if ok else 'fail'}"><div class="head">{CHECK if ok else CROSS}
Test {i} <span class="ag-status">{'PASS' if ok else 'FAIL'}</span></div>
<div class="ag-kv"><span>Input</span><code>{esc(r['input'])}</code><span>Expected</span><code>{esc(r['expected'])}</code>
<span>Actual</span><code>{actual}</code></div>{details}</div>"""


def cards_html(results) -> str:
    return '<div class="ag-grid">' + "".join(card_html(i + 1, r) for i, r in enumerate(results)) + "</div>"


def steps_html(stages, labels, revealed: int) -> str:
    out = []
    for i, s in enumerate(stages):
        cls = "done" if i < revealed else ("next" if i == revealed else "")
        out.append(f'<span class="ag-step {cls}">{"✓ " if i < revealed else ""}{labels[s]}</span>')
    return '<div class="ag-steps">' + "".join(out) + "</div>"


def hint_header_html(label: str, source: str) -> str:
    return (f'<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap">'
            f'<span class="ag-hint-lbl">{esc(label)}</span><span class="ag-hint-src">{esc(source)}</span></div>')
