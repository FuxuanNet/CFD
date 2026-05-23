from app.core.workspace import workspace_api_path, write_json
from app.schemas.common import FileReference
from app.schemas.preprocess import MaterialRequest, MaterialResponse
from app.services.cae_files import preprocess_dir


def set_material(request: MaterialRequest) -> MaterialResponse:
    """Store material settings for the current mesh.

    Input:
        mesh_id, material name, elastic modulus, and Poisson ratio.

    Return:
        Material ID plus placeholder material JSON path.

    This implementation persists material configuration for INP generation.
    """

    material_id = request.mesh_id
    material_path = preprocess_dir(request.mesh_id) / "material.json"
    write_json(
        material_path,
        {
            "material_id": material_id,
            "mesh_id": request.mesh_id,
            "name": request.name,
            "elastic_modulus": request.elastic_modulus,
            "poisson_ratio": request.poisson_ratio,
            "unit": "MPa",
        },
    )

    return MaterialResponse(
        message="Material saved.",
        material_id=material_id,
        mesh_id=request.mesh_id,
        files=[
            FileReference(name="material.json", path=workspace_api_path(material_path), description="Material parameters."),
        ],
    )
