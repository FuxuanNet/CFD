from pathlib import Path

from app.core.workspace import stage_dir


def geometry_dir(job_id: str) -> Path:
    return stage_dir(job_id, "geometry")


def mesh_dir(job_id: str) -> Path:
    return stage_dir(job_id, "mesh")


def preprocess_dir(job_id: str) -> Path:
    return stage_dir(job_id, "preprocess")


def solver_dir(job_id: str) -> Path:
    return stage_dir(job_id, "solver")


def results_dir(job_id: str) -> Path:
    return stage_dir(job_id, "results")

