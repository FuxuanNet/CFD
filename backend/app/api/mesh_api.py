from fastapi import APIRouter

from app.api.error_handling import as_http_error
from app.schemas.mesh import MeshGenerateRequest, MeshResponse
from app.schemas.tasks import TaskStartResponse
from app.services.mesh.generate_mesh import generate_mesh
from app.services.tasks.task_manager import start_task

router = APIRouter(prefix="/mesh", tags=["mesh"])


@router.post("/generate", response_model=MeshResponse)
def generate(request: MeshGenerateRequest) -> MeshResponse:
    return as_http_error("mesh generation", lambda: generate_mesh(request))


@router.post("/tasks", response_model=TaskStartResponse)
def start_generate_task(request: MeshGenerateRequest) -> TaskStartResponse:
    return as_http_error("mesh task start", lambda: start_task(request.geometry_id, "mesh", lambda emit: generate_mesh(request, emit)))
