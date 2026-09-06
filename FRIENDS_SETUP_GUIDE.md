# 🚀 TalentRank Studio — Quick Friend Setup & Run Guide

Welcome to **TalentRank Studio**! This guide helps you set up and run the application on any PC (Windows, macOS, or Linux) in under 3 minutes.

---

## 📋 Prerequisites

Before starting, ensure you have:
1. **Python 3.10+** installed on your system:
   - Check by running: `python --version` (or `python3 --version`)
2. **Git** installed:
   - Check by running: `git --version`

---

## ⚡ 3-Step Quick Start

### 1. Clone the Repository

Open your Terminal (macOS/Linux) or PowerShell/Command Prompt (Windows) and run:

```bash
git clone https://github.com/Anshik-02/ai_screening.git
cd ai_screening
```

---

### 2. Set Up Virtual Environment & Install Dependencies

#### 💻 Windows (PowerShell / Command Prompt):
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# In PowerShell:
.\.venv\Scripts\Activate.ps1
# In Command Prompt (cmd):
# .\.venv\Scripts\activate.bat

# Upgrade pip & install requirements
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 🍎 macOS / 🐧 Linux (Terminal):
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip & install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 3. Launch the Application

Run the server with Uvicorn:

#### Windows:
```powershell
$env:PYTHONPATH = "src"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### macOS / Linux:
```bash
PYTHONPATH=src python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Now open your web browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🎯 Modes Available

1. **Recruiter Mode**:
   - Screen candidate resumes against job descriptions.
   - Test text mode or upload PDF/DOCX resume files.
   - View top-ranked candidates with Gold/Silver/Bronze badges and score breakdowns.

2. **Candidate Mode**:
   - Guided 5-Stage interview prep journey.
   - Click **✨ Try Live Demo** to run an offline deterministic scenario (Alex Rivera - Backend Python Engineer) with **zero API key required**.
   - Interactive Skill Constellation Map, Readiness Orbit Gauge, and Adaptive Mock Interview.

---

## 🗝️ AI Gemini / OpenAI Integration (Optional)

The project includes built-in **Deterministic Demo Mode** so it works 100% offline out of the box!

If you want live AI LLM reasoning:
1. Create a `.env` file in the root directory:
   ```env
   # Option A: Gemini API Key (Free)
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Option B: OpenAI API Key
   # OPENAI_API_KEY=your_openai_api_key_here
   ```
2. Restart the server. The badge in the top header will switch to **AI Engine Active**.

---

## ❓ Troubleshooting FAQ

- **Error: `Command 'uvicorn' not found`**
  - Make sure your virtual environment `.venv` is activated before running the uvicorn command.
- **Port 8000 in use**
  - Change the port in the launch command to `--port 8001`.
- **PowerShell Script Execution Error (Windows)**
  - If PowerShell blocks activating `.venv`, run PowerShell as Administrator once and execute:
    `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

Built with ❤️ by [Anshik-02](https://github.com/Anshik-02).
