from fastapi import APIRouter

from app.api.error_handling import as_http_error
from app.schemas.solver import SolverPluginInfo, SolverPluginListResponse, SolverRunRequest, SolverRunResponse
from app.schemas.tasks import TaskStartResponse
from app.services.structural_plugins.manager import get_structural_solver_manager
from app.services.tasks.task_manager import start_task

router = APIRouter(prefix="/solver", tags=["solver"])


@router.get("/plugins", response_model=SolverPluginListResponse)
def list_solver_plugins() -> SolverPluginListResponse:
    def _list() -> SolverPluginListResponse:
        manager = get_structural_solver_manager()
        return SolverPluginListResponse(
            plugins=[
                SolverPluginInfo(
                    id=record.manifest.id,
                    name=record.manifest.name,
                    version=record.manifest.version,
                )
                for record in manager.list_plugins()
            ]
        )

    return as_http_error("solver plugin list", _list)


@router.post("/run", response_model=SolverRunResponse)
def run(request: SolverRunRequest) -> SolverRunResponse:
    return as_http_error(
        "solver run",
        lambda: get_structural_solver_manager().create_plugin(request.solver_plugin_id).solve(request),
    )


@router.post("/tasks", response_model=TaskStartResponse)
def start_solver_task(request: SolverRunRequest) -> TaskStartResponse:
    return as_http_error(
        "solver task start",
        lambda: start_task(
            request.mesh_id,
            "solver",
            lambda emit: get_structural_solver_manager().create_plugin(request.solver_plugin_id).solve(request, emit),
        ),
    )
