# AntiGPT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AntiGPT is an AI-powered feedback system for programming assignments. It evaluates student Python code against real test cases and gives helpful explanations without revealing the full solution. The goal is to make grading objective while keeping feedback educational and constructive.

## Project Overview

This project was built for the Build for Your Campus track and focuses on the gap between strict auto-grading and generic AI answers. Instead of only saying “pass” or “fail,” AntiGPT explains what went wrong and nudges students toward the right idea.

## Features

- Runs student code in a separate Python subprocess
- Enforces a timeout to prevent infinite loops
- Compares outputs against expected test cases
- Shows pass/fail results for each test
- Uses Gemini-powered feedback to explain mistakes
- Provides three feedback modes: hint, explain, and detailed guidance
- Includes an instructor dashboard with class statistics and common errors
- Stores submissions locally in a JSON file for demo use

## Tech Stack

- Python
- Streamlit
- Gemini API / Google AI Studio
- Requests
- Python-dotenv
- Pandas

## How It Works

1. The grader runs a student solution in an isolated Python process.
2. The result is compared to the expected output for real test cases.
3. The test outcome is sent to the AI model along with the assignment prompt and code.
4. The model generates feedback that explains the error without giving the final answer.
5. Instructors can view aggregated class performance and common mistakes.

## Live Demo

To run the application locally:

```bash
pip install -r requirements.txt
# Add your Gemini API key in a .env file
# GEMINI_API_KEY=your_key_here
streamlit run app.py
```

If you deploy this project to Streamlit Cloud or another host, add your live URL here.

## Example Workflow

1. A student submits a Python solution.
2. AntiGPT runs the code against hidden and visible test cases.
3. The app shows which tests passed or failed.
4. The student receives a hint or conceptual explanation.
5. The instructor can track class performance and recurring mistakes.

## Repository Details

- Name: AntiGPT
- Repository: https://github.com/arpita154/Hacktoberfest.git
- Description: AI-powered programming feedback system for student submissions
- License: MIT

## Limitations

- This is designed for Python assignments and is not a full sandboxed security environment.
- Local JSON storage is used for demo purposes.
- For production deployment, a more isolated runtime environment is recommended.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
