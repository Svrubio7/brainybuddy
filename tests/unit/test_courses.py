import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_course_crud(client: AsyncClient):
    # Create
    response = await client.post("/api/courses", json={
        "name": "Algorithms",
        "code": "CS301",
        "color": "#FF5733",
    })
    assert response.status_code == 201
    course = response.json()
    assert course["name"] == "Algorithms"
    course_id = course["id"]

    # List
    response = await client.get("/api/courses")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # Update
    response = await client.patch(f"/api/courses/{course_id}", json={"name": "Advanced Algorithms"})
    assert response.status_code == 200
    assert response.json()["name"] == "Advanced Algorithms"

    # Delete
    response = await client.delete(f"/api/courses/{course_id}")
    assert response.status_code == 204
