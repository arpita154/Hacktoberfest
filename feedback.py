"""Learning assistance. Explains results the grader already produced — never changes them.

Three progressive stages: hint1 -> hint2 -> full.
Gemma 4 is used when GEMINI_API_KEY is set; otherwise clearly-labelled rule-based hints.
"""
import os

import requests

MODEL = "gemma-4-26b-a4b-it"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

STAGES = ["hint1", "hint2", "full"]
STAGE_LABELS = {"hint1": "Hint 1", "hint2": "Hint 2", "full": "Full explanation"}
STAGE_RULES = {
    "hint1": "Give ONE short nudge (max 2 sentences), ideally a question, pointing at WHICH failing case to look at. "
             "No code. Do not say how to fix it.",
    "hint2": "Give a more specific direction (max 3 sentences): which part of THEIR code is responsible and what to "
             "check there. Still no corrected code.",
    "full": "Write a full explanation with these markdown headings: **What is wrong**, **Why it fails**, "
            "**Concept**, **How to reason toward a fix** (numbered steps), **Small example** (an unrelated "
            "3-5 line example of the concept). Do NOT write the complete corrected solution for this assignment.",
}


def _key():
    key = (os.getenv("GEMINI_API_KEY") or "").strip()
    return None if not key or key.startswith("paste") or key == "bad-placeholder" else key


def gemma_available() -> bool:
    return _key() is not None


def _facts(results):
    return "\n".join(
        f"- input {r['input']}: expected {r['expected']}, got {r['got']}, "
        f"error {r['error']} -> {'PASS' if r['passed'] else 'FAIL'}" for r in results)


def build_prompt(assignment, code, results, stage, previous):
    earlier = "\n".join(f"- {STAGE_LABELS[s]}: {t}" for s, t in previous) or "- none yet"
    return f"""You are AntiGPT, a programming tutor for college students. Learn to think, don't just copy.
The test results below come from REAL execution. Never change them, never invent new ones,
and never claim a test passed or failed differently.

Assignment: {assignment['desc']}
Student code:
{code}

Test results:
{_facts(results)}

Hints already shown to the student (do not repeat them, go one step further):
{earlier}

Your task — {STAGE_LABELS[stage]}: {STAGE_RULES[stage]}"""


def rule_based(results, stage):
    bad = [r for r in results if not r["passed"]]
    if not bad:
        return "All tests passed — nothing to fix!"
    r = bad[0]
    err = (r["error"] or "").split(":")[0]
    if stage == "hint1":
        return f"Look closely at the failing test with input `{r['input']}`. What should happen for that input?"
    if stage == "hint2":
        specific = {
            "ZeroDivisionError": "You divide by something that can be 0 for this input. Check that case before dividing.",
            "IndentationError": "Python needs the function body indented by 4 spaces under the `def` line.",
            "SyntaxError": "Python could not read your code — look for a missing `:` or bracket.",
            "TypeError": "Check the types of the values you combine on this input.",
            "IndexError": "An index goes past the end of the list — check your loop bounds.",
            "Timeout": "Your loop may never stop — make sure the loop condition eventually becomes false.",
        }.get(err, f"Your code returned `{r['got']}` but `{r['expected']}` was expected. "
                   "Trace each line by hand with this input.")
        return specific
    return (f"**What is wrong:** for input `{r['input']}` the expected result is `{r['expected']}`, "
            f"but your code {'raised ' + r['error'] if r['error'] else 'returned ' + repr(r['got'])}.\n\n"
            "**Why it fails:** this input is an edge case your current logic does not handle.\n\n"
            "**How to reason toward a fix:**\n1. Write the failing input on paper.\n"
            "2. Run your code line by line in your head.\n3. Find the first line where the value differs from "
            "what you expect.\n4. Add a check for this case before that line.")


def get_hint(assignment, code, results, stage, previous):
    """Returns dict(text, source, ok, error). ok=False means the Gemma call failed (UI offers retry)."""
    if not gemma_available():
        return {"text": rule_based(results, stage), "source": "Rule-based (no GEMINI_API_KEY set)",
                "ok": True, "error": None}
    try:
        resp = requests.post(URL, headers={"x-goog-api-key": _key()},
                             json={"contents": [{"parts": [{"text": build_prompt(assignment, code, results,
                                                                                    stage, previous)}]}],
                                   "generationConfig": {"temperature": 0.3}},
                             timeout=60)
        resp.raise_for_status()
        parts = resp.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
        if not text:
            raise ValueError("empty response from model")
        return {"text": text, "source": f"Gemma 4 ({MODEL})", "ok": True, "error": None}
    except Exception as e:  # never break grading because of the model
        return {"text": None, "source": None, "ok": False, "error": str(e)[:200]}


# Backwards-compatible helper used by earlier versions of app.py
def ask_gemma(assignment, code, results, level):
    stage = {"hint": "hint1", "explain": "hint2", "detailed": "full"}.get(level, "hint1")
    r = get_hint(assignment, code, results, stage, [])
    return (r["text"], r["source"]) if r["ok"] else (rule_based(results, stage), "rule-based")
