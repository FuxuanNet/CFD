from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services._ids import make_id


def workspace_root() -> Path:
    root = Path(get_settings().WORKSPACE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    return root


def new_job_id() -> str:
    return make_id("job")


def job_dir(job_id: str) -> Path:
    path = workspace_root() / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def stage_dir(job_id: str, stage: str) -> Path:
    path = job_dir(job_id) / stage
    path.mkdir(parents=True, exist_ok=True)
    return path


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def workspace_api_path(path: Path) -> str:
    return f"workspace/{relative_path(path)}"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_job(job_id: str) -> None:
    path = workspace_root() / job_id
    if path.exists():
        shutil.rmtree(path)


def require_file(path: Path, message: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(message)
    return path

