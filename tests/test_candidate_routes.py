"""
Integration tests for candidate API routes using FastAPI TestClient.

All LLM calls are patched — no real network requests.
"""
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import (
    CandidateProfileAnalysis,
    GenerateQuestionsResponse,
    InterviewSummaryResponse,
    MockInterviewAnswerResponse,
    MockInterviewStartResponse,
)
from app.services import candidate_coach

client = TestClient(app)

RESUME_TEXT = (
    "Name: Alex Tester\n"
    "Years of Experience: 3\n"
    "Skills: Python FastAPI Docker AWS PostgreSQL CI/CD backend engineering"
)
JOB_TITLE = "Senior Backend Engineer"
JOB_DESC = (
    "We are looking for a Python backend engineer with FastAPI, Docker, AWS, "
    "Kubernetes and PostgreSQL experience in a production environment."
)


# ---------------------------------------------------------------------------
# POST /v1/candidate/analyze
# ---------------------------------------------------------------------------


def test_analyze_endpoint_returns_skill_gap():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        resp = client.post(
            "/v1/candidate/analyze",
            json={"resume_text": RESUME_TEXT, "job_title": JOB_TITLE, "job_description": JOB_DESC},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "skill_gap" in body
    assert "resume_improvement" in body
    assert body["llm_available"] is False


def test_analyze_endpoint_validates_short_resume():
    resp = client.post(
        "/v1/candidate/analyze",
        json={"resume_text": "short", "job_title": JOB_TITLE, "job_description": JOB_DESC},
    )
    assert resp.status_code == 422


def test_analyze_file_endpoint():
    payload = b"Name: Alex\nYears of Experience: 3\nPython FastAPI Docker AWS PostgreSQL"
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        resp = client.post(
            "/v1/candidate/analyze-file",
            data={"job_title": JOB_TITLE, "job_description": JOB_DESC},
            files={"resume": ("alex_resume.txt", BytesIO(payload), "text/plain")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "skill_gap" in body


# ---------------------------------------------------------------------------
# POST /v1/candidate/questions
# ---------------------------------------------------------------------------


def test_generate_questions_endpoint_returns_list():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        resp = client.post(
            "/v1/candidate/questions",
            json={
                "resume_text": RESUME_TEXT,
                "job_title": JOB_TITLE,
                "job_description": JOB_DESC,
                "max_questions": 5,
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "questions" in body
    assert isinstance(body["questions"], list)
    assert 1 <= len(body["questions"]) <= 5


def test_generate_questions_max_questions_respected():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        resp = client.post(
            "/v1/candidate/questions",
            json={
                "resume_text": RESUME_TEXT,
                "job_title": JOB_TITLE,
                "job_description": JOB_DESC,
                "max_questions": 3,
            },
        )
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) <= 3


# ---------------------------------------------------------------------------
# Mock Interview: full lifecycle
# ---------------------------------------------------------------------------


def test_interview_start_endpoint():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        resp = client.post(
            "/v1/candidate/interview/start",
            json={
                "resume_text": RESUME_TEXT,
                "job_title": JOB_TITLE,
                "job_description": JOB_DESC,
                "max_questions": 3,
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert "first_question" in body
    assert body["first_question"]["question_type"] in ("planned", "adaptive_follow_up")


def test_interview_answer_endpoint():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        # Start session
        start = client.post(
            "/v1/candidate/interview/start",
            json={
                "resume_text": RESUME_TEXT,
                "job_title": JOB_TITLE,
                "job_description": JOB_DESC,
                "max_questions": 3,
            },
        ).json()
        session_id = start["session_id"]

        # Answer question
        ans = client.post(
            "/v1/candidate/interview/answer",
            json={"session_id": session_id, "answer": "I have 3 years of Python and FastAPI experience."},
        )
    assert ans.status_code == 200
    body = ans.json()
    assert "feedback" in body
    assert "scores" in body["feedback"]
    assert 0 <= body["feedback"]["scores"]["overall_answer_score"] <= 100
    assert body["question_number"] == 1


def test_interview_answer_invalid_session():
    resp = client.post(
        "/v1/candidate/interview/answer",
        json={"session_id": "bad-session-id", "answer": "test answer"},
    )
    assert resp.status_code == 404


def test_interview_summary_endpoint():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        # Start and answer one question
        start = client.post(
            "/v1/candidate/interview/start",
            json={
                "resume_text": RESUME_TEXT,
                "job_title": JOB_TITLE,
                "job_description": JOB_DESC,
                "max_questions": 3,
            },
        ).json()
        session_id = start["session_id"]

        client.post(
            "/v1/candidate/interview/answer",
            json={"session_id": session_id, "answer": "Python, FastAPI, Docker are my core strengths."},
        )

        # Get summary
        summary = client.get(f"/v1/candidate/interview/{session_id}/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert 0.0 <= body["readiness_score"] <= 100.0
    assert body["readiness_band"] in ("not_ready", "needs_work", "almost_ready", "ready", "strong")
    assert body["questions_answered"] >= 1
    assert isinstance(body["preparation_roadmap"], list)
    assert len(body["preparation_roadmap"]) >= 1


def test_interview_summary_invalid_session():
    resp = client.get("/v1/candidate/interview/nonexistent-id/summary")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Health check still works (regression guard)
# ---------------------------------------------------------------------------


def test_health_check_unchanged():
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
