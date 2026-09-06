"""
Candidate Mode API routes.

All endpoints are under /v1/candidate/.

⚠️  The mock interview uses an in-memory session store inside candidate_coach.py.
    Sessions are lost when the backend process restarts.
    This is intentional — no user data is persisted.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import (
    CandidateAnalyzeRequest,
    CandidateProfileAnalysis,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    InterviewSummaryResponse,
    MockInterviewAnswerRequest,
    MockInterviewAnswerResponse,
    MockInterviewStartRequest,
    MockInterviewStartResponse,
)
from app.services import candidate_coach
from app.services.resume_parser import ResumeParsingError, parse_resume_bytes

router = APIRouter(prefix="/v1/candidate", tags=["candidate"])


# ---------------------------------------------------------------------------
# Profile analysis  (text body)
# ---------------------------------------------------------------------------


@router.post("/analyze", response_model=CandidateProfileAnalysis)
def analyze_candidate(request: CandidateAnalyzeRequest) -> CandidateProfileAnalysis:
    """
    Analyse a candidate's resume text against a job description.

    Returns a deterministic skill gap plus optional LLM narrative and
    resume improvement suggestions.  Never fails due to LLM issues —
    llm_available=False and llm_error explain any degraded state.
    """
    return candidate_coach.analyze_profile(
        resume_text=request.resume_text,
        job_title=request.job_title,
        job_description=request.job_description,
    )


@router.post("/analyze-file", response_model=CandidateProfileAnalysis)
async def analyze_candidate_file(
    job_title: str = Form(...),
    job_description: str = Form(...),
    resume: UploadFile = File(...),
) -> CandidateProfileAnalysis:
    """
    Upload a resume file (PDF, DOCX, TXT) and analyse against a job description.
    """
    try:
        content = await resume.read()
        resume_text = parse_resume_bytes(resume.filename or "resume.txt", content)
    except ResumeParsingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return candidate_coach.analyze_profile(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
    )


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------


@router.post("/questions", response_model=GenerateQuestionsResponse)
def generate_questions(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
    """
    Generate a list of interview questions tailored to the candidate's profile.
    Falls back to template questions when LLM is unavailable.
    """
    return candidate_coach.generate_interview_questions(
        resume_text=request.resume_text,
        job_title=request.job_title,
        job_description=request.job_description,
        max_questions=request.max_questions,
    )


# ---------------------------------------------------------------------------
# Mock interview (ephemeral in-memory sessions)
# ---------------------------------------------------------------------------


@router.post("/interview/start", response_model=MockInterviewStartResponse)
def start_interview(request: MockInterviewStartRequest) -> MockInterviewStartResponse:
    """
    Create a new mock interview session and return the first question.
    Store the returned session_id in the client for subsequent calls.

    ⚠️  Sessions are in-memory and lost on server restart.
    """
    _, response = candidate_coach.create_interview_session(
        resume_text=request.resume_text,
        job_title=request.job_title,
        job_description=request.job_description,
        max_questions=request.max_questions,
    )
    return response


@router.post("/interview/answer", response_model=MockInterviewAnswerResponse)
def answer_interview(request: MockInterviewAnswerRequest) -> MockInterviewAnswerResponse:
    """
    Submit an answer to the current question.
    Returns per-answer feedback scores plus the next question (or marks complete).
    Scores are AI-estimated and labelled as such in llm_available.
    """
    try:
        return candidate_coach.process_interview_answer(
            session_id=request.session_id,
            answer=request.answer,
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found or expired. Start a new session.",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/interview/{session_id}/summary", response_model=InterviewSummaryResponse)
def interview_summary(session_id: str) -> InterviewSummaryResponse:
    """
    Retrieve the final readiness report for a completed (or in-progress) session.

    The readiness score is computed deterministically.
    The narrative and roadmap are LLM-generated (graceful fallback if unavailable).
    """
    try:
        return candidate_coach.get_interview_summary(session_id=session_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found or expired. Start a new session.",
        )
