"""Socratic tutor service.

Implements a guided learning approach where instead of giving direct
answers, the tutor leads the student through the reasoning process
with calibrated hints.
"""

import logging
from typing import Any

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

# Hint level definitions
HINT_LEVELS = {
    "nudge": {
        "description": "Minimal hint — ask a guiding question to steer thinking",
        "instruction": (
            "Do NOT reveal the answer. Instead, ask a single Socratic question that "
            "guides the student toward discovering the answer themselves. Point them "
            "in the right direction with a question, not a statement."
        ),
    },
    "partial": {
        "description": "Partial hint — reveal part of the reasoning or a key concept",
        "instruction": (
            "Give the student a partial hint. Reveal one key concept or reasoning step "
            "that they need, but do NOT give the full answer. Explain the relevant "
            "principle and let them apply it. End with a follow-up question."
        ),
    },
    "full_explanation": {
        "description": "Full explanation — thorough walkthrough of the solution",
        "instruction": (
            "Provide a complete, step-by-step explanation of the answer. Be thorough "
            "but clear. After explaining, ask the student to restate the key insight "
            "in their own words to check understanding."
        ),
    },
}

SOCRATIC_SYSTEM_PROMPT = """You are a Socratic tutor for university students. Your goal is to help students learn by guiding their thinking, not by giving them answers directly.

Core principles:
1. Meet the student where they are — assess what they already know.
2. Ask questions that expose gaps in understanding.
3. Build on what the student knows to scaffold new understanding.
4. Encourage the student to reason through problems step by step.
5. Celebrate correct reasoning and gently redirect incorrect reasoning.

Hint level for this response: {hint_level}
Hint instructions: {hint_instruction}

{context_section}

Be warm, encouraging, and patient. Use analogies when helpful. Keep your response focused and not too long."""

EXPLAIN_SYSTEM_PROMPT = """You are an expert tutor who can explain concepts at different levels of complexity.

Explanation level: {level}

Level descriptions:
- "eli5": Explain like I'm 5. Use simple analogies, everyday language, no jargon. Make it fun and memorable.
- "undergrad": Explain for an undergraduate student. Use proper terminology, include key details, reference related concepts.
- "expert": Explain at an expert/graduate level. Be precise, include nuances, edge cases, formal definitions, and connections to broader theory.

Provide a clear, well-structured explanation at the requested level. Use examples when helpful."""


async def socratic_response(
    question: str,
    context: str | None = None,
    hint_level: str = "nudge",
    conversation_history: list[dict[str, str]] | None = None,
    course_name: str | None = None,
) -> dict[str, Any]:
    """Generate a Socratic tutoring response.

    Args:
        question: The student's question or current statement.
        context: Optional course material context for grounded responses.
        hint_level: One of 'nudge', 'partial', 'full_explanation'.
        conversation_history: Previous messages in the tutoring conversation.
        course_name: Optional course name for context.

    Returns:
        Dict with 'response', 'hint_level', 'follow_up_question'.
    """
    if hint_level not in HINT_LEVELS:
        hint_level = "nudge"

    hint_info = HINT_LEVELS[hint_level]

    # Build context section
    context_parts = []
    if course_name:
        context_parts.append(f"Course: {course_name}")
    if context:
        context_parts.append(f"Relevant material:\n{context[:4000]}")
    context_section = "\n".join(context_parts) if context_parts else ""

    system = SOCRATIC_SYSTEM_PROMPT.format(
        hint_level=hint_info["description"],
        hint_instruction=hint_info["instruction"],
        context_section=context_section,
    )

    # Build message list
    messages: list[dict[str, str]] = []
    if conversation_history:
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

    messages.append({"role": "user", "content": question})

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=messages,
        )

        response_text = response.content[0].text.strip()

        # Try to extract a follow-up question (last sentence ending with ?)
        follow_up = _extract_follow_up(response_text)

        logger.info("Socratic response generated at hint level: %s", hint_level)

        return {
            "response": response_text,
            "hint_level": hint_level,
            "follow_up_question": follow_up,
        }

    except anthropic.APIError as exc:
        logger.error("Anthropic API error in Socratic tutor: %s", exc)
        return {
            "response": (
                "I'm having trouble connecting right now. "
                "Let's try a different approach: can you tell me what you already "
                "know about this topic? That will help me guide you better."
            ),
            "hint_level": hint_level,
            "follow_up_question": "What do you already know about this?",
            "error": str(exc),
        }


async def explain_concept(
    concept: str,
    level: str = "undergrad",
    course_name: str | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """Explain a concept at a specified complexity level.

    Args:
        concept: The concept or topic to explain.
        level: One of 'eli5', 'undergrad', 'expert'.
        course_name: Optional course context.
        context: Optional relevant material.

    Returns:
        Dict with 'explanation', 'level', 'key_takeaways'.
    """
    valid_levels = {"eli5", "undergrad", "expert"}
    if level not in valid_levels:
        level = "undergrad"

    system = EXPLAIN_SYSTEM_PROMPT.format(level=level)

    user_message_parts = [f"Explain: {concept}"]
    if course_name:
        user_message_parts.append(f"(In the context of: {course_name})")
    if context:
        user_message_parts.append(f"\nRelevant context:\n{context[:4000]}")

    user_message = "\n".join(user_message_parts)

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        explanation = response.content[0].text.strip()

        return {
            "explanation": explanation,
            "level": level,
            "concept": concept,
        }

    except anthropic.APIError as exc:
        logger.error("Anthropic API error explaining concept: %s", exc)
        return {
            "explanation": f"Unable to generate explanation for '{concept}' at this time.",
            "level": level,
            "concept": concept,
            "error": str(exc),
        }


def _extract_follow_up(text: str) -> str | None:
    """Extract the last question from a response as a follow-up prompt."""
    sentences = text.replace("?", "?\n").split("\n")
    questions = [s.strip() for s in sentences if s.strip().endswith("?")]
    return questions[-1] if questions else None
