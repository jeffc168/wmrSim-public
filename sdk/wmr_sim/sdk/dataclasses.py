"""wmrSim SDK Data Structures for Customer Algorithm Extensions.

Provides strongly-typed data models for Poses, Twists, Grids,
Traffic Snapshots, and Plugin Validation Reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


@dataclass
class Pose2D:
    x: float
    y: float
    theta_rad: float = 0.0
    level: str = "L1"


@dataclass
class Velocity2D:
    vx: float = 0.0
    vy: float = 0.0
    vtheta_rad_s: float = 0.0


Twist2D = Velocity2D  # ROS Twist alias


@dataclass
class OccupancyGridData:
    width: int
    height: int
    resolution_m: float
    origin_x: float
    origin_y: float
    data: List[int] = field(repr=False)  # 0-100 occupancy values, -1 for unknown


class PluginStatus(str, Enum):
    VALID = "VALID"
    INVALID_INTERFACE = "INVALID_INTERFACE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class PluginValidationReport:
    status: PluginStatus
    plugin_name: str
    avg_latency_ms: float = 0.0
    error_message: str = ""
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)


@dataclass
class CustomerTrafficPlanResult:
    """Traffic plugin output contract (``wmr_sim.traffic/v1``).

    ``pass_side`` / ``yield_to`` / ``encounter_type`` are optional coordination
    hints consumed by the runtime (see future_work.md 第 2 部 建議 1-3).
    """

    accepted: bool
    modified_waypoints: Optional[List[Pose2D]] = None
    wait_duration_sec: float = 0.0
    reason: str = ""
    pass_side: int = 0            # +1 靠右 / -1 靠左 / 0 不指定
    yield_to: str = ""            # 讓路的對象 robot_id
    encounter_type: str = ""      # head_on | crossing | converging | same | none
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerTaskPlanResult:
    """Task plugin output contract (``wmr_sim.task/v1``).

    ``assignments`` maps ``task_id -> robot_id``; tasks omitted from it are
    reported back to the runtime as unassigned.
    """

    assignments: Dict[str, str] = field(default_factory=dict)
    wait_durations: Dict[str, float] = field(default_factory=dict)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginType(str, Enum):
    GLOBAL_PLANNER = "GLOBAL_PLANNER"
    LOCAL_CONTROLLER = "LOCAL_CONTROLLER"
    TRAFFIC_MANAGER = "TRAFFIC_MANAGER"
    TASK_MANAGER = "TASK_MANAGER"


class PluginCapability(str, Enum):
    DIFFERENTIAL_DRIVE = "DIFFERENTIAL_DRIVE"
    OMNIDIRECTIONAL = "OMNIDIRECTIONAL"
    DYNAMIC_OBSTACLE_AVOIDANCE = "DYNAMIC_OBSTACLE_AVOIDANCE"
    TIME_SCHEDULED_ROUTING = "TIME_SCHEDULED_ROUTING"
    MULTI_FLOOR_ROUTING = "MULTI_FLOOR_ROUTING"
    ROLLING_LEASE = "ROLLING_LEASE"
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    RECIPROCAL_AVOIDANCE = "RECIPROCAL_AVOIDANCE"


@dataclass
class PluginParameterSchema:
    name: str
    type: str  # "float", "int", "bool", "str"
    default: Any
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    plugin_type: PluginType
    entrypoint: str
    author: str = ""
    description: str = ""
    capabilities: List[PluginCapability] = field(default_factory=list)
    parameters: List[PluginParameterSchema] = field(default_factory=list)
    ros_package: str = ""


@dataclass
class Point3D:
    x: float
    y: float
    z: float
    intensity: float = 0.0


@dataclass
class PointCloud3DData:
    frame_id: str
    timestamp_sec: float
    points: List[Point3D] = field(default_factory=list)

