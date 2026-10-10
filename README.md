# AntiGPT

**Feedback that teaches, not answers that cheat.** Built for the *Build for Your Campus* track (OpenLake × MLH Hack Day, IIT Bhilai — Build with Gemma 4).

Students submit Python code. AntiGPT runs it against **real test cases** and shows which pass or fail. **Gemma 4** then explains *why* a test failed — as a hint, a concept explanation, or detailed feedback — without handing over the solution. Instructors see class-wide scores and the most common mistakes.

## Why
Normal autograders say only "pass/fail". ChatGPT-style tools just give the answer. AntiGPT sits in between: the grade is objective, the feedback makes the student think.

## How it works
1. `grader.py` runs student code in a **separate Python process** with a 5-second timeout (infinite loops can't freeze the app) and compares the output with expected values. **This is the only thing that decides the score.**
2. `feedback.py` sends the assignment, the code and the **real test results** to **Gemma 4** (`gemma-4-26b-a4b-it` via the Gemini API). The prompt forbids changing or inventing results.
3. If Gemma is unavailable or no key is set, rule-based feedback is shown instead — the score is never affected.
4. `app.py` (Streamlit) has a Student tab and an Instructor tab (submissions, average score, most common errors).

## Gemma 4 integration
- Model: `gemma-4-26b-a4b-it`, hosted by Google AI Studio / Gemini API.
- Called with a plain HTTPS request (`requests`) — key read from `.env`, never committed.
- Help levels: `hint` (one guiding question, no code), `explain` (concept, no solution), `detailed` (small fix allowed).

## Run it
```
pip install -r requirements.txt
# put your key in .env:  GEMINI_API_KEY=...
streamlit run app.py
```

## Demo
1. Student → "Average of a List" → Run tests → 3/4 (empty list → ZeroDivisionError).
2. Help level *hint* → "Explain my mistake (Gemma 4)".
3. Fix: `return sum(nums) / len(nums) if nums else 0` → 4/4.
4. Instructor tab → class stats and common mistakes.

## Limitations
- The subprocess + timeout is not a full security sandbox; for real deployment run the grader inside Docker with no network.
- Submissions are stored in a local JSON file; no login yet.
- Python assignments only.

## License
MIT
