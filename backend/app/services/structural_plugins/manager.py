import importlib.util
from functools import lru_cache
from pathlib import Path

import yaml

from app.services.structural_plugins.models import StructuralPluginManifest, StructuralPluginRecord


class StructuralSolverManager:
    def __init__(self, plugins_root: Path):
        self.plugins_root = plugins_root
        self._plugins = self._scan_plugins()

    def list_plugins(self) -> list[StructuralPluginRecord]:
        return list(self._plugins.values())

    def get_plugin(self, plugin_id: str) -> StructuralPluginRecord:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise ValueError(f"Unknown solver plugin: {plugin_id}")
        return plugin

    def create_plugin(self, plugin_id: str):
        record = self.get_plugin(plugin_id)
        return record.plugin_class(record.plugin_dir, record.manifest)

    def _scan_plugins(self) -> dict[str, StructuralPluginRecord]:
        plugins: dict[str, StructuralPluginRecord] = {}
        if not self.plugins_root.exists():
            return plugins
        for plugin_dir in sorted(path for path in self.plugins_root.iterdir() if path.is_dir()):
            manifest_path = plugin_dir / "plugin.yaml"
            if not manifest_path.exists():
                continue
            manifest = self._load_manifest(manifest_path)
            if manifest.id in plugins:
                raise ValueError(f"Duplicate solver plugin id: {manifest.id}")
            entry_path = plugin_dir / manifest.entry
            plugin_class = self._load_plugin_class(manifest.id, entry_path, manifest.class_name)
            plugins[manifest.id] = StructuralPluginRecord(
                manifest=manifest,
                plugin_dir=plugin_dir,
                plugin_class=plugin_class,
                executable_path=plugin_dir / manifest.executable,
            )
        return plugins

    @staticmethod
    def _load_manifest(manifest_path: Path) -> StructuralPluginManifest:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        required_fields = ["id", "name", "version", "backend", "entry", "class", "executable"]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            raise ValueError(f"Missing required plugin fields in {manifest_path}: {', '.join(missing)}")
        return StructuralPluginManifest(
            id=str(payload["id"]),
            name=str(payload["name"]),
            version=str(payload["version"]),
            backend=str(payload["backend"]),
            entry=str(payload["entry"]),
            class_name=str(payload["class"]),
            executable=str(payload["executable"]),
        )

    @staticmethod
    def _load_plugin_class(plugin_id: str, entry_path: Path, class_name: str) -> type:
        if not entry_path.exists():
            raise ValueError(f"Plugin entry file not found: {entry_path}")
        spec = importlib.util.spec_from_file_location(f"app.plugins.{plugin_id}.adapter", entry_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Unable to load plugin module: {entry_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_class = getattr(module, class_name, None)
        if plugin_class is None:
            raise ValueError(f"Plugin class {class_name} not found in {entry_path}")
        return plugin_class


@lru_cache
def get_structural_solver_manager() -> StructuralSolverManager:
    return StructuralSolverManager(Path(__file__).resolve().parents[2] / "plugins")
