from datetime import datetime

from pydantic import BaseModel


class MaterialResponse(BaseModel):
    id: int
    user_id: int
    course_id: int | None
    filename: str
    content_type: str
    file_size: int
    extraction_status: str
    created_at: datetime


class ExtractionResult(BaseModel):
    material_id: int
    extracted_tasks: list[dict]
    extracted_events: list[dict]
    confidence: float
    raw_text_preview: str


class ExtractionConfirm(BaseModel):
    material_id: int
    tasks_to_create: list[dict]
    events_to_create: list[dict] = []
