from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import files_api, geometry_api, mesh_api, preprocess_api, projects_api, results_api, solver_api, tasks_api
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(geometry_api.router, prefix=settings.API_PREFIX)
app.include_router(projects_api.router, prefix=settings.API_PREFIX)
app.include_router(mesh_api.router, prefix=settings.API_PREFIX)
app.include_router(preprocess_api.router, prefix=settings.API_PREFIX)
app.include_router(solver_api.router, prefix=settings.API_PREFIX)
app.include_router(results_api.router, prefix=settings.API_PREFIX)
app.include_router(files_api.router, prefix=settings.API_PREFIX)
app.include_router(tasks_api.router, prefix=settings.API_PREFIX)


@app.get(f"{settings.API_PREFIX}/health")
def health_check() -> dict[str, str | bool]:
    return {
        "success": True,
        "app_name": settings.APP_NAME,
        "ccx_executable": settings.CCX_EXECUTABLE,
    }
