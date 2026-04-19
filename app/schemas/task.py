from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

TaskStatus = Literal["pending", "in_progress", "completed"]
TaskPriority = Literal["low", "medium", "high"]

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"
    tags: list[str] | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    tags: list[str] | None = None

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

class TaskListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[TaskOut]
    total: int
    page: int
    page_size: int
    total_pages: int