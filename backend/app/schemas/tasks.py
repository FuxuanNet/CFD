from typing import Any, Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["queued", "running", "completed", "failed"]
LogChannel = Literal["message", "mesh", "solver", "error"]


class TaskLogEntry(BaseModel):
    sequence: int
    channel: LogChannel
    phase: str
    message: str
    time: str


class TaskStartResponse(BaseModel):
    success: bool = True
    task_id: str
    job_id: str
    status: TaskStatus
    progress: int = 0
    phase: str = "queued"
    message: str = "Task queued."


class TaskStatusResponse(BaseModel):
    success: bool = True
    task_id: str
    job_id: str
    status: TaskStatus
    progress: int = Field(default=0, ge=0, le=100)
    phase: str
    message: str
    logs: list[TaskLogEntry]
    result: dict[str, Any] | None = None
    error: str | None = None
