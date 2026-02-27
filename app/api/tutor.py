"""API routes for the Premium Tutor features.

Includes flashcard generation and review, practice exam generation and grading,
Socratic tutoring, and multi-level concept explanations.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


# ---- Request / Response schemas ----


class FlashcardGenerateRequest(BaseModel):
    material_text: str = Field(..., min_length=10)
    count: int = Field(default=10, ge=1, le=50)
    course_name: str | None = None
    topic: str | None = None


class FlashcardItem(BaseModel):
    front: str
    back: str


class FlashcardGradeRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5)


class FlashcardGradeResponse(BaseModel):
    card_id: int
    easiness: float
    interval_days: int
    repetitions: int
    next_review: str
    quality: int


class ExamGenerateRequest(BaseModel):
    course_id: int | None = None
    topics: list[str] = Field(..., min_length=1)
    question_types: list[str] | None = Field(default=None)
    num_questions: int = Field(default=10, ge=1, le=50)
    difficulty: str = Field(default="medium")
    course_context: str | None = None


class ExamGradeRequest(BaseModel):
    exam_data: dict[str, Any]
    answers: dict[int, str]


class SocraticRequest(BaseModel):
    question: str = Field(..., min_length=1)
    context: str | None = None
    hint_level: str = Field(default="nudge")
    conversation_history: list[dict[str, str]] | None = None
    course_name: str | None = None


class SocraticResponse(BaseModel):
    response: str
    hint_level: str
    follow_up_question: str | None = None


class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=1)
    level: str = Field(default="undergrad")
    course_name: str | None = None
    context: str | None = None


class ExplainResponse(BaseModel):
    explanation: str
    level: str
    concept: str


# ---- Flashcards ----


@router.post("/flashcards/generate", response_model=list[FlashcardItem])
async def generate_flashcards_endpoint(
    data: FlashcardGenerateRequest,
    user: CurrentUser,
    session: DbSession,
):
    """Generate flashcards from study material using Claude."""
    from app.services.tutor.flashcards import generate_flashcards

    cards = await generate_flashcards(
        material_text=data.material_text,
        count=data.count,
        course_name=data.course_name,
        topic=data.topic,
    )

    if not cards:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate flashcards. Please try again.",
        )

    return [FlashcardItem(front=c["front"], back=c["back"]) for c in cards]


@router.get("/flashcards")
async def list_flashcard_decks(
    user: CurrentUser,
    session: DbSession,
    course_id: int | None = Query(default=None),
):
    """List flashcard decks for the current user."""
    from sqlalchemy import text

    query = "SELECT * FROM flashcards WHERE user_id = :user_id"
    params: dict[str, Any] = {"user_id": user.id}

    if course_id:
        query += " AND course_id = :course_id"
        params["course_id"] = course_id

    query += " ORDER BY next_review ASC NULLS FIRST"

    try:
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "front": row.front,
                "back": row.back,
                "easiness": row.easiness,
                "interval_days": row.interval_days,
                "repetitions": row.repetitions,
                "next_review": row.next_review.isoformat() if row.next_review else None,
                "last_reviewed": row.last_reviewed.isoformat() if row.last_reviewed else None,
            }
            for row in rows
        ]
    except Exception:
        # Table may not exist yet; return empty
        return []


@router.post("/flashcards/{card_id}/grade", response_model=FlashcardGradeResponse)
async def grade_flashcard_endpoint(
    card_id: int,
    data: FlashcardGradeRequest,
    user: CurrentUser,
    session: DbSession,
):
    """Grade a flashcard review using SM-2 spaced repetition."""
    from app.services.tutor.flashcards import grade_flashcard

    try:
        result = await grade_flashcard(
            card_id=card_id,
            quality=data.quality,
            session=session,
        )
        return FlashcardGradeResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Grading failed: {exc}")


# ---- Practice Exams ----


@router.post("/exams/generate")
async def generate_exam_endpoint(
    data: ExamGenerateRequest,
    user: CurrentUser,
    session: DbSession,
):
    """Generate a practice exam using Claude."""
    from app.services.tutor.practice_exams import generate_practice_exam

    exam = await generate_practice_exam(
        course_id=data.course_id,
        topics=data.topics,
        question_types=data.question_types,
        num_questions=data.num_questions,
        difficulty=data.difficulty,
        course_context=data.course_context,
    )

    if not exam.get("questions"):
        raise HTTPException(
            status_code=500,
            detail=exam.get("error", "Failed to generate exam."),
        )

    return exam


@router.post("/exams/{exam_id}/grade")
async def grade_exam_endpoint(
    exam_id: int,
    data: ExamGradeRequest,
    user: CurrentUser,
    session: DbSession,
):
    """Grade a practice exam's answers using Claude."""
    from app.services.tutor.practice_exams import grade_exam

    result = await grade_exam(
        exam_id=exam_id,
        exam_data=data.exam_data,
        answers=data.answers,
    )

    return result


# ---- Socratic Tutor ----


@router.post("/socratic", response_model=SocraticResponse)
async def socratic_question_endpoint(
    data: SocraticRequest,
    user: CurrentUser,
    session: DbSession,
):
    """Ask a Socratic question and receive guided tutoring."""
    from app.services.tutor.socratic import socratic_response

    result = await socratic_response(
        question=data.question,
        context=data.context,
        hint_level=data.hint_level,
        conversation_history=data.conversation_history,
        course_name=data.course_name,
    )

    return SocraticResponse(
        response=result["response"],
        hint_level=result["hint_level"],
        follow_up_question=result.get("follow_up_question"),
    )


# ---- Multi-level Explanation ----


@router.post("/explain", response_model=ExplainResponse)
async def explain_concept_endpoint(
    data: ExplainRequest,
    user: CurrentUser,
    session: DbSession,
):
    """Explain a concept at different levels (ELI5 / undergrad / expert)."""
    from app.services.tutor.socratic import explain_concept

    result = await explain_concept(
        concept=data.concept,
        level=data.level,
        course_name=data.course_name,
        context=data.context,
    )

    return ExplainResponse(
        explanation=result["explanation"],
        level=result["level"],
        concept=result["concept"],
    )
