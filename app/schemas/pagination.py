from pydantic import BaseModel

from app.schemas.task import TaskResponse


class PaginatedTaskResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    offset: int
    limit: int
