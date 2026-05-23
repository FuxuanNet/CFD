from app.core.workspace import read_json, require_file, workspace_api_path
from app.schemas.common import FileReference
from app.schemas.results import ResultSummaryResponse
from app.services.cae_files import results_dir


def get_result_summary(result_id: str) -> ResultSummaryResponse:
    """Return summary values for a solved result.

    Input:
        result_id.

    Return:
        Placeholder maximum displacement, maximum Von Mises stress, and result file paths.

    This implementation reads result_summary.json from the result workspace.
    """

    result_path = results_dir(result_id)
    summary_path = require_file(result_path / "result_summary.json", "Result summary not found.")
    summary = read_json(summary_path)
    return ResultSummaryResponse(
        message="Result summary returned.",
        result_id=result_id,
        max_displacement=float(summary.get("max_displacement", 0.0)),
        max_von_mises=float(summary.get("max_von_mises", 0.0)),
        warnings=[str(item) for item in summary.get("warnings", []) if str(item).strip()],
        files=[
            FileReference(name="result.vtu", path=workspace_api_path(result_path / "result.vtu"), description="Converted unstructured grid result."),
            FileReference(name="result_surface_displacement.vtp", path=workspace_api_path(result_path / "result_surface_displacement.vtp"), description="Displacement cloud plot surface."),
            FileReference(name="result_surface_von_mises.vtp", path=workspace_api_path(result_path / "result_surface_von_mises.vtp"), description="Von Mises cloud plot surface."),
            FileReference(name="result_summary.json", path=workspace_api_path(summary_path), description="Result maximum values."),
        ],
    )
