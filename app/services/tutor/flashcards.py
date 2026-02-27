"""Flashcard generator and SM-2 spaced repetition grading.

Uses Claude to generate high-quality flashcards from study material,
and implements the SM-2 algorithm for adaptive review scheduling.
"""

import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import anthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

FLASHCARD_SYSTEM_PROMPT = """You are an expert flashcard creator for students. Given study material, create high-quality flashcards that test understanding, not just memorization.

Rules:
- Each flashcard has a "front" (question/prompt) and "back" (answer).
- Questions should test conceptual understanding, application, and analysis.
- Vary question types: definitions, comparisons, cause-effect, application scenarios.
- Keep answers concise but complete.
- Avoid trivial or overly broad questions.
- Return ONLY valid JSON — no markdown, no explanation.

Return a JSON array of objects with "front" and "back" keys."""

GRADE_FLASHCARD_PROMPT = """Based on the student's response quality, provide a brief explanation of the correct answer and what to focus on.

Flashcard front: {front}
Flashcard back (correct answer): {back}
Student's quality rating: {quality}/5

Provide a short (1-2 sentence) review note."""


async def generate_flashcards(
    material_text: str,
    count: int = 10,
    course_name: str | None = None,
    topic: str | None = None,
) -> list[dict[str, str]]:
    """Generate flashcards from study material using Claude.

    Args:
        material_text: The source text to generate flashcards from.
        count: Number of flashcards to generate.
        course_name: Optional course name for context.
        topic: Optional topic focus.

    Returns:
        List of dicts with 'front' and 'back' keys.
    """
    context_parts = []
    if course_name:
        context_parts.append(f"Course: {course_name}")
    if topic:
        context_parts.append(f"Topic focus: {topic}")
    context_header = "\n".join(context_parts) + "\n\n" if context_parts else ""

    user_message = (
        f"{context_header}"
        f"Create exactly {count} flashcards from the following material:\n\n"
        f"{material_text[:8000]}"  # Limit input to avoid token overflow
    )

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=FLASHCARD_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()

        # Parse the JSON response
        flashcards = json.loads(raw_text)

        # Validate structure
        validated: list[dict[str, str]] = []
        for card in flashcards:
            if isinstance(card, dict) and "front" in card and "back" in card:
                validated.append({
                    "front": str(card["front"]),
                    "back": str(card["back"]),
                })

        logger.info("Generated %d flashcards (requested %d)", len(validated), count)
        return validated

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse flashcard JSON from Claude: %s", exc)
        return []
    except anthropic.APIError as exc:
        logger.error("Anthropic API error generating flashcards: %s", exc)
        return []


async def grade_flashcard(
    card_id: int,
    quality: int,
    session: AsyncSession,
) -> dict[str, Any]:
    """Update SM-2 spaced repetition parameters for a flashcard.

    Args:
        card_id: The flashcard ID.
        quality: Grade quality 0-5 (0=complete blackout, 5=perfect).
        session: Database session.

    Returns:
        Updated SM-2 parameters: easiness, interval, repetitions, next_review.
    """
    quality = max(0, min(5, quality))

    # Fetch current SM-2 params from the database
    try:
        result = await session.execute(
            text("""
                SELECT easiness, interval_days, repetitions, front, back
                FROM flashcards
                WHERE id = :card_id
            """),
            {"card_id": card_id},
        )
        row = result.fetchone()
    except Exception as exc:
        logger.error("Failed to fetch flashcard %d: %s", card_id, exc)
        raise

    if row is None:
        raise ValueError(f"Flashcard {card_id} not found")

    easiness = float(row.easiness)
    interval = int(row.interval_days)
    repetitions = int(row.repetitions)

    # SM-2 algorithm
    new_easiness, new_interval, new_repetitions = _sm2_update(
        easiness, interval, repetitions, quality
    )

    next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)

    # Persist updated params
    try:
        await session.execute(
            text("""
                UPDATE flashcards
                SET easiness = :easiness,
                    interval_days = :interval,
                    repetitions = :repetitions,
                    next_review = :next_review,
                    last_reviewed = :now
                WHERE id = :card_id
            """),
            {
                "easiness": new_easiness,
                "interval": new_interval,
                "repetitions": new_repetitions,
                "next_review": next_review,
                "now": datetime.now(timezone.utc),
                "card_id": card_id,
            },
        )
        await session.commit()
    except Exception as exc:
        logger.error("Failed to update flashcard %d SM-2 params: %s", card_id, exc)
        raise

    return {
        "card_id": card_id,
        "easiness": round(new_easiness, 2),
        "interval_days": new_interval,
        "repetitions": new_repetitions,
        "next_review": next_review.isoformat(),
        "quality": quality,
    }


def _sm2_update(
    easiness: float,
    interval: int,
    repetitions: int,
    quality: int,
) -> tuple[float, int, int]:
    """Apply the SM-2 spaced repetition algorithm.

    Args:
        easiness: Current easiness factor (>= 1.3).
        interval: Current inter-repetition interval in days.
        repetitions: Number of consecutive correct reviews.
        quality: Response quality (0-5).

    Returns:
        Tuple of (new_easiness, new_interval, new_repetitions).
    """
    # Update easiness factor
    new_easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_easiness = max(1.3, new_easiness)

    if quality < 3:
        # Reset on failure
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = max(1, round(interval * new_easiness))

    return new_easiness, new_interval, new_repetitions
