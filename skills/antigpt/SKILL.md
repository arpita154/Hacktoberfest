---
name: antigpt
description: Rules for AI coding agents working on AntiGPT, a Gemma 4 powered programming-feedback app.
---

# Working on AntiGPT

## Architecture
- `grader.py` — deterministic grader. Runs student code in a subprocess with a timeout. **Only source of scores.**
- `feedback.py` — calls Gemma 4 (`gemma-4-26b-a4b-it`, Gemini API) to explain real test results; falls back to rule-based text.
- `app.py` — Streamlit UI (Student + Instructor tabs). Submissions saved to `submissions.json`.

## Rules
1. Never let the model change, invent or decide test results or scores.
2. Never run student code inside the app process — always via `grader.grade()`.
3. Hint/explain levels must not return a full solution.
4. A Gemma failure must fall back gracefully; never crash the grading flow.
5. Never commit `.env` or API keys.

## Adding an assignment
Add an entry to `ASSIGNMENTS` in `grader.py`: `func`, `desc`, `starter`, and `tests` as `(args_list, expected)` pairs.

## Run
`pip install -r requirements.txt` then `streamlit run app.py`.
