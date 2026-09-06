# TalentRank Studio — Setup Guide

Follow these steps to run TalentRank Studio on any Windows, macOS, or Linux machine.

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.11 or newer |
| pip | Latest |
| Git | Any recent version |
| Browser | Chrome, Firefox, or Edge |

**Optional:** An OpenAI API key enables AI-powered Candidate Mode (mock interviews, coaching). Recruiter Mode works fully without it.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/prashantsingh5/TalentRank-Studio-AI-Resume-Screening.git
cd TalentRank-Studio-AI-Resume-Screening
```

---

## Step 2 — Create a Virtual Environment

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Step 3 — Configure Environment (Optional)

Copy the example env file and edit if you want AI features:

```bash
cp .env.example .env
```

Edit `.env` and set your OpenAI key:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

> **Without an API key:** Candidate Mode still works with deterministic rule-based scoring. Only AI mock interviews and LLM coaching require a key.

---

## Step 4 — Start the Server

### Windows (PowerShell)

```powershell
$env:PYTHONPATH = "src"
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### macOS / Linux

```bash
PYTHONPATH=src uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8001
```

---

## Step 5 — Open the Dashboard

Open your browser and go to:

| URL | Purpose |
|---|---|
| http://127.0.0.1:8001/ | Main dashboard (Recruiter + Candidate modes) |
| http://127.0.0.1:8001/docs | Interactive API documentation |
| http://127.0.0.1:8001/health | Health check endpoint |

---

## Using the App

### Recruiter Mode (default)

1. Fill in job title, description, and required skills.
2. Add candidates by pasting resume text **or** upload PDF/DOCX/TXT files.
3. Click **Run AI Screening** to get a ranked leaderboard.
4. Compare two candidates side-by-side in the comparison panel.

### Candidate Mode

1. Click **Candidate** in the top navigation.
2. Paste your resume or upload a file.
3. Enter your target job title and description (or use a preset).
4. Follow the 5-stage guided journey: Skill Gap → Improvements → Mock Interview → Readiness Report.

---

## Run Tests

```bash
PYTHONPATH=src pytest -q
```

---

## Troubleshooting

### "Failed to fetch" in the browser

- Make sure the server is running (`uvicorn` command above).
- Open the dashboard at **http://127.0.0.1:8001/** (same origin as the API).
- Do not open `index.html` directly from the file system.

### Port 8001 already in use

Use a different port:

```bash
PYTHONPATH=src uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Then open http://127.0.0.1:8080/

### Python not found

Install Python 3.11+ from [python.org](https://www.python.org/downloads/) and ensure "Add to PATH" is checked on Windows.

### PowerShell script execution blocked (Windows)

Run once as Administrator:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Share with a Friend on the Same Network (Optional)

To let a friend on your local Wi-Fi access the app:

```bash
PYTHONPATH=src uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Your friend opens `http://YOUR_LOCAL_IP:8001/` (find your IP with `ipconfig` on Windows or `ifconfig` on Mac/Linux).

> Only do this on trusted networks. This is a development server, not production-hardened.

---

## Quick Reference

```bash
# Full setup (macOS/Linux) — copy-paste all at once
git clone https://github.com/prashantsingh5/TalentRank-Studio-AI-Resume-Screening.git
cd TalentRank-Studio-AI-Resume-Screening
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Then open **http://127.0.0.1:8001/** in your browser.
