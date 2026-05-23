from fastapi import APIRouter, HTTPException

from app.schemas.tasks import TaskStatusResponse
from app.services.tasks.task_manager import get_task


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
def status(task_id: str) -> TaskStatusResponse:
    try:
        return get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found.") from exc
