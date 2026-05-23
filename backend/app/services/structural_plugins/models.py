from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StructuralPluginManifest:
    id: str
    name: str
    version: str
    backend: str
    entry: str
    class_name: str
    executable: str


@dataclass(frozen=True)
class StructuralPluginRecord:
    manifest: StructuralPluginManifest
    plugin_dir: Path
    plugin_class: type
    executable_path: Path
