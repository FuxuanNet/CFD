from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.solver import SolverRunRequest, SolverRunResponse
from app.services.structural_plugins.models import StructuralPluginManifest


class StructuralSolverPlugin(ABC):
    def __init__(self, plugin_dir: Path, manifest: StructuralPluginManifest):
        self.plugin_dir = plugin_dir
        self.manifest = manifest

    @abstractmethod
    def solve(self, request: SolverRunRequest, emit=None) -> SolverRunResponse:
        raise NotImplementedError
