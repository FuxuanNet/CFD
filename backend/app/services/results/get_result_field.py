from app.core.workspace import require_file, workspace_api_path
from app.schemas.common import FileReference
from app.schemas.results import ResultFieldName, ResultFieldResponse
from app.services.cae_files import results_dir


def get_result_field(result_id: str, field: ResultFieldName) -> ResultFieldResponse:
    """Return the frontend display file for a requested result field.

    Input:
        result_id and field name: displacement or von_mises.

    Return:
        Placeholder VTP file reference for the selected cloud plot.

    This implementation returns the real generated surface VTP file reference.
    """

    result_path = results_dir(result_id)
    file_name = f"result_surface_{field}.vtp"
    file_path = require_file(result_path / file_name, f"Result field file not found: {file_name}")
    return ResultFieldResponse(
        message="Result field returned.",
        result_id=result_id,
        field=field,
        file=FileReference(name=file_name, path=workspace_api_path(file_path), description=f"Surface cloud plot for {field}."),
    )
