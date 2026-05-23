from pydantic import BaseModel, Field


class FileReference(BaseModel):
    """Reference to a file produced or consumed by the CAE pipeline."""

    name: str = Field(..., description="Logical file name.")
    path: str = Field(..., description="Workspace-relative file path.")
    description: str | None = Field(default=None, description="Human readable purpose.")


class ApiMessage(BaseModel):
    success: bool = True
    message: str

