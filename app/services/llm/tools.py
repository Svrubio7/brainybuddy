"""LLM tool schemas for Claude tool-calling."""

TOOLS = [
    {
        "name": "create_task",
        "description": "Create a new study task for the student. Extract title, due date, estimated hours, difficulty, and other details from the conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "due_date": {
                    "type": "string",
                    "description": "Due date in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                },
                "estimated_hours": {
                    "type": "number",
                    "description": "Estimated hours to complete",
                },
                "difficulty": {
                    "type": "integer",
                    "description": "Difficulty 1-5",
                    "minimum": 1,
                    "maximum": 5,
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                },
                "task_type": {
                    "type": "string",
                    "enum": ["assignment", "exam", "reading", "project", "other"],
                },
                "focus_load": {
                    "type": "string",
                    "enum": ["light", "medium", "deep"],
                },
                "description": {"type": "string"},
            },
            "required": ["title", "due_date"],
        },
    },
    {
        "name": "update_task",
        "description": "Update an existing task's fields.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to update"},
                "title": {"type": "string"},
                "due_date": {"type": "string"},
                "estimated_hours": {"type": "number"},
                "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "set_constraint",
        "description": "Set a scheduling constraint or rule for the student.",
        "input_schema": {
            "type": "object",
            "properties": {
                "constraint_type": {
                    "type": "string",
                    "enum": [
                        "daily_max_hours",
                        "break_after_minutes",
                        "preferred_start_hour",
                        "preferred_end_hour",
                        "sleep_start_hour",
                        "sleep_end_hour",
                    ],
                },
                "value": {"type": "number", "description": "The value for the constraint"},
            },
            "required": ["constraint_type", "value"],
        },
    },
    {
        "name": "trigger_replan",
        "description": "Trigger a replan of the study schedule. Use when the student wants to regenerate their plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why the replan is needed",
                },
            },
            "required": ["reason"],
        },
    },
    {
        "name": "mark_done",
        "description": "Mark a task as completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to mark done"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "cant_study_today",
        "description": "Student can't study today. Mark today as unavailable and trigger replan to reschedule blocks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Optional reason"},
            },
        },
    },
]
