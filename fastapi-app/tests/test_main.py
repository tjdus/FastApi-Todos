import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app, save_todos, load_todos, TodoItem

client = TestClient(app)

def make_todo(
    id=1,
    title="Test",
    description="Test description",
    status="아직",
    completed=False,
    created_at=None,
    updated_at=None
):
    now = datetime.utcnow().isoformat()
    return TodoItem(
        id=id,
        title=title,
        description=description,
        status=status,
        completed=completed,
        created_at=created_at or now,
        updated_at=updated_at or now
    )

@pytest.fixture(autouse=True)
def setup_and_teardown():
    save_todos([])
    yield
    save_todos([])

def test_get_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_get_todos_with_items():
    todo = make_todo()
    save_todos([todo.dict()])
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Test"

def test_create_todo():
    todo = make_todo().dict()
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    assert response.json()["title"] == "Test"

def test_create_todo_invalid():
    # 필수 필드 누락
    todo = {"id": 1, "title": "Test"}
    response = client.post("/todos", json=todo)
    assert response.status_code == 422

def test_update_todo():
    todo = make_todo()
    save_todos([todo.dict()])
    updated_todo = make_todo(
        id=1,
        title="Updated",
        description="Updated description",
        status="진행중",
        completed=True
    ).dict()
    response = client.put("/todos/1", json=updated_todo)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"

def test_update_todo_not_found():
    updated_todo = make_todo(
        id=1,
        title="Updated",
        description="Updated description",
        status="진행중",
        completed=True
    ).dict()
    response = client.put("/todos/1", json=updated_todo)
    assert response.status_code == 404

def test_delete_todo():
    todo = make_todo()
    save_todos([todo.dict()])
    response = client.delete("/todos/1")
    assert response.status_code == 200
    assert response.json()["message"] == "To-Do item deleted"

def test_delete_todo_not_found():
    response = client.delete("/todos/1")
    assert response.status_code == 200
    assert response.json()["message"] == "To-Do item deleted"