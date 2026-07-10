# LLM Judge Chatbot Testing |[Türkçe](README_TR.md)|

![CI](https://github.com/TuranAymis/llm-judge-chatbot-testing/actions/workflows/ci.yml/badge.svg)

A Python-based QA automation project for testing chatbot responses with structured mock test data and LLM-based evaluation.

This repository demonstrates how chatbot answers can be tested in a repeatable way using Playwright, Pytest, JSON test data, Allure reporting, and an optional LLM judge.

## Project Purpose

The purpose of this project is to validate chatbot behavior through automated end-to-end tests.

The test flow is designed to:

* Open a chatbot widget in the browser
* Send predefined test questions
* Capture chatbot responses
* Compare actual responses against expected criteria
* Use an LLM judge to evaluate answer quality
* Generate test results and optional Allure reports

This project is intended as a public QA automation portfolio project.

## Tech Stack

* Python
* Pytest
* Playwright
* pytest-playwright
* Allure Pytest
* JSON test data
* python-dotenv
* OpenAI / Gemini integration for LLM-based evaluation

## Repository Structure

```text
.
├── chatbotKontrolAI/
├── data/
│   └── test-data.json
├── scripts/
│   └── converter.py
├── specs/
│   └── system_audit_v2.md
├── tests/
│   └── test_chatbot.py
├── utils/
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Test Data

The project uses safe mock test data stored in:

```text
data/test-data.json
```

Current mock data format:

```json
[
  {
    "soru": "What are the main benefits of automated testing in a software project?",
    "cevap": "Automated testing provides faster feedback, repeatable test execution, better regression coverage, and helps teams detect issues earlier."
  },
  {
    "soru": "What is the difference between smoke testing and regression testing?",
    "cevap": "Smoke testing checks whether the most critical functions work after a build, while regression testing checks that existing features still work after changes."
  }
]
```

Private, customer-related, company-related, or real production test data should not be committed to this repository.

## Environment Variables

Create a local `.env` file based on `.env.example`.

Example values:

```env
OPENAI_API_KEY=
GEMINI_API_KEY=
LLM_TYPE=openai

CHATBOT_BASE_URL=
CHATBOT_WIDGET_TIMEOUT_MS=60000

CHATBOT_TEST_NAME=Test Automation
CHATBOT_TEST_EMAIL=test@example.com
```

Do not commit `.env` files.

## Setup

Clone the repository:

```bash
git clone https://github.com/TuranAymis/llm-judge-chatbot-testing.git
cd llm-judge-chatbot-testing
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browsers:

```bash
playwright install
```

## Running Tests

Run all tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run the chatbot E2E test with Allure results:

```bash
pytest tests/test_chatbot.py --alluredir=reports/allure-results --clean-alluredir
```

Serve the Allure report locally:

```bash
allure serve reports/allure-results
```

Generate a static Allure report:

```bash
allure generate reports/allure-results --clean
```

## QA Focus

This project demonstrates several QA automation practices:

* Chatbot response validation
* End-to-end testing with Playwright
* Data-driven testing with JSON
* LLM-assisted answer evaluation
* Mock test data usage
* Test reporting with Allure
* Environment-based configuration
* Public repository hygiene

## Repository Hygiene

The following files and folders should not be committed:

```text
.venv/
venv/
.env
allure-report/
allure-results/
reports/
*.docx
*.xlsx
*.csv
__pycache__/
.pytest_cache/
```

Only safe mock data should be kept in the repository.

## Current Status

This repository has been cleaned and renamed for portfolio use.

Completed improvements:

* Removed virtual environment files from the repository
* Removed generated report artifacts
* Removed real test data
* Replaced real data with safe mock questions
* Renamed the repository to `llm-judge-chatbot-testing`
* Added a professional README structure

Planned improvements:

* Clean and normalize `.gitignore`
* Add clearer test result examples
* Add a sample Allure report screenshot
* Add GitHub repository description and topics
* Improve test documentation under the `specs/` folder
