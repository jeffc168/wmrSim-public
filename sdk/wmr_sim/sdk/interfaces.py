"""wmrSim SDK Abstract Interfaces for Customer Extensions.

External customers subclass these interfaces to implement custom
Traffic Coordinators, Global Path Planners, and Local Controllers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from .dataclasses import (Pose2D, Velocity2D, OccupancyGridData,
                           CustomerTaskPlanResult, CustomerTrafficPlanResult)


class BaseTrafficPlugin(ABC):
    """Abstract Base Class for Customer Traffic Coordination Algorithms."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with custom parameters."""
        pass

    @abstractmethod
    def plan_traffic(self,
                     robot_id: str,
                     requested_path: List[Pose2D],
                     fleet_states: Dict[str, Pose2D]) -> CustomerTrafficPlanResult:
        """Evaluate and coordinate traffic route for a robot."""
        pass

    def request_rolling_lease(self,
                              robot_id: str,
                              current_pose: Pose2D,
                              forward_path: List[Pose2D],
                              lease_radius_m: float = 3.0) -> bool:
        """Optional rolling lease claim for dynamic spatial-temporal traffic."""
        return True

    def release_lease(self, robot_id: str) -> None:
        """Optional release of active spatial leases for a robot."""
        pass


class BaseTaskManager(ABC):
    """Abstract Base Class for Customer Task Assignment / Scheduling Algorithms.

    Receives the pending tasks and current robots (plain dicts, see
    ``docs``/``future_work.md`` 第 2 部 §E.3) and returns which task each robot
    should execute. The runtime keeps ownership of the task lifecycle.
    """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with custom parameters."""
        pass

    @abstractmethod
    def plan_tasks(self,
                   pending_tasks: List[Dict[str, Any]],
                   robots: List[Dict[str, Any]]) -> CustomerTaskPlanResult:
        """Assign pending tasks to available robots."""
        pass


class BaseGlobalPlanner(ABC):
    """Abstract Base Class for Customer Global Path Planning Algorithms."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize planner plugin."""
        pass

    @abstractmethod
    def plan_path(self,
                  start: Pose2D,
                  goal: Pose2D,
                  grid_map: OccupancyGridData,
                  costmap: Optional[OccupancyGridData] = None) -> List[Pose2D]:
        """Compute global path from start to goal."""
        pass

    def cancel_planning(self) -> None:
        """Signal interrupt/cancellation to long-running planning jobs."""
        pass


class BaseLocalController(ABC):
    """Abstract Base Class for Customer Local Trajectory Tracking & Obstacle Avoidance."""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize controller plugin."""
        pass

    @abstractmethod
    def compute_velocity(self,
                         current_pose: Pose2D,
                         current_vel: Velocity2D,
                         target_path: List[Pose2D],
                         dt_sec: float,
                         local_costmap: Optional[OccupancyGridData] = None,
                         obstacles: Optional[List[Pose2D]] = None) -> Velocity2D:
        """Compute linear and angular velocity commands for local path tracking."""
        pass

    def reset(self) -> None:
        """Reset internal controller state (e.g. integral terms or trajectory caches)."""
        pass

