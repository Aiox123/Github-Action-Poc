"""FastAPI HTTP interface for the todo service."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from . import __version__
from .config import get_settings
from .repositories import JsonTodoRepository
from .services import TodoNotFoundError, TodoService


# ---- DTOs ---------------------------------------------------------------
class TodoOut(BaseModel):
    id: int
    title: str
    done: bool
    created_at: str
    completed_at: str | None = None


class CreateTodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


# ---- DI -----------------------------------------------------------------
def get_service() -> TodoService:
    settings = get_settings()
    return TodoService(JsonTodoRepository(settings.data_file))


# ---- app factory --------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(title="Todo API", version=__version__)

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {"status": "ok", "version": __version__}

    @app.get("/todos", response_model=list[TodoOut])
    def list_todos(service: TodoService = Depends(get_service)) -> list[TodoOut]:
        return [TodoOut(**t.to_dict()) for t in service.list()]

    @app.post("/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
    def create_todo(
        payload: CreateTodoIn,
        service: TodoService = Depends(get_service),
    ) -> TodoOut:
        try:
            item = service.add(payload.title)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return TodoOut(**item.to_dict())

    @app.post("/todos/{todo_id}/complete", response_model=TodoOut)
    def complete_todo(todo_id: int, service: TodoService = Depends(get_service)) -> TodoOut:
        try:
            item = service.complete(todo_id)
        except TodoNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return TodoOut(**item.to_dict())

    @app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_todo(todo_id: int, service: TodoService = Depends(get_service)) -> None:
        try:
            service.delete(todo_id)
        except TodoNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
