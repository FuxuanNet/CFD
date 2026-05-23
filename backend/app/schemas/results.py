from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import FileReference


ResultFieldName = Literal["displacement", "von_mises"]


class ResultSummaryResponse(BaseModel):
    success: bool = True
    message: str
    result_id: str
    max_displacement: float = Field(..., description="Maximum displacement magnitude.")
    max_von_mises: float = Field(..., description="Maximum Von Mises stress.")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warnings about result credibility.")
    files: list[FileReference]


class ResultFieldResponse(BaseModel):
    success: bool = True
    message: str
    result_id: str
    field: ResultFieldName
    file: FileReference
