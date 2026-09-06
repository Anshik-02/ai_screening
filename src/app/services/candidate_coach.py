"""
Candidate coaching service for TalentRank Studio.

This module owns ALL Candidate Mode business logic:

  1. Skill gap analysis          — deterministic (taxonomy) + optional LLM narrative
  2. Resume improvement advice   — deterministic fallbacks + optional LLM suggestions
  3. Interview question generation — template fallback + optional LLM questions
  4. Adaptive mock interview      — session state (in-memory, ephemeral)
  5. Per-answer evaluation        — keyword fallback + optional LLM scoring
  6. Readiness score             — deterministic weighted formula (LLM adds narrative only)

⚠️  In-memory session store (_interview_sessions) is lost when the backend restarts.
    This is intentional: no user data is persisted.

Readiness Score Formula (documented weights):
    skill_coverage    : 0.25
    resume_job_match  : 0.25
    interview_perf    : 0.35
    experience        : 0.15

Overall Answer Score Formula (per answer):
    technical_accuracy   : 0.35
    relevance            : 0.25
    completeness         : 0.20
    communication_clarity: 0.10
    answer_structure     : 0.10
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.schemas import (
    AnswerFeedback,
    AnswerScores,
    CandidateProfileAnalysis,
    GenerateQuestionsResponse,
    InterviewQuestion,
    InterviewSummaryResponse,
    MockInterviewAnswerResponse,
    MockInterviewStartResponse,
    PreparationRoadmapItem,
    ReadinessScoreBreakdown,
    ResumeSuggestion,
    ResumeImprovementResult,
    SkillGapResult,
)
from app.services import llm_client
from app.services.llm_client import LLMError, LLMUnavailableError
from app.services.skill_taxonomy import (
    extract_skills,
    get_semantic_skill_matches,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ANSWER_SCORE_WEIGHTS: dict[str, float] = {
    "technical_accuracy": 0.35,
    "relevance": 0.25,
    "completeness": 0.20,
    "communication_clarity": 0.10,
    "answer_structure": 0.10,
}

_READINESS_WEIGHTS: dict[str, float] = {
    "skill_coverage": 0.25,
    "resume_job_match": 0.25,
    "interview_performance": 0.35,
    "experience": 0.15,
}

# Fallback question templates keyed by skill name (used when LLM is unavailable)
_SKILL_QUESTION_TEMPLATES: dict[str, tuple[str, str]] = {
    "python": ("Tell me about a complex Python project you built. What design decisions did you make?", "python"),
    "fastapi": ("How would you design and structure a FastAPI service for a high-traffic production API?", "fastapi"),
    "docker": ("Explain your approach to containerising a Python application, including multi-stage builds.", "docker"),
    "kubernetes": ("Describe how you have deployed or managed workloads on Kubernetes.", "kubernetes"),
    "aws": ("Walk me through how you have used AWS services in a past project.", "cloud"),
    "postgresql": ("How do you approach database schema design and query optimisation in PostgreSQL?", "databases"),
    "machine learning": ("Describe the end-to-end ML pipeline you are most proud of.", "machine learning"),
    "react": ("How do you manage state and component lifecycle in a large React application?", "frontend"),
    "typescript": ("What benefits has TypeScript brought to a project you worked on?", "typescript"),
    "terraform": ("How have you managed infrastructure-as-code with Terraform at scale?", "devops"),
    "ci/cd": ("Walk me through your CI/CD setup on a recent project.", "devops"),
    "llm": ("How have you integrated large language models into a product? What challenges arose?", "ai"),
    "sql": ("Explain a complex SQL query or schema migration you have written.", "databases"),
}

_GENERIC_QUESTIONS: list[tuple[str, str, str, str]] = [
    ("Tell me about yourself and your most relevant technical experience.", "intro", "easy", "general"),
    ("Describe a technically challenging problem you solved. What was your approach?", "problem solving", "medium", "general"),
    ("How do you ensure code quality and reliability in a team environment?", "engineering practices", "medium", "general"),
    ("Talk about a time you had to learn a new technology quickly. How did you approach it?", "learning agility", "easy", "general"),
    ("Describe a production incident you handled. What did you do and what did you learn?", "incident response", "hard", "general"),
]

# ---------------------------------------------------------------------------
# Internal session state (ephemeral — lost on restart)
# ---------------------------------------------------------------------------


@dataclass
class _QuestionRecord:
    question: InterviewQuestion
    answer: Optional[str] = None
    feedback: Optional[AnswerFeedback] = None


@dataclass
class _InterviewSession:
    session_id: str
    resume_text: str
    job_title: str
    job_description: str
    max_questions: int
    skill_gap: dict[str, Any]           # raw deterministic gap data
    years_experience: float
    questions: list[_QuestionRecord] = field(default_factory=list)
    topics_covered: set[str] = field(default_factory=set)
    is_complete: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ⚠️ Ephemeral store — lost on backend restart. Not persisted to any database.
_interview_sessions: dict[str, _InterviewSession] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_profile(
    resume_text: str,
    job_title: str,
    job_description: str,
) -> CandidateProfileAnalysis:
    """
    Analyse a candidate's resume against a job description.

    Deterministic parts (skill gap) always succeed.
    LLM parts (narrative, improvement suggestions) degrade gracefully.
    """
    gap_data = _compute_skill_gap(resume_text, job_description)
    available = llm_client.is_available()
    llm_err: str | None = None
    narrative: str | None = None
    suggestions: list[ResumeSuggestion] = []
    imp_summary: str | None = None

    if available:
        try:
            llm_result = _llm_profile_analysis(gap_data, resume_text, job_title, job_description)
            narrative = llm_result.get("narrative")
            raw_suggestions = llm_result.get("improvement_suggestions", [])
            suggestions = _parse_suggestions(raw_suggestions)
            imp_summary = llm_result.get("improvement_summary")
        except LLMError as exc:
            available = False
            llm_err = _friendly_llm_error(exc)

    if not suggestions:
        suggestions = _fallback_suggestions(gap_data)

    skill_gap = SkillGapResult(
        matched_skills=gap_data["matched_skills"],
        missing_skills=gap_data["missing_skills"],
        partially_covered_skills=gap_data["partially_covered_skills"],
        gap_severity=gap_data["gap_severity"],
        match_percentage=gap_data["match_percentage"],
        required_skills=gap_data["required_skills"],
        narrative=narrative,
    )
    improvement = ResumeImprovementResult(suggestions=suggestions, summary=imp_summary)
    return CandidateProfileAnalysis(
        skill_gap=skill_gap,
        resume_improvement=improvement,
        llm_available=available,
        llm_error=llm_err,
    )


def generate_interview_questions(
    resume_text: str,
    job_title: str,
    job_description: str,
    max_questions: int = 5,
) -> GenerateQuestionsResponse:
    """Generate a list of interview questions for the candidate."""
    gap_data = _compute_skill_gap(resume_text, job_description)
    available = llm_client.is_available()
    llm_err: str | None = None
    questions: list[InterviewQuestion] = []

    if available:
        try:
            questions = _llm_generate_questions(gap_data, resume_text, job_title, job_description, max_questions)
        except LLMError as exc:
            available = False
            llm_err = _friendly_llm_error(exc)

    if not questions:
        questions = _fallback_questions(gap_data, max_questions)

    return GenerateQuestionsResponse(questions=questions, llm_available=available, llm_error=llm_err)


def create_interview_session(
    resume_text: str,
    job_title: str,
    job_description: str,
    max_questions: int = 5,
) -> tuple[str, MockInterviewStartResponse]:
    """
    Create a new in-memory interview session and return the first question.

    Returns (session_id, MockInterviewStartResponse).
    """
    gap_data = _compute_skill_gap(resume_text, job_description)
    _, years_experience = _extract_experience(resume_text)
    available = llm_client.is_available()
    llm_err: str | None = None

    # Generate all planned questions up-front (we'll serve them adaptively)
    planned: list[InterviewQuestion] = []
    if available:
        try:
            planned = _llm_generate_questions(gap_data, resume_text, job_title, job_description, max_questions)
        except LLMError as exc:
            available = False
            llm_err = _friendly_llm_error(exc)

    if not planned:
        planned = _fallback_questions(gap_data, max_questions)

    session_id = str(uuid.uuid4())
    session = _InterviewSession(
        session_id=session_id,
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
        max_questions=max_questions,
        skill_gap=gap_data,
        years_experience=years_experience,
    )
    # Queue all planned questions as records (answers will be filled later)
    for q in planned:
        session.questions.append(_QuestionRecord(question=q))

    _interview_sessions[session_id] = session

    first = session.questions[0].question
    return session_id, MockInterviewStartResponse(
        session_id=session_id,
        first_question=first,
        total_planned=len(planned),
        llm_available=available,
        llm_error=llm_err,
    )


def process_interview_answer(session_id: str, answer: str) -> MockInterviewAnswerResponse:
    """
    Record the candidate's answer to the current question, evaluate it, and
    return feedback plus the next question (or mark the interview complete).

    Raises:
        KeyError: Session not found.
        RuntimeError: No pending question in this session.
    """
    session = _interview_sessions.get(session_id)
    if session is None:
        raise KeyError(session_id)

    # Find the current unanswered question
    current_idx = next(
        (i for i, r in enumerate(session.questions) if r.answer is None),
        None,
    )
    if current_idx is None:
        raise RuntimeError("No pending question in this session.")

    record = session.questions[current_idx]
    record.answer = answer

    # -- Evaluate answer --
    available = llm_client.is_available()
    llm_err: str | None = None
    feedback: AnswerFeedback
    next_question: InterviewQuestion | None = None

    if available:
        try:
            remaining = len([r for r in session.questions if r.answer is None and r != record]) - 1
            remaining = max(remaining, 0)
            feedback, next_q_data = _llm_evaluate_answer(
                session, record, current_idx, remaining
            )
            record.feedback = feedback
            session.topics_covered.add(record.question.topic)

            # Decide next question
            next_question = _resolve_next_question(
                session, current_idx, next_q_data, available
            )
        except LLMError as exc:
            available = False
            llm_err = _friendly_llm_error(exc)
            feedback = _fallback_evaluation(answer, record.question)
            record.feedback = feedback
            session.topics_covered.add(record.question.topic)
            next_question = _next_planned_question(session, current_idx)
    else:
        feedback = _fallback_evaluation(answer, record.question)
        record.feedback = feedback
        session.topics_covered.add(record.question.topic)
        next_question = _next_planned_question(session, current_idx)

    question_number = current_idx + 1
    total = len(session.questions)
    is_complete = (next_question is None) or (question_number >= session.max_questions)

    if is_complete:
        session.is_complete = True

    return MockInterviewAnswerResponse(
        feedback=feedback,
        next_question=None if is_complete else next_question,
        question_number=question_number,
        total_questions=total,
        is_complete=is_complete,
        llm_error=llm_err,
    )


def get_interview_summary(session_id: str) -> InterviewSummaryResponse:
    """
    Compute the final readiness report for a completed (or in-progress) session.

    Raises:
        KeyError: Session not found.
    """
    session = _interview_sessions.get(session_id)
    if session is None:
        raise KeyError(session_id)

    answered = [r for r in session.questions if r.answer is not None]
    answer_scores = [
        r.feedback.scores.overall_answer_score
        for r in answered
        if r.feedback is not None
    ]
    avg_answer = round(sum(answer_scores) / len(answer_scores), 1) if answer_scores else 0.0

    dimension_averages: dict[str, float] = {}
    if answered:
        for dim in [
            "technical_accuracy",
            "relevance",
            "completeness",
            "communication_clarity",
            "answer_structure",
        ]:
            dim_vals = [
                getattr(r.feedback.scores, dim)
                for r in answered
                if r.feedback is not None and hasattr(r.feedback.scores, dim)
            ]
            dimension_averages[dim] = round(sum(dim_vals) / len(dim_vals), 1) if dim_vals else 0.0


    breakdown = _compute_readiness_score(
        session.skill_gap,
        answer_scores,
        session.years_experience,
        is_session_complete=session.is_complete,
    )

    readiness = breakdown.final_score
    band = _readiness_band(readiness)

    available = llm_client.is_available()
    llm_err: str | None = None
    narrative: str | None = None
    roadmap: list[PreparationRoadmapItem] = []

    if available:
        try:
            llm_result = _llm_generate_summary(session, breakdown, avg_answer, band)
            narrative = llm_result.get("narrative")
            roadmap = _parse_roadmap(llm_result.get("roadmap", []))
        except LLMError as exc:
            available = False
            llm_err = _friendly_llm_error(exc)

    if not roadmap:
        roadmap = _fallback_roadmap(session.skill_gap, band)

    return InterviewSummaryResponse(
        session_id=session_id,
        readiness_score=readiness,
        readiness_band=band,
        score_breakdown=breakdown,
        narrative=narrative,
        questions_answered=len(answered),
        average_answer_score=avg_answer,
        dimension_averages=dimension_averages,
        preparation_roadmap=roadmap,
        llm_available=available,
        llm_error=llm_err,
        is_complete=session.is_complete,
        assessment_status=breakdown.assessment_status,
        status_message=breakdown.formula_explanation,
    )


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


def _compute_skill_gap(resume_text: str, job_description: str) -> dict[str, Any]:
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description)
    semantic_map = get_semantic_skill_matches(list(jd_skills), resume_skills)

    exact_match = sorted(jd_skills & resume_skills)
    semantic_covered = sorted(semantic_map.keys())
    all_matched = sorted(set(exact_match) | set(semantic_covered))
    missing = sorted(jd_skills - resume_skills - set(semantic_covered))
    partially = sorted(set(semantic_covered) - set(exact_match))

    total = len(jd_skills)
    weighted_hits = len(exact_match) + 0.6 * len(semantic_covered)
    match_pct = round((weighted_hits / total * 100) if total else 0.0, 1)

    if match_pct >= 80:
        severity = "low"
    elif match_pct >= 60:
        severity = "moderate"
    elif match_pct >= 40:
        severity = "high"
    else:
        severity = "critical"

    return {
        "matched_skills": all_matched,
        "missing_skills": missing,
        "partially_covered_skills": partially,
        "gap_severity": severity,
        "match_percentage": match_pct,
        "required_skills": sorted(jd_skills),
    }


def _extract_experience(resume_text: str) -> tuple[str, float]:
    """Reuse existing parser without importing the full route layer."""
    from app.services.resume_parser import extract_candidate_profile
    return extract_candidate_profile(resume_text, "resume.txt")


def _experience_score(years: float) -> float:
    """Mirror of scoring.py logic, kept local to avoid coupling."""
    if years >= 8:
        return 100.0
    if years >= 5:
        return 85.0
    if years >= 3:
        return 70.0
    if years >= 1:
        return 50.0
    return 30.0


def _compute_readiness_score(
    gap_data: dict[str, Any],
    answer_scores: list[float],
    years_experience: float,
    is_session_complete: bool = False,
) -> ReadinessScoreBreakdown:
    """
    Deterministic readiness score using documented weights.

    Components:
        skill_coverage:        0.25 — fraction of JD skills matched (exact + semantic)
        resume_job_match:      0.25 — exact-only match fraction (stricter)
        interview_performance: 0.35 — average overall_answer_score across all answers
        experience:            0.15 — bands: 0 yrs→30, 1→50, 3→70, 5→85, 8+→100

    If no answers submitted (len(answer_scores) == 0):
        interview_performance_score = None
        assessment_status = "preliminary"
        is_preliminary = True
        final_score = normalized sum of available components / 0.65
        formula_explanation = "Preliminary Profile Assessment: (Skill Coverage 25% + Resume Match 25% + Experience 15%) / 0.65 normalized. Complete the mock interview to unlock full readiness score."

    If partially answered (len(answer_scores) > 0 and not is_session_complete):
        interview_performance_score = average of answered questions
        assessment_status = "in_progress"
        is_preliminary = True
        final_score = full weighted formula with current interview average
        formula_explanation = "In-Progress Interview Assessment: Skill Coverage (25%) + Resume Match (25%) + Interview Perf so far (35%) + Experience (15%). Complete remaining questions for final assessment."

    If completed (is_session_complete):
        interview_performance_score = average of all questions
        assessment_status = "final"
        is_preliminary = False
        final_score = full weighted formula
        formula_explanation = "Final Readiness Assessment: Skill Coverage (25%) + Resume Match (25%) + Interview Performance (35%) + Experience (15%)."
    """
    required = gap_data["required_skills"]
    total = len(required)

    skill_coverage = gap_data["match_percentage"]

    exact_matched = len(set(gap_data["matched_skills"]) - set(gap_data["partially_covered_skills"]))
    resume_job_match = round((exact_matched / total * 100) if total else 0.0, 1)

    exp_score = _experience_score(years_experience)

    W = _READINESS_WEIGHTS

    if not answer_scores:
        interview_perf = None
        available_weight_sum = W["skill_coverage"] + W["resume_job_match"] + W["experience"]
        available_score_sum = (
            W["skill_coverage"] * skill_coverage
            + W["resume_job_match"] * resume_job_match
            + W["experience"] * exp_score
        )
        final = round(available_score_sum / available_weight_sum, 1)
        assessment_status = "preliminary"
        is_preliminary = True
        formula_explanation = (
            "Preliminary Profile Assessment: Normalized from available profile components "
            "(Skill Coverage 25% + Resume Match 25% + Experience 15%) / 0.65. "
            "Complete the mock interview to unlock your full readiness score."
        )
    else:
        interview_perf = round(sum(answer_scores) / len(answer_scores), 1)
        final = round(
            W["skill_coverage"] * skill_coverage
            + W["resume_job_match"] * resume_job_match
            + W["interview_performance"] * interview_perf
            + W["experience"] * exp_score,
            1,
        )
        if is_session_complete:
            assessment_status = "final"
            is_preliminary = False
            formula_explanation = (
                "Final Readiness Assessment: Skill Coverage (25%) + Resume Match (25%) "
                "+ Interview Performance (35%) + Experience (15%)."
            )
        else:
            assessment_status = "in_progress"
            is_preliminary = True
            formula_explanation = (
                f"In-Progress Interview Assessment: Skill Coverage (25%) + Resume Match (25%) "
                f"+ Interview Perf so far ({interview_perf:.1f}) (35%) + Experience (15%). "
                "Complete remaining questions for final assessment."
            )

    return ReadinessScoreBreakdown(
        skill_coverage_score=skill_coverage,
        resume_job_match_score=resume_job_match,
        interview_performance_score=interview_perf,
        experience_score=exp_score,
        final_score=final,
        weights=W,
        is_preliminary=is_preliminary,
        assessment_status=assessment_status,
        formula_explanation=formula_explanation,
    )


def _compute_overall_answer_score(scores: dict[str, float]) -> float:

    W = _ANSWER_SCORE_WEIGHTS
    return round(
        W["technical_accuracy"] * scores.get("technical_accuracy", 0)
        + W["relevance"] * scores.get("relevance", 0)
        + W["completeness"] * scores.get("completeness", 0)
        + W["communication_clarity"] * scores.get("communication_clarity", 0)
        + W["answer_structure"] * scores.get("answer_structure", 0),
        1,
    )


def _readiness_band(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 65:
        return "ready"
    if score >= 50:
        return "almost_ready"
    if score >= 35:
        return "needs_work"
    return "not_ready"


# ---------------------------------------------------------------------------
# Fallback logic (used when LLM is unavailable)
# ---------------------------------------------------------------------------


def _fallback_suggestions(gap_data: dict[str, Any]) -> list[ResumeSuggestion]:
    suggestions: list[ResumeSuggestion] = []
    missing = gap_data["missing_skills"]
    if missing:
        suggestions.append(ResumeSuggestion(
            category="skills",
            suggestion=f"Add hands-on projects or certifications covering: {', '.join(missing[:5])}.",
            priority="high",
        ))
    suggestions.append(ResumeSuggestion(
        category="keywords",
        suggestion="Tailor your resume to mirror the exact terminology used in the job description.",
        priority="medium",
    ))
    suggestions.append(ResumeSuggestion(
        category="achievements",
        suggestion="Quantify your impact with metrics (e.g., 'reduced latency by 40%', 'served 10k req/s').",
        priority="medium",
    ))
    return suggestions


def _fallback_questions(gap_data: dict[str, Any], max_q: int) -> list[InterviewQuestion]:
    questions: list[InterviewQuestion] = []
    seen_topics: set[str] = set()

    # Target missing skills first
    for skill in gap_data["missing_skills"]:
        if len(questions) >= max_q:
            break
        if skill in _SKILL_QUESTION_TEMPLATES:
            text, topic = _SKILL_QUESTION_TEMPLATES[skill]
            if topic not in seen_topics:
                seen_topics.add(topic)
                questions.append(InterviewQuestion(
                    question_id=str(uuid.uuid4()),
                    text=text,
                    topic=topic,
                    difficulty="medium",
                    target_skill=skill,
                    question_type="planned",
                ))

    # Fill remaining slots with generic questions
    for text, topic, difficulty, skill in _GENERIC_QUESTIONS:
        if len(questions) >= max_q:
            break
        if topic not in seen_topics:
            seen_topics.add(topic)
            questions.append(InterviewQuestion(
                question_id=str(uuid.uuid4()),
                text=text,
                topic=topic,
                difficulty=difficulty,
                target_skill=skill if skill != "general" else None,
                question_type="planned",
            ))

    return questions[:max_q]


def _fallback_evaluation(answer: str, question: InterviewQuestion) -> AnswerFeedback:
    """
    Keyword-based fallback evaluation when LLM is unavailable.
    Returns neutral scores with a note that LLM evaluation is disabled.
    """
    answer_lower = answer.lower()
    skill_mentioned = question.target_skill and question.target_skill in answer_lower
    tech_score = 60.0 if skill_mentioned else 40.0

    # Length-based completeness heuristic
    words = len(answer.split())
    completeness = min(100.0, max(20.0, words * 2.0))

    scores_raw = {
        "technical_accuracy": tech_score,
        "relevance": 50.0,
        "completeness": completeness,
        "communication_clarity": 50.0,
        "answer_structure": 50.0,
    }
    overall = _compute_overall_answer_score(scores_raw)

    return AnswerFeedback(
        scores=AnswerScores(
            technical_accuracy=scores_raw["technical_accuracy"],
            relevance=scores_raw["relevance"],
            completeness=scores_raw["completeness"],
            communication_clarity=scores_raw["communication_clarity"],
            answer_structure=scores_raw["answer_structure"],
            overall_answer_score=overall,
        ),
        strengths=["Answer recorded."],
        weaknesses=["AI evaluation is unavailable — scores are estimates only."],
        missing_concepts=[],
        improvement_suggestions=["Enable the OpenAI API key for detailed feedback."],
        improved_answer_example="(AI evaluation unavailable — please review the model answer manually.)",
    )


def _fallback_roadmap(gap_data: dict[str, Any], band: str) -> list[PreparationRoadmapItem]:
    items: list[PreparationRoadmapItem] = []
    priority = 1

    if gap_data["missing_skills"]:
        items.append(PreparationRoadmapItem(
            priority=priority,
            category="technical_skill",
            action=f"Build or expand experience with: {', '.join(gap_data['missing_skills'][:4])}",
            timeline="2–4 weeks",
        ))
        priority += 1

    if band in ("not_ready", "needs_work"):
        items.append(PreparationRoadmapItem(
            priority=priority,
            category="practice",
            action="Complete at least 3 LeetCode/system design problems per week targeting role-relevant patterns.",
            timeline="Ongoing",
        ))
        priority += 1

    items.append(PreparationRoadmapItem(
        priority=priority,
        category="portfolio",
        action="Add a project to your resume that demonstrates end-to-end ownership of a technical problem.",
        timeline="1–3 months",
    ))
    priority += 1

    items.append(PreparationRoadmapItem(
        priority=priority,
        category="practice",
        action="Record yourself answering behavioural (STAR format) and technical questions to improve delivery.",
        timeline="1–2 weeks",
    ))
    return items


def _next_planned_question(
    session: _InterviewSession, current_idx: int
) -> Optional[InterviewQuestion]:
    """Return the next unanswered planned question after current_idx."""
    for record in session.questions[current_idx + 1:]:
        if record.answer is None:
            return record.question
    return None


# ---------------------------------------------------------------------------
# LLM-powered helpers
# ---------------------------------------------------------------------------


def _llm_profile_analysis(
    gap_data: dict[str, Any],
    resume_text: str,
    job_title: str,
    job_description: str,
) -> dict[str, Any]:
    system = (
        "You are an expert technical recruiter and career coach. "
        "Analyse the candidate's skill gap and return ONLY a valid JSON object "
        "with keys: narrative (string), improvement_suggestions (array of objects "
        "each with keys category, suggestion, priority), improvement_summary (string). "
        "Be specific, constructive, and concise."
    )
    user = (
        f"Job Title: {job_title}\n"
        f"Required Skills: {', '.join(gap_data['required_skills']) or 'none detected'}\n"
        f"Matched Skills: {', '.join(gap_data['matched_skills']) or 'none'}\n"
        f"Missing Skills: {', '.join(gap_data['missing_skills']) or 'none'}\n"
        f"Gap Severity: {gap_data['gap_severity']} ({gap_data['match_percentage']:.0f}% match)\n\n"
        f"Resume (first 2000 chars):\n{resume_text[:2000]}\n\n"
        f"Job Description (first 1500 chars):\n{job_description[:1500]}"
    )
    return llm_client.chat_json(system, user, temperature=0.4)


def _llm_generate_questions(
    gap_data: dict[str, Any],
    resume_text: str,
    job_title: str,
    job_description: str,
    max_questions: int,
) -> list[InterviewQuestion]:
    system = (
        "You are an expert technical interviewer. Generate interview questions "
        "and return ONLY a valid JSON object with a single key 'questions'. "
        "Each question must have: text, topic, difficulty (easy|medium|hard), target_skill (string or null). "
        "Mix technical depth with behavioural questions. Target identified skill gaps."
    )
    user = (
        f"Job Title: {job_title}\n"
        f"Missing Skills (priority): {', '.join(gap_data['missing_skills'][:6]) or 'none'}\n"
        f"Candidate Skills: {', '.join(gap_data['matched_skills'][:8]) or 'none'}\n"
        f"Number of questions needed: {max_questions}\n\n"
        f"Resume Summary (first 1200 chars):\n{resume_text[:1200]}\n\n"
        f"Job Description (first 800 chars):\n{job_description[:800]}"
    )
    result = llm_client.chat_json(system, user, temperature=0.6)
    raw_qs = result.get("questions", [])
    questions: list[InterviewQuestion] = []
    seen_topics: set[str] = set()
    for raw in raw_qs:
        if not isinstance(raw, dict):
            continue
        text = raw.get("text", "").strip()
        topic = raw.get("topic", "general").strip()
        if not text or topic in seen_topics:
            continue
        seen_topics.add(topic)
        difficulty = raw.get("difficulty", "medium")
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"
        questions.append(InterviewQuestion(
            question_id=str(uuid.uuid4()),
            text=text,
            topic=topic,
            difficulty=difficulty,
            target_skill=raw.get("target_skill") or None,
            question_type="planned",
        ))
    return questions[:max_questions]


def _llm_evaluate_answer(
    session: _InterviewSession,
    record: _QuestionRecord,
    current_idx: int,
    remaining: int,
) -> tuple[AnswerFeedback, dict[str, Any]]:
    system = (
        "You are an expert technical interviewer evaluating a candidate's answer. "
        "Return ONLY a valid JSON object with keys:\n"
        "  scores: {technical_accuracy, relevance, completeness, communication_clarity, answer_structure} (int 0-100 each)\n"
        "  feedback: {strengths (array), weaknesses (array), missing_concepts (array), "
        "improvement_suggestions (array), improved_answer_example (string)}\n"
        "  next_decision: {strategy ('follow_up'|'new_topic'), reasoning (string), "
        "follow_up_question: {text, topic, difficulty} (only if strategy='follow_up')}\n"
        "Use 'follow_up' only if the answer reveals a concept worth probing deeper AND remaining > 1. "
        "Use 'new_topic' otherwise."
    )
    user = (
        f"Job Title: {session.job_title}\n"
        f"Required Skills: {', '.join(session.skill_gap['required_skills'][:8])}\n"
        f"Missing Skills: {', '.join(session.skill_gap['missing_skills'][:5])}\n\n"
        f"Question #{current_idx + 1}: {record.question.text}\n"
        f"Topic: {record.question.topic}\n\n"
        f"Candidate Answer:\n{record.answer}\n\n"
        f"Topics already covered: {', '.join(session.topics_covered) or 'none'}\n"
        f"Questions remaining after this: {remaining}"
    )
    result = llm_client.chat_json(system, user, temperature=0.3)

    raw_scores = result.get("scores", {})
    raw_scores = {k: float(max(0, min(100, v))) for k, v in raw_scores.items() if isinstance(v, (int, float))}
    overall = _compute_overall_answer_score(raw_scores)

    scores = AnswerScores(
        technical_accuracy=raw_scores.get("technical_accuracy", 50.0),
        relevance=raw_scores.get("relevance", 50.0),
        completeness=raw_scores.get("completeness", 50.0),
        communication_clarity=raw_scores.get("communication_clarity", 50.0),
        answer_structure=raw_scores.get("answer_structure", 50.0),
        overall_answer_score=overall,
    )
    raw_fb = result.get("feedback", {})
    feedback = AnswerFeedback(
        scores=scores,
        strengths=_ensure_str_list(raw_fb.get("strengths", [])),
        weaknesses=_ensure_str_list(raw_fb.get("weaknesses", [])),
        missing_concepts=_ensure_str_list(raw_fb.get("missing_concepts", [])),
        improvement_suggestions=_ensure_str_list(raw_fb.get("improvement_suggestions", [])),
        improved_answer_example=str(raw_fb.get("improved_answer_example", "")),
    )
    next_decision = result.get("next_decision", {})
    return feedback, next_decision


def _resolve_next_question(
    session: _InterviewSession,
    current_idx: int,
    next_decision: dict[str, Any],
    llm_available: bool,
) -> InterviewQuestion | None:
    answered_count = current_idx + 1
    if answered_count >= session.max_questions:
        return None

    strategy = next_decision.get("strategy", "new_topic")

    # Adaptive follow-up (LLM suggested digging deeper)
    if strategy == "follow_up" and llm_available:
        fq = next_decision.get("follow_up_question", {})
        text = fq.get("text", "").strip()
        if text:
            follow_up = InterviewQuestion(
                question_id=str(uuid.uuid4()),
                text=text,
                topic=fq.get("topic", "follow-up"),
                difficulty=fq.get("difficulty", "medium"),
                target_skill=None,
                question_type="adaptive_follow_up",
            )
            # Insert follow-up right after current position
            insert_at = current_idx + 1
            session.questions.insert(insert_at, _QuestionRecord(question=follow_up))
            return follow_up

    # Fall back to next planned question
    return _next_planned_question(session, current_idx)


def _llm_generate_summary(
    session: _InterviewSession,
    breakdown: ReadinessScoreBreakdown,
    avg_answer: float,
    band: str,
) -> dict[str, Any]:
    system = (
        "You are an expert career coach providing an interview debrief. "
        "Return ONLY a valid JSON object with keys:\n"
        "  narrative (string, 3-4 sentences — balanced, honest, encouraging)\n"
        "  roadmap (array of objects with: priority (int), category (string), "
        "action (string), timeline (string), resources (array of strings, max 3))\n"
        "Max 6 roadmap items. Prioritise by career impact."
    )
    answered = [r for r in session.questions if r.answer]
    user = (
        f"Job Title: {session.job_title}\n"
        f"Readiness Score: {breakdown.final_score}/100 (band: {band})\n"
        f"  Skill Coverage: {breakdown.skill_coverage_score:.0f}/100\n"
        f"  Resume-Job Match: {breakdown.resume_job_match_score:.0f}/100\n"
        f"  Interview Performance: {breakdown.interview_performance_score:.0f}/100\n"
        f"  Experience Score: {breakdown.experience_score:.0f}/100\n\n"
        f"Questions Answered: {len(answered)}\n"
        f"Average Answer Score: {avg_answer:.0f}/100\n\n"
        f"Missing Skills (top gaps): {', '.join(session.skill_gap['missing_skills'][:5]) or 'none'}\n"
        f"Matched Skills: {', '.join(session.skill_gap['matched_skills'][:6]) or 'none'}\n\n"
        f"Job Description (first 600 chars):\n{session.job_description[:600]}"
    )
    return llm_client.chat_json(system, user, temperature=0.5)


# ---------------------------------------------------------------------------
# Parsing + utility helpers
# ---------------------------------------------------------------------------


def _parse_suggestions(raw: list[Any]) -> list[ResumeSuggestion]:
    results: list[ResumeSuggestion] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        priority = item.get("priority", "medium")
        if priority not in ("high", "medium", "low"):
            priority = "medium"
        suggestion = str(item.get("suggestion", "")).strip()
        if not suggestion:
            continue
        results.append(ResumeSuggestion(
            category=str(item.get("category", "general")),
            suggestion=suggestion,
            priority=priority,
        ))
    return results


def _parse_roadmap(raw: list[Any]) -> list[PreparationRoadmapItem]:
    results: list[PreparationRoadmapItem] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "")).strip()
        if not action:
            continue
        results.append(PreparationRoadmapItem(
            priority=int(item.get("priority", idx + 1)),
            category=str(item.get("category", "general")),
            action=action,
            timeline=str(item.get("timeline", "TBD")),
            resources=[str(r) for r in item.get("resources", []) if r],
        ))
    return results


def _ensure_str_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if item]


def _friendly_llm_error(exc: LLMError) -> str:
    from app.services.llm_client import LLMAuthError, LLMRateLimitError, LLMUnavailableError
    if isinstance(exc, LLMUnavailableError):
        return "AI features disabled: OPENAI_API_KEY not configured."
    if isinstance(exc, LLMAuthError):
        return "AI service rejected the API key. Check your OPENAI_API_KEY."
    if isinstance(exc, LLMRateLimitError):
        return "AI service rate limit reached. Please wait a moment and retry."
    return "AI service temporarily unavailable. Deterministic results shown."
