"""Practice exam builder and grader.

Uses Claude to generate practice exams with multiple question types
(MCQ, short_answer, essay) and provides detailed grading feedback.
"""

import json
import logging
from typing import Any

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

EXAM_GENERATION_SYSTEM = """You are an expert exam creator for university-level courses. Generate practice exam questions that effectively test student understanding.

Question types:
- "mcq": Multiple choice with 4 options (A, B, C, D). Include the correct answer key.
- "short_answer": Requires a 1-3 sentence answer. Include a model answer.
- "essay": Requires a paragraph-length response. Include key points that should be covered.

Return ONLY valid JSON — no markdown, no explanation.

JSON format:
{
  "title": "Practice Exam: <topic>",
  "questions": [
    {
      "id": 1,
      "type": "mcq",
      "question": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "B",
      "explanation": "...",
      "points": 2
    },
    {
      "id": 2,
      "type": "short_answer",
      "question": "...",
      "model_answer": "...",
      "key_points": ["point1", "point2"],
      "points": 5
    },
    {
      "id": 3,
      "type": "essay",
      "question": "...",
      "key_points": ["point1", "point2", "point3"],
      "model_answer": "...",
      "points": 10
    }
  ],
  "total_points": 17,
  "time_estimate_minutes": 30
}"""

GRADING_SYSTEM = """You are an expert exam grader. Grade the student's answers against the model answers and key points.

For each answer:
- Award points based on accuracy, completeness, and understanding.
- Provide specific, constructive feedback.
- Note what was correct and what was missing or incorrect.

Return ONLY valid JSON — no markdown, no explanation.

JSON format:
{
  "results": [
    {
      "question_id": 1,
      "points_awarded": 2,
      "max_points": 2,
      "feedback": "Correct! ..."
    }
  ],
  "total_score": 15,
  "total_possible": 17,
  "percentage": 88.2,
  "overall_feedback": "Strong performance overall. ..."
}"""


async def generate_practice_exam(
    course_id: int | None,
    topics: list[str],
    question_types: list[str] | None = None,
    num_questions: int = 10,
    difficulty: str = "medium",
    course_context: str | None = None,
) -> dict[str, Any]:
    """Generate a practice exam using Claude.

    Args:
        course_id: Associated course ID (for metadata).
        topics: List of topics to cover.
        question_types: List of allowed types ('mcq', 'short_answer', 'essay').
                       Defaults to all types.
        num_questions: Total number of questions to generate.
        difficulty: 'easy', 'medium', or 'hard'.
        course_context: Optional additional context about the course material.

    Returns:
        Exam dict with title, questions, total_points, time_estimate_minutes.
    """
    if question_types is None:
        question_types = ["mcq", "short_answer", "essay"]

    # Validate question types
    valid_types = {"mcq", "short_answer", "essay"}
    question_types = [qt for qt in question_types if qt in valid_types]
    if not question_types:
        question_types = ["mcq"]

    topics_str = ", ".join(topics)
    types_str = ", ".join(question_types)

    context_section = ""
    if course_context:
        context_section = f"\n\nCourse material context:\n{course_context[:6000]}"

    user_message = (
        f"Generate a practice exam with the following parameters:\n"
        f"- Topics: {topics_str}\n"
        f"- Number of questions: {num_questions}\n"
        f"- Question types: {types_str}\n"
        f"- Difficulty: {difficulty}\n"
        f"{context_section}"
    )

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=EXAM_GENERATION_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()
        exam = json.loads(raw_text)

        # Add metadata
        exam["course_id"] = course_id
        exam["topics"] = topics
        exam["difficulty"] = difficulty

        logger.info(
            "Generated practice exam with %d questions on topics: %s",
            len(exam.get("questions", [])),
            topics_str,
        )
        return exam

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse exam JSON from Claude: %s", exc)
        return {
            "title": "Exam Generation Failed",
            "questions": [],
            "total_points": 0,
            "time_estimate_minutes": 0,
            "error": "Failed to parse generated exam",
        }
    except anthropic.APIError as exc:
        logger.error("Anthropic API error generating exam: %s", exc)
        return {
            "title": "Exam Generation Failed",
            "questions": [],
            "total_points": 0,
            "time_estimate_minutes": 0,
            "error": str(exc),
        }


async def grade_exam(
    exam_id: int | None,
    exam_data: dict[str, Any],
    answers: dict[int, str],
) -> dict[str, Any]:
    """Grade a student's answers against the exam.

    Args:
        exam_id: Optional stored exam ID.
        exam_data: The full exam dict (with questions and model answers).
        answers: Dict mapping question_id -> student's answer text.

    Returns:
        Grading results with per-question feedback and overall score.
    """
    questions = exam_data.get("questions", [])
    if not questions:
        return {
            "exam_id": exam_id,
            "results": [],
            "total_score": 0,
            "total_possible": 0,
            "percentage": 0.0,
            "overall_feedback": "No questions in the exam.",
        }

    # Build grading context
    grading_items = []
    for q in questions:
        q_id = q.get("id", 0)
        student_answer = answers.get(q_id, "[No answer provided]")
        grading_items.append({
            "question_id": q_id,
            "type": q.get("type"),
            "question": q.get("question"),
            "correct_answer": q.get("correct_answer") or q.get("model_answer", ""),
            "key_points": q.get("key_points", []),
            "points": q.get("points", 1),
            "student_answer": student_answer,
        })

    user_message = (
        f"Grade the following exam answers:\n\n"
        f"{json.dumps(grading_items, indent=2)}"
    )

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=GRADING_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()
        grading_result = json.loads(raw_text)

        grading_result["exam_id"] = exam_id
        logger.info(
            "Graded exam %s: %s/%s (%.1f%%)",
            exam_id,
            grading_result.get("total_score"),
            grading_result.get("total_possible"),
            grading_result.get("percentage", 0),
        )
        return grading_result

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse grading JSON from Claude: %s", exc)
        return _fallback_grading(exam_id, questions, answers)
    except anthropic.APIError as exc:
        logger.error("Anthropic API error grading exam: %s", exc)
        return _fallback_grading(exam_id, questions, answers)


def _fallback_grading(
    exam_id: int | None,
    questions: list[dict],
    answers: dict[int, str],
) -> dict[str, Any]:
    """Simple fallback grading for MCQ questions when Claude is unavailable."""
    results = []
    total_score = 0
    total_possible = 0

    for q in questions:
        q_id = q.get("id", 0)
        points = q.get("points", 1)
        total_possible += points
        student_answer = answers.get(q_id, "")

        if q.get("type") == "mcq" and q.get("correct_answer"):
            is_correct = student_answer.strip().upper() == q["correct_answer"].strip().upper()
            awarded = points if is_correct else 0
            total_score += awarded
            results.append({
                "question_id": q_id,
                "points_awarded": awarded,
                "max_points": points,
                "feedback": "Correct!" if is_correct else f"Incorrect. The correct answer is {q['correct_answer']}.",
            })
        else:
            results.append({
                "question_id": q_id,
                "points_awarded": 0,
                "max_points": points,
                "feedback": "Manual grading required (AI grading unavailable).",
            })

    percentage = (total_score / total_possible * 100) if total_possible > 0 else 0.0

    return {
        "exam_id": exam_id,
        "results": results,
        "total_score": total_score,
        "total_possible": total_possible,
        "percentage": round(percentage, 1),
        "overall_feedback": "Partial grading only (MCQ auto-graded, others need manual review).",
    }
