"""
Unit tests for candidate_coach.py.

LLM client is patched throughout — zero real API calls.
Deterministic functions (skill gap, readiness score) are tested without any mocking.
"""
from unittest.mock import patch

import pytest

from app.services import candidate_coach
from app.services.candidate_coach import (
    _compute_skill_gap,
    _compute_readiness_score,
    _experience_score,
    _fallback_questions,
    _fallback_suggestions,
    _readiness_band,
)


# ---------------------------------------------------------------------------
# Deterministic skill gap
# ---------------------------------------------------------------------------


def test_skill_gap_detects_exact_matches():
    gap = _compute_skill_gap(
        "Python FastAPI Docker PostgreSQL AWS",
        "We need Python FastAPI and Docker skills.",
    )
    assert "python" in gap["matched_skills"]
    assert "fastapi" in gap["matched_skills"]
    assert "docker" in gap["matched_skills"]


def test_skill_gap_classifies_missing():
    gap = _compute_skill_gap(
        "Python Django",
        "Looking for Python, FastAPI, Kubernetes, Terraform.",
    )
    assert "kubernetes" in gap["missing_skills"]
    assert "terraform" in gap["missing_skills"]


def test_skill_gap_severity_critical_when_low_match():
    gap = _compute_skill_gap("Java Spring", "Python FastAPI Docker AWS Kubernetes Terraform")
    assert gap["gap_severity"] in ("high", "critical")
    assert gap["match_percentage"] < 40


def test_skill_gap_severity_low_when_full_match():
    gap = _compute_skill_gap(
        "Python FastAPI Docker AWS Kubernetes",
        "Python FastAPI Docker AWS.",
    )
    assert gap["gap_severity"] == "low"
    assert gap["match_percentage"] >= 80


def test_skill_gap_partial_semantic_coverage():
    # pytorch is semantically related to machine learning
    gap = _compute_skill_gap("PyTorch NLP", "machine learning experience required")
    # pytorch -> machine learning semantic
    assert gap["match_percentage"] > 0


# ---------------------------------------------------------------------------
# Experience score
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("years,expected", [
    (0, 30.0),
    (1, 50.0),
    (3, 70.0),
    (5, 85.0),
    (8, 100.0),
    (10, 100.0),
])
def test_experience_score_bands(years, expected):
    assert _experience_score(years) == expected


# ---------------------------------------------------------------------------
# Readiness score formula
# ---------------------------------------------------------------------------


def test_readiness_score_zero_interview_no_answers():
    gap = _compute_skill_gap("Python FastAPI", "Python FastAPI Docker")
    breakdown = _compute_readiness_score(gap, [], 3.0)
    # interview_performance should be None with no answers submitted
    assert breakdown.interview_performance_score is None
    assert breakdown.is_preliminary is True
    assert breakdown.assessment_status == "preliminary"
    # Should calculate preliminary score normalized from available components without zero-penalty
    expected_normalized = round(((0.25 * gap["match_percentage"]) + (0.25 * gap["match_percentage"]) + (0.15 * 70.0)) / 0.65, 1)
    assert abs(breakdown.final_score - expected_normalized) < 0.2



def test_readiness_score_full_match_high_answers_high_score():
    gap = _compute_skill_gap("Python FastAPI Docker AWS", "Python FastAPI Docker AWS")
    breakdown = _compute_readiness_score(gap, [90.0, 85.0, 88.0], 5.0)
    assert breakdown.final_score >= 75.0


def test_readiness_score_weights_sum_to_one():
    gap = _compute_skill_gap("Python", "Python")
    breakdown = _compute_readiness_score(gap, [50.0], 2.0)
    total_weight = sum(breakdown.weights.values())
    assert abs(total_weight - 1.0) < 1e-9


def test_readiness_band_thresholds():
    assert _readiness_band(85) == "strong"
    assert _readiness_band(70) == "ready"
    assert _readiness_band(55) == "almost_ready"
    assert _readiness_band(40) == "needs_work"
    assert _readiness_band(20) == "not_ready"


# ---------------------------------------------------------------------------
# Fallback questions (no LLM required)
# ---------------------------------------------------------------------------


def test_fallback_questions_respects_max():
    gap = _compute_skill_gap("Java", "Python FastAPI Docker AWS Kubernetes Terraform")
    questions = _fallback_questions(gap, 5)
    assert len(questions) <= 5


def test_fallback_questions_all_planned():
    gap = _compute_skill_gap("Java", "Python FastAPI Docker")
    questions = _fallback_questions(gap, 5)
    for q in questions:
        assert q.question_type == "planned"


def test_fallback_questions_no_duplicate_topics():
    gap = _compute_skill_gap("Java", "Python FastAPI Docker Kubernetes")
    questions = _fallback_questions(gap, 7)
    topics = [q.topic for q in questions]
    assert len(topics) == len(set(topics))


# ---------------------------------------------------------------------------
# Fallback suggestions
# ---------------------------------------------------------------------------


def test_fallback_suggestions_includes_missing_skills():
    gap = _compute_skill_gap("Java", "Python FastAPI Docker")
    suggestions = _fallback_suggestions(gap)
    assert len(suggestions) >= 1
    assert any("python" in s.suggestion.lower() or "fastapi" in s.suggestion.lower()
               or "missing" in s.suggestion.lower() or "docker" in s.suggestion.lower()
               for s in suggestions)


# ---------------------------------------------------------------------------
# analyze_profile — deterministic path (LLM unavailable)
# ---------------------------------------------------------------------------


def test_analyze_profile_succeeds_without_llm():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = candidate_coach.analyze_profile(
            resume_text="Python FastAPI Docker AWS CI/CD backend engineer 3 years",
            job_title="Backend Engineer",
            job_description="Looking for Python, FastAPI, Docker, AWS, and Kubernetes skills.",
        )
    assert result.llm_available is False
    assert len(result.skill_gap.matched_skills) >= 0
    assert len(result.resume_improvement.suggestions) > 0
    assert result.skill_gap.gap_severity in ("low", "moderate", "high", "critical")


# ---------------------------------------------------------------------------
# analyze_profile — LLM path (mocked)
# ---------------------------------------------------------------------------


def test_analyze_profile_uses_llm_narrative_when_available():
    mock_llm_result = {
        "narrative": "Strong candidate for backend roles.",
        "improvement_suggestions": [
            {"category": "skills", "suggestion": "Add Kubernetes.", "priority": "high"}
        ],
        "improvement_summary": "Focus on cloud-native skills.",
    }
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False):
        with patch("app.services.candidate_coach._llm_profile_analysis", return_value=mock_llm_result):
            result = candidate_coach.analyze_profile(
                resume_text="Python FastAPI Docker AWS backend engineer 3 years",
                job_title="Backend Engineer",
                job_description="Looking for Python FastAPI Docker AWS Kubernetes.",
            )
    assert result.llm_available is True
    assert result.skill_gap.narrative == "Strong candidate for backend roles."
    assert any(s.suggestion == "Add Kubernetes." for s in result.resume_improvement.suggestions)


# ---------------------------------------------------------------------------
# generate_interview_questions — fallback
# ---------------------------------------------------------------------------


def test_generate_questions_fallback_without_llm():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = candidate_coach.generate_interview_questions(
            resume_text="Python FastAPI 2 years experience",
            job_title="Backend Engineer",
            job_description="Looking for Python FastAPI Docker Kubernetes expertise.",
            max_questions=5,
        )
    assert result.llm_available is False
    assert 1 <= len(result.questions) <= 5


# ---------------------------------------------------------------------------
# Mock interview session lifecycle  (fallback, no LLM)
# ---------------------------------------------------------------------------


def test_interview_session_lifecycle_no_llm():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        # Start
        session_id, start_resp = candidate_coach.create_interview_session(
            resume_text="Python FastAPI Docker 3 years",
            job_title="Backend Engineer",
            job_description="Python FastAPI Docker Kubernetes AWS.",
            max_questions=3,
        )
        assert session_id in candidate_coach._interview_sessions
        assert start_resp.first_question is not None
        assert start_resp.total_planned >= 1

        # Answer Q1
        ans1 = candidate_coach.process_interview_answer(session_id, "I have used Python for 3 years.")
        assert ans1.question_number == 1
        assert ans1.feedback is not None
        assert 0.0 <= ans1.feedback.scores.overall_answer_score <= 100.0

        # Answer Q2 if not complete
        if not ans1.is_complete and ans1.next_question:
            ans2 = candidate_coach.process_interview_answer(session_id, "I deployed on AWS using Docker.")
            assert ans2.question_number == 2

        # Summary
        summary = candidate_coach.get_interview_summary(session_id)
        assert 0.0 <= summary.readiness_score <= 100.0
        assert summary.readiness_band in ("not_ready", "needs_work", "almost_ready", "ready", "strong")
        assert summary.questions_answered >= 1
        assert len(summary.preparation_roadmap) >= 1


def test_interview_answer_raises_for_unknown_session():
    with pytest.raises(KeyError):
        candidate_coach.process_interview_answer("nonexistent-session-id", "some answer")


def test_interview_summary_raises_for_unknown_session():
    with pytest.raises(KeyError):
        candidate_coach.get_interview_summary("nonexistent-session-id")


def test_interview_summary_includes_dimension_averages():
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        session_id, _ = candidate_coach.create_interview_session(
            resume_text="Python FastAPI Docker 3 years",
            job_title="Backend Engineer",
            job_description="Python FastAPI Docker Kubernetes AWS.",
            max_questions=2,
        )
        candidate_coach.process_interview_answer(session_id, "I have built REST APIs with Python and FastAPI for 3 years.")
        summary = candidate_coach.get_interview_summary(session_id)
        assert "technical_accuracy" in summary.dimension_averages
        assert "relevance" in summary.dimension_averages
        assert "completeness" in summary.dimension_averages
        assert "communication_clarity" in summary.dimension_averages
        assert "answer_structure" in summary.dimension_averages
        assert summary.dimension_averages["technical_accuracy"] >= 0.0


# ---------------------------------------------------------------------------
# Readiness Assessment State Audit Tests (No Interview / In-Progress / Final)
# ---------------------------------------------------------------------------


def test_readiness_assessment_case1_no_interview_started():
    """Case 1: No interview session created yet. Skill gap analysis only."""
    gap = candidate_coach._compute_skill_gap(
        "Python FastAPI Docker 3 years experience",
        "Python FastAPI Docker AWS Kubernetes",
    )
    breakdown = candidate_coach._compute_readiness_score(gap, [], 3.0)
    assert breakdown.interview_performance_score is None
    assert breakdown.is_preliminary is True
    assert breakdown.assessment_status == "preliminary"
    assert "Preliminary Profile Assessment" in breakdown.formula_explanation
    assert breakdown.final_score > 0.0


def test_readiness_assessment_case2_interview_started_no_answers():
    """Case 2: Interview session created, but candidate has not submitted any answers."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        session_id, _ = candidate_coach.create_interview_session(
            resume_text="Python FastAPI Docker 3 years experience",
            job_title="Backend Engineer",
            job_description="Python FastAPI Docker AWS Kubernetes",
            max_questions=3,
        )
        summary = candidate_coach.get_interview_summary(session_id)
        assert summary.questions_answered == 0
        assert summary.average_answer_score == 0.0
        assert summary.score_breakdown.interview_performance_score is None
        assert summary.score_breakdown.is_preliminary is True
        assert summary.score_breakdown.assessment_status == "preliminary"
        assert summary.is_complete is False
        assert "Preliminary Profile Assessment" in summary.status_message


def test_readiness_assessment_case3_partially_completed_interview():
    """Case 3: Interview in progress (1 of 2 questions answered)."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        session_id, _ = candidate_coach.create_interview_session(
            resume_text="Python FastAPI Docker 3 years experience",
            job_title="Backend Engineer",
            job_description="Python FastAPI Docker AWS Kubernetes",
            max_questions=2,
        )
        candidate_coach.process_interview_answer(
            session_id, "I use Python and FastAPI to build asynchronous microservices."
        )
        summary = candidate_coach.get_interview_summary(session_id)
        assert summary.questions_answered == 1
        assert summary.score_breakdown.interview_performance_score is not None
        assert summary.score_breakdown.interview_performance_score > 0
        assert summary.score_breakdown.is_preliminary is True
        assert summary.score_breakdown.assessment_status == "in_progress"
        assert summary.is_complete is False
        assert "In-Progress Interview Assessment" in summary.status_message


def test_readiness_assessment_case4_completed_interview():
    """Case 4: Completed interview (all questions answered)."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        session_id, _ = candidate_coach.create_interview_session(
            resume_text="Python FastAPI Docker 3 years experience",
            job_title="Backend Engineer",
            job_description="Python FastAPI Docker AWS Kubernetes",
            max_questions=1,
        )
        candidate_coach.process_interview_answer(
            session_id, "I use Python and FastAPI to build asynchronous microservices with Docker."
        )
        summary = candidate_coach.get_interview_summary(session_id)
        assert summary.questions_answered == 1
        assert summary.score_breakdown.interview_performance_score is not None
        assert summary.score_breakdown.is_preliminary is False
        assert summary.score_breakdown.assessment_status == "final"
        assert summary.is_complete is True
        assert "Final Readiness Assessment" in summary.status_message


