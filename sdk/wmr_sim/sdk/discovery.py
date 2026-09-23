"""Plugin Auto-Discovery subsystem for wmrSim SDK.

Discovers third-party and built-in algorithm plugins registered via ROS 2
ament_index (share/ament_index/resource_index/wmr_sim_plugins) or explicit
directory manifests in designated paths.
"""

import importlib
import json
import logging
import os
import sys
from typing import Dict, List, Optional

from .dataclasses import (
    PluginCapability,
    PluginManifest,
    PluginParameterSchema,
    PluginType,
)
from .interfaces import (BaseGlobalPlanner, BaseLocalController,
                         BaseTaskManager, BaseTrafficPlugin)

_logger = logging.getLogger("wmr_sim.sdk.discovery")

RESOURCE_INDEX_CATEGORY = "wmr_sim_plugins"
DEFAULT_ENV_VAR = "WMR_SIM_PLUGIN_PATH"


class PluginDiscoverer:
    """Discovers and parses plugin manifests from installed ROS 2 packages and designated directories."""

    def __init__(
        self,
        extra_search_paths: Optional[List[str]] = None,
        auto_default_paths: bool = True,
    ) -> None:
        self._extra_paths: List[str] = list(extra_search_paths or [])
        self._discovered: Dict[str, PluginManifest] = {}

        if auto_default_paths:
            self._add_default_search_paths()

    def _add_default_search_paths(self) -> None:
        # 1. Environment variable (WMR_SIM_PLUGIN_PATH)
        env_val = os.environ.get(DEFAULT_ENV_VAR, "").strip()
        if env_val:
            delimiter = ";" if os.name == "nt" else ":"
            for p in env_val.split(delimiter):
                p = p.strip()
                if p and p not in self._extra_paths:
                    self._extra_paths.append(p)

        # 2. User home path: ~/.wmr_sim/plugins
        user_plugins = os.path.expanduser("~/.wmr_sim/plugins")
        if user_plugins not in self._extra_paths:
            self._extra_paths.append(user_plugins)

        # 3. Workspace standard directory: ./plugins
        workspace_plugins = os.path.abspath("plugins")
        if workspace_plugins not in self._extra_paths:
            self._extra_paths.append(workspace_plugins)

    def discover_all(
        self, force_refresh: bool = False, verify: bool = True
    ) -> Dict[str, PluginManifest]:
        """Discover all available wmr_sim plugins across ament_index and extra paths."""
        if self._discovered and not force_refresh:
            return dict(self._discovered)

        discovered: Dict[str, PluginManifest] = {}

        # 1. Scan ROS 2 ament_index
        try:
            from ament_index_python.packages import (
                get_package_share_directory,
                get_resources,
            )
            resources = get_resources(RESOURCE_INDEX_CATEGORY)
            for pkg_name, resource_content in resources.items():
                try:
                    share_dir = get_package_share_directory(pkg_name)
                    manifest_path = os.path.join(share_dir, "manifest.json")
                    if os.path.isfile(manifest_path):
                        manifest = self._load_manifest_file(manifest_path, ros_package=pkg_name)
                        if manifest:
                            if not verify or self._verify_manifest(manifest):
                                discovered[manifest.plugin_id] = manifest
                    else:
                        # Parse resource content directly if formatted as JSON
                        if resource_content.strip().startswith("{"):
                            manifest = self._parse_manifest_dict(
                                json.loads(resource_content), ros_package=pkg_name
                            )
                            if manifest:
                                if not verify or self._verify_manifest(manifest):
                                    discovered[manifest.plugin_id] = manifest
                except Exception as exc:
                    _logger.warning("Failed to inspect ament plugin package %s: %s", pkg_name, exc)
        except (ImportError, OSError):
            _logger.debug("ament_index_python or AMENT_PREFIX_PATH not available; skipping ROS 2 resource index scanning.")

        # 2. Scan extra explicit and default paths
        for path in self._extra_paths:
            if not os.path.isdir(path):
                continue

            # Ensure root search path is in sys.path
            if path not in sys.path:
                sys.path.insert(0, path)

            for root, _, files in os.walk(path):
                if "manifest.json" in files:
                    # Ensure the plugin folder and its parent are in sys.path
                    if root not in sys.path:
                        sys.path.insert(0, root)
                    parent = os.path.dirname(root)
                    if parent and parent not in sys.path:
                        sys.path.insert(0, parent)

                    mpath = os.path.join(root, "manifest.json")
                    manifest = self._load_manifest_file(mpath)
                    if manifest:
                        if verify and not self._verify_manifest(manifest):
                            _logger.warning(
                                "Plugin '%s' at %s failed verification; discarded from registration.",
                                manifest.plugin_id, mpath
                            )
                            continue
                        discovered[manifest.plugin_id] = manifest

        self._discovered = discovered
        return dict(self._discovered)

    def _verify_manifest(self, manifest: PluginManifest) -> bool:
        """Verify plugin conformance with PluginVerifier."""
        entrypoint = manifest.entrypoint.strip()
        if ":" not in entrypoint:
            # C++ symbol or external ROS package binary without direct Python module:Class
            return True

        try:
            from .verifier import PluginVerifier, PluginStatus

            instance = self.instantiate_plugin(manifest)
            if manifest.plugin_type == PluginType.GLOBAL_PLANNER:
                report = PluginVerifier.verify_global_planner(instance, num_benchmark_runs=2)
            elif manifest.plugin_type == PluginType.LOCAL_CONTROLLER:
                report = PluginVerifier.verify_local_controller(instance, num_benchmark_runs=2)
            elif manifest.plugin_type == PluginType.TRAFFIC_MANAGER:
                report = PluginVerifier.verify_traffic_plugin(instance, num_benchmark_runs=2)
            else:
                return True

            if report.status != PluginStatus.VALID:
                _logger.warning(
                    "Plugin '%s' (%s) rejected: status=%s, failed_checks=%s, error=%s",
                    manifest.plugin_id, manifest.name, report.status.value,
                    report.checks_failed, report.error_message,
                )
                return False
            return True
        except Exception as exc:
            _logger.warning("Plugin '%s' failed dynamic verification: %s", manifest.plugin_id, exc)
            return False

    def get_by_type(self, plugin_type: PluginType) -> Dict[str, PluginManifest]:
        """Return plugins filtered by plugin_type."""
        all_plugins = self.discover_all()
        return {
            pid: m for pid, m in all_plugins.items() if m.plugin_type == plugin_type
        }

    def instantiate_plugin(self, manifest: PluginManifest):
        """Dynamically instantiate the plugin class specified in the manifest."""
        entrypoint = manifest.entrypoint.strip()
        if ":" not in entrypoint:
            raise ValueError(f"Invalid entrypoint '{entrypoint}', expected 'module.submodule:ClassName'")

        mod_name, cls_name = entrypoint.split(":", 1)
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)

        # Validate interface inheritance based on plugin type
        instance = cls()
        if manifest.plugin_type == PluginType.GLOBAL_PLANNER and not isinstance(instance, BaseGlobalPlanner):
            raise TypeError(f"{cls_name} does not inherit from BaseGlobalPlanner")
        elif manifest.plugin_type == PluginType.LOCAL_CONTROLLER and not isinstance(instance, BaseLocalController):
            raise TypeError(f"{cls_name} does not inherit from BaseLocalController")
        elif manifest.plugin_type == PluginType.TRAFFIC_MANAGER and not isinstance(instance, BaseTrafficPlugin):
            raise TypeError(f"{cls_name} does not inherit from BaseTrafficPlugin")
        elif manifest.plugin_type == PluginType.TASK_MANAGER and not isinstance(instance, BaseTaskManager):
            raise TypeError(f"{cls_name} does not inherit from BaseTaskManager")

        return instance

    def _load_manifest_file(self, file_path: str, ros_package: str = "") -> Optional[PluginManifest]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._parse_manifest_dict(data, ros_package=ros_package)
        except Exception as exc:
            _logger.warning("Failed to load plugin manifest file %s: %s", file_path, exc)
            return None

    def _parse_manifest_dict(self, data: dict, ros_package: str = "") -> Optional[PluginManifest]:
        try:
            params = []
            for p in data.get("parameters", []):
                params.append(
                    PluginParameterSchema(
                        name=str(p.get("name")),
                        type=str(p.get("type", "str")),
                        default=p.get("default"),
                        description=str(p.get("description", "")),
                        min_value=p.get("min_value"),
                        max_value=p.get("max_value"),
                    )
                )

            caps = []
            for c in data.get("capabilities", []):
                try:
                    caps.append(PluginCapability(c))
                except ValueError:
                    pass

            return PluginManifest(
                plugin_id=str(data["plugin_id"]),
                name=str(data.get("name", data["plugin_id"])),
                version=str(data.get("version", "1.0.0")),
                plugin_type=PluginType(data["plugin_type"]),
                entrypoint=str(data["entrypoint"]),
                author=str(data.get("author", "")),
                description=str(data.get("description", "")),
                capabilities=caps,
                parameters=params,
                ros_package=ros_package,
            )
        except Exception as exc:
            _logger.warning("Manifest parsing error: %s", exc)
            return None
