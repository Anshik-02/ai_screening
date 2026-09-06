from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RoleFamily = Literal["backend", "frontend", "data_ai", "devops", "fullstack"]


class CandidateInput(BaseModel):
    name: str = Field(..., min_length=1)
    resume_text: str = Field(..., min_length=30)
    years_experience: float = Field(0, ge=0)


class AnalyzeRequest(BaseModel):
    job_title: str = Field(..., min_length=2)
    job_description: str = Field(..., min_length=50)
    candidates: list[CandidateInput] = Field(..., min_length=1)
    role_family: RoleFamily | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)


class CandidateScore(BaseModel):
    name: str
    total_score: float
    role_family: RoleFamily
    skill_score: float
    must_have_match_rate: float
    nice_to_have_match_rate: float
    experience_score: float
    hard_constraint_passed: bool
    matched_skills: list[str]
    missing_skills: list[str]
    semantic_matches: dict[str, list[str]]
    strengths: list[str]
    concerns: list[str]


class AnalyzeResponse(BaseModel):
    job_title: str
    role_family: RoleFamily
    required_skills: list[str]
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    ranked_candidates: list[CandidateScore]


class UploadProfilePreview(BaseModel):
    file_name: str
    status: Literal["ok", "error"]
    candidate_name: str | None = None
    years_experience: float | None = None
    detected_skills: list[str] = Field(default_factory=list)
    message: str | None = None


class PreviewFilesResponse(BaseModel):
    previews: list[UploadProfilePreview]


# =============================================================================
# Candidate Mode Schemas
# =============================================================================

QuestionDifficulty = Literal["easy", "medium", "hard"]
QuestionType = Literal["planned", "adaptive_follow_up"]
GapSeverity = Literal["low", "moderate", "high", "critical"]
ReadinessBand = Literal["not_ready", "needs_work", "almost_ready", "ready", "strong"]


# --- Profile Analysis ---

class CandidateAnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=30)
    job_title: str = Field(..., min_length=2)
    job_description: str = Field(..., min_length=20)


class SkillGapResult(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    partially_covered_skills: list[str]
    gap_severity: GapSeverity
    match_percentage: float
    required_skills: list[str]
    narrative: str | None = None          # LLM-generated; None when unavailable


class ResumeSuggestion(BaseModel):
    category: str                          # "skills", "experience", "format", etc.
    suggestion: str
    priority: Literal["high", "medium", "low"]


class ResumeImprovementResult(BaseModel):
    suggestions: list[ResumeSuggestion]
    summary: str | None = None            # LLM-generated; None when unavailable


class CandidateProfileAnalysis(BaseModel):
    skill_gap: SkillGapResult
    resume_improvement: ResumeImprovementResult
    llm_available: bool
    llm_error: str | None = None          # Human-readable error when llm_available=False


# --- Interview Questions ---

class InterviewQuestion(BaseModel):
    question_id: str
    text: str
    topic: str
    difficulty: QuestionDifficulty
    target_skill: str | None = None
    question_type: QuestionType


class GenerateQuestionsRequest(BaseModel):
    resume_text: str = Field(..., min_length=30)
    job_title: str = Field(..., min_length=2)
    job_description: str = Field(..., min_length=20)
    max_questions: int = Field(default=5, ge=3, le=10)


class GenerateQuestionsResponse(BaseModel):
    questions: list[InterviewQuestion]
    llm_available: bool
    llm_error: str | None = None


# --- Mock Interview ---

class MockInterviewStartRequest(BaseModel):
    resume_text: str = Field(..., min_length=30)
    job_title: str = Field(..., min_length=2)
    job_description: str = Field(..., min_length=20)
    max_questions: int = Field(default=5, ge=3, le=10)


class MockInterviewStartResponse(BaseModel):
    session_id: str
    first_question: InterviewQuestion
    total_planned: int
    llm_available: bool
    llm_error: str | None = None


class AnswerScores(BaseModel):
    technical_accuracy: float
    relevance: float
    completeness: float
    communication_clarity: float
    answer_structure: float
    overall_answer_score: float           # Deterministic weighted average (Python-computed)


class AnswerFeedback(BaseModel):
    scores: AnswerScores
    strengths: list[str]
    weaknesses: list[str]
    missing_concepts: list[str]
    improvement_suggestions: list[str]
    improved_answer_example: str


class MockInterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str = Field(..., min_length=1)


class MockInterviewAnswerResponse(BaseModel):
    feedback: AnswerFeedback
    next_question: InterviewQuestion | None
    question_number: int                  # 1-based index of the question just answered
    total_questions: int
    is_complete: bool
    llm_error: str | None = None


# --- Readiness Report ---

class ReadinessScoreBreakdown(BaseModel):
    skill_coverage_score: float           # deterministic
    resume_job_match_score: float         # deterministic
    interview_performance_score: float | None = None    # average of overall_answer_score values or None if 0 answers
    experience_score: float               # deterministic (reuses scoring.py logic)
    final_score: float                    # weighted formula
    weights: dict[str, float]
    is_preliminary: bool = False
    assessment_status: str = "final"       # "preliminary" | "in_progress" | "final"
    formula_explanation: str = ""


class PreparationRoadmapItem(BaseModel):
    priority: int
    category: str
    action: str
    timeline: str
    resources: list[str] = Field(default_factory=list)


class InterviewSummaryResponse(BaseModel):
    session_id: str
    readiness_score: float
    readiness_band: ReadinessBand
    score_breakdown: ReadinessScoreBreakdown
    narrative: str | None = None          # LLM-generated; None when unavailable
    questions_answered: int
    average_answer_score: float
    dimension_averages: dict[str, float] = Field(default_factory=dict)
    preparation_roadmap: list[PreparationRoadmapItem]
    llm_available: bool
    llm_error: str | None = None
    is_complete: bool = False
    assessment_status: str = "final"
    status_message: str = ""



