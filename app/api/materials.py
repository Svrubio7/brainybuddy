from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.deps import CurrentUser, DbSession
from app.models.material import ExtractionStatus, Material
from app.schemas.material import ExtractionConfirm, ExtractionResult, MaterialResponse
from app.services.ingestion.extractor import extract_from_text, extract_syllabus
from app.services.ingestion.parser import extract_text

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.post("/upload", response_model=MaterialResponse, status_code=201)
async def upload_material(
    user: CurrentUser,
    session: DbSession,
    file: UploadFile = File(...),
    course_id: int | None = Form(None),
):
    contents = await file.read()

    material = Material(
        user_id=user.id,
        course_id=course_id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "",
        file_size=len(contents),
        extraction_status=ExtractionStatus.PROCESSING,
    )
    session.add(material)
    await session.flush()

    # Extract text
    text = await extract_text(contents, file.content_type or "")
    material.extracted_text = text
    material.extraction_status = ExtractionStatus.COMPLETED if text else ExtractionStatus.FAILED
    await session.commit()
    await session.refresh(material)

    return material


@router.post("/extract/{material_id}", response_model=ExtractionResult)
async def extract_material(material_id: int, user: CurrentUser, session: DbSession):
    from sqlmodel import select

    result = await session.execute(
        select(Material).where(Material.id == material_id, Material.user_id == user.id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if not material.extracted_text:
        raise HTTPException(status_code=400, detail="No text extracted from this material")

    # Use Claude to extract structured data
    extracted = await extract_from_text(material.extracted_text)

    return ExtractionResult(
        material_id=material.id,
        extracted_tasks=extracted.get("tasks", []),
        extracted_events=extracted.get("events", []),
        confidence=extracted.get("confidence", 0),
        raw_text_preview=material.extracted_text[:500],
    )


@router.post("/extract-syllabus/{material_id}", response_model=ExtractionResult)
async def extract_syllabus_endpoint(material_id: int, user: CurrentUser, session: DbSession):
    from sqlmodel import select

    result = await session.execute(
        select(Material).where(Material.id == material_id, Material.user_id == user.id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    extracted = await extract_syllabus(material.extracted_text)

    return ExtractionResult(
        material_id=material.id,
        extracted_tasks=extracted.get("tasks", []),
        extracted_events=extracted.get("events", []),
        confidence=extracted.get("confidence", 0),
        raw_text_preview=material.extracted_text[:500],
    )


@router.post("/confirm-extraction")
async def confirm_extraction(data: ExtractionConfirm, user: CurrentUser, session: DbSession):
    """Create tasks from confirmed extraction results."""
    from app.models.task import Task

    created_tasks = []
    for task_data in data.tasks_to_create:
        task = Task(
            user_id=user.id,
            title=task_data.get("title", "Untitled"),
            due_date=task_data.get("due_date"),
            estimated_hours=task_data.get("estimated_hours"),
            difficulty=task_data.get("difficulty", 3),
            task_type=task_data.get("task_type", "assignment"),
            description=task_data.get("description", ""),
        )
        session.add(task)
        created_tasks.append(task_data.get("title"))

    await session.commit()
    return {"created": len(created_tasks), "task_titles": created_tasks}


@router.get("", response_model=list[MaterialResponse])
async def list_materials(user: CurrentUser, session: DbSession):
    from sqlmodel import select

    result = await session.execute(
        select(Material).where(Material.user_id == user.id).order_by(Material.created_at.desc())
    )
    return list(result.scalars().all())
