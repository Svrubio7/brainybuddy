"""
Claude-powered extraction: convert document text into structured tasks and events.
"""

import json

import anthropic

from app.core.config import settings

EXTRACTION_PROMPT = """You are an academic document parser. Analyze the following document text and extract:

1. **Tasks**: assignments, exams, projects, readings with:
   - title, due_date (ISO 8601), estimated_hours, difficulty (1-5), task_type (assignment/exam/reading/project), description

2. **Events**: lectures, labs, office hours with:
   - title, day_of_week, start_time, end_time, recurrence (weekly/once)

3. **Confidence score** (0-1): how confident you are in the extractions.

Return ONLY valid JSON in this format:
{
  "tasks": [{"title": "...", "due_date": "...", "estimated_hours": ..., "difficulty": ..., "task_type": "...", "description": "..."}],
  "events": [{"title": "...", "day_of_week": "...", "start_time": "...", "end_time": "...", "recurrence": "..."}],
  "confidence": 0.85
}

Document text:
"""


async def extract_from_text(text: str) -> dict:
    """Use Claude to extract structured data from document text."""
    if not settings.ANTHROPIC_API_KEY:
        return {
            "tasks": [],
            "events": [],
            "confidence": 0,
            "error": "ANTHROPIC_API_KEY not configured",
        }

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Truncate very long texts
    truncated = text[:15000] if len(text) > 15000 else text

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": EXTRACTION_PROMPT + truncated}
        ],
    )

    response_text = response.content[0].text

    # Parse JSON from response
    try:
        # Try to find JSON in the response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
    except json.JSONDecodeError:
        pass

    return {"tasks": [], "events": [], "confidence": 0, "error": "Failed to parse response"}


async def extract_syllabus(text: str) -> dict:
    """Specialized extraction for syllabi — gets exam schedule, weekly topics, office hours."""
    if not settings.ANTHROPIC_API_KEY:
        return {"tasks": [], "events": [], "confidence": 0}

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = """Analyze this syllabus and extract ALL of the following:

1. **Exam dates**: midterms, finals, quizzes → as tasks with type "exam"
2. **Assignment deadlines**: homework, projects, papers → as tasks with type "assignment" or "project"
3. **Weekly schedule**: lecture times, lab times, office hours → as recurring events
4. **Key milestones**: paper drafts, project checkpoints → as tasks

Return valid JSON:
{
  "tasks": [{"title": "...", "due_date": "YYYY-MM-DDT23:59:00", "estimated_hours": ..., "difficulty": ..., "task_type": "exam|assignment|project|reading", "description": "..."}],
  "events": [{"title": "...", "day_of_week": "monday|tuesday|...", "start_time": "HH:MM", "end_time": "HH:MM", "recurrence": "weekly"}],
  "confidence": 0.85
}

Syllabus text:
""" + text[:15000]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = response.content[0].text
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(response_text[start:end])
    except json.JSONDecodeError:
        pass

    return {"tasks": [], "events": [], "confidence": 0}
