import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient):
    response = await client.post("/api/tasks", json={
        "title": "Lab Report",
        "due_date": "2026-03-15T23:59:00",
        "estimated_hours": 3.0,
        "difficulty": 4,
        "priority": "high",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Lab Report"
    assert data["difficulty"] == 4
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient):
    # Create two tasks
    await client.post("/api/tasks", json={
        "title": "Task 1",
        "due_date": "2026-03-10T23:59:00",
    })
    await client.post("/api/tasks", json={
        "title": "Task 2",
        "due_date": "2026-03-12T23:59:00",
    })
    response = await client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 2
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    create = await client.post("/api/tasks", json={
        "title": "Original",
        "due_date": "2026-03-15T23:59:00",
    })
    task_id = create.json()["id"]

    response = await client.patch(f"/api/tasks/{task_id}", json={
        "title": "Updated",
        "difficulty": 5,
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["difficulty"] == 5


@pytest.mark.asyncio
async def test_complete_task(client: AsyncClient):
    create = await client.post("/api/tasks", json={
        "title": "To Complete",
        "due_date": "2026-03-15T23:59:00",
    })
    task_id = create.json()["id"]

    response = await client.post(f"/api/tasks/{task_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    create = await client.post("/api/tasks", json={
        "title": "To Delete",
        "due_date": "2026-03-15T23:59:00",
    })
    task_id = create.json()["id"]

    response = await client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204

    get = await client.get(f"/api/tasks/{task_id}")
    assert get.status_code == 404
