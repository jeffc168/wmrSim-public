"""wmrSim SDK Package for Customer Extensions.

公開之外掛開發介面（Open Plugin API）。
Copyright (C) 2026 宇集創新科技. All Rights Reserved.
Licensed under GNU General Public License v3.0 with Plugin Linking Exception.
Version: V1.0
"""

__version__ = "1.0.0"
__copyright__ = "Copyright (C) 2026 宇集創新科技. All Rights Reserved."
__license__ = "GPL-3.0-or-later WITH Plugin-Linking-Exception"

from .dataclasses import (
    Pose2D,
    Velocity2D,
    OccupancyGridData,
    PluginStatus,
    PluginValidationReport,
    CustomerTaskPlanResult,
    CustomerTrafficPlanResult,
    PluginType,
    PluginCapability,
    PluginParameterSchema,
    PluginManifest,
    Point3D,
    PointCloud3DData,
)
from .interfaces import (BaseTrafficPlugin, BaseGlobalPlanner,
                         BaseLocalController, BaseTaskManager)
from .verifier import PluginVerifier
from .discovery import PluginDiscoverer, RESOURCE_INDEX_CATEGORY

# ``adapters`` 需要 runtime（wmrSim 核心）才存在（它把 SDK 契約橋接至
# wmr_sim.traffic / wmr_sim.task_management）。核心未安裝時仍必須能
# import wmr_sim.sdk 以進行介面開發，因此改為惰性載入。
_LAZY_ADAPTERS = ("SdkTrafficAdapter", "SdkTaskAdapter")


def __getattr__(name: str):
    if name in _LAZY_ADAPTERS:
        from . import adapters  # noqa: PLC0415 - 延遲載入，避免純 SDK 環境失敗
        return getattr(adapters, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "Pose2D",
    "Velocity2D",
    "OccupancyGridData",
    "PluginStatus",
    "PluginValidationReport",
    "CustomerTaskPlanResult",
    "CustomerTrafficPlanResult",
    "PluginType",
    "PluginCapability",
    "PluginParameterSchema",
    "PluginManifest",
    "Point3D",
    "PointCloud3DData",
    "BaseTrafficPlugin",
    "BaseGlobalPlanner",
    "BaseLocalController",
    "BaseTaskManager",
    "SdkTrafficAdapter",
    "SdkTaskAdapter",
    "PluginVerifier",
    "PluginDiscoverer",
    "RESOURCE_INDEX_CATEGORY",
]
