from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Lock
from typing import Any, Callable

from app.schemas.tasks import LogChannel, TaskLogEntry, TaskStartResponse, TaskStatusResponse
from app.services._ids import make_id


TaskFn = Callable[[Callable[[str, int, str, LogChannel], None]], Any]

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cae-task")
_lock = Lock()
_tasks: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _snapshot(task_id: str) -> TaskStatusResponse:
    task = _tasks[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        job_id=task["job_id"],
        status=task["status"],
        progress=task["progress"],
        phase=task["phase"],
        message=task["message"],
        logs=[TaskLogEntry(**entry) for entry in task["logs"]],
        result=task.get("result"),
        error=task.get("error"),
    )


def _append_log(task: dict[str, Any], phase: str, progress: int, message: str, channel: LogChannel) -> None:
    task["sequence"] += 1
    task["phase"] = phase
    task["progress"] = max(0, min(100, int(progress)))
    task["message"] = message
    task["logs"].append(
        {
            "sequence": task["sequence"],
            "channel": channel,
            "phase": phase,
            "message": message,
            "time": _now(),
        }
    )


def start_task(job_id: str, task_type: str, fn: TaskFn) -> TaskStartResponse:
    task_id = make_id("task")
    with _lock:
        _tasks[task_id] = {
            "job_id": job_id,
            "task_type": task_type,
            "status": "queued",
            "progress": 0,
            "phase": "queued",
            "message": "Task queued.",
            "logs": [],
            "sequence": 0,
            "result": None,
            "error": None,
        }

    def emit(phase: str, progress: int, message: str, channel: LogChannel = "message") -> None:
        with _lock:
            task = _tasks.get(task_id)
            if not task:
                return
            _append_log(task, phase, progress, message, channel)

    def runner() -> None:
        with _lock:
            task = _tasks[task_id]
            task["status"] = "running"
            _append_log(task, "running", 1, f"{task_type} task started.", "message")
        try:
            result = fn(emit)
            with _lock:
                task = _tasks[task_id]
                task["status"] = "completed"
                task["result"] = result.model_dump() if hasattr(result, "model_dump") else result
                _append_log(task, "completed", 100, f"{task_type} task completed.", "message")
        except Exception as exc:
            with _lock:
                task = _tasks[task_id]
                task["status"] = "failed"
                task["error"] = str(exc)
                _append_log(task, "failed", task["progress"], str(exc), "error")

    _executor.submit(runner)
    with _lock:
        return TaskStartResponse(
            task_id=task_id,
            job_id=job_id,
            status=_tasks[task_id]["status"],
            progress=_tasks[task_id]["progress"],
            phase=_tasks[task_id]["phase"],
            message=_tasks[task_id]["message"],
        )


def get_task(task_id: str) -> TaskStatusResponse:
    with _lock:
        if task_id not in _tasks:
            raise KeyError(task_id)
        return _snapshot(task_id)
