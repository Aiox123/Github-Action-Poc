"""Integration tests for the FastAPI HTTP layer."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from todo.api import create_app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("TODO_DATA_FILE", str(tmp_path / "todos.json"))
    return TestClient(create_app())


def test_healthz(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_create_and_list(client: TestClient) -> None:
    res = client.post("/todos", json={"title": "write docs"})
    assert res.status_code == 201
    created = res.json()
    assert created["id"] == 1
    assert created["title"] == "write docs"
    assert created["done"] is False

    res = client.get("/todos")
    assert res.status_code == 200
    assert [t["title"] for t in res.json()] == ["write docs"]


def test_create_rejects_empty_title(client: TestClient) -> None:
    res = client.post("/todos", json={"title": ""})
    assert res.status_code == 422  # pydantic validation


def test_complete_then_delete(client: TestClient) -> None:
    client.post("/todos", json={"title": "a"})

    res = client.post("/todos/1/complete")
    assert res.status_code == 200
    assert res.json()["done"] is True

    res = client.delete("/todos/1")
    assert res.status_code == 204

    res = client.get("/todos")
    assert res.json() == []


def test_complete_unknown_returns_404(client: TestClient) -> None:
    res = client.post("/todos/999/complete")
    assert res.status_code == 404


def test_delete_unknown_returns_404(client: TestClient) -> None:
    res = client.delete("/todos/999")
    assert res.status_code == 404
