"""Custom Traffic Manager sample using wmr-sim-sdk.

Copyright (C) 2026 宇集創新科技. All Rights Reserved.
Sample code for SDK users — this sample itself is provided for reference use.

契約（wmr_sim.sdk.interfaces.BaseTrafficPlugin）::

    initialize(config: Dict[str, Any]) -> None
    plan_traffic(robot_id: str,
                 requested_path: List[Pose2D],
                 fleet_states: Dict[str, Pose2D]) -> CustomerTrafficPlanResult
    request_rolling_lease(...) -> bool    # 選用
    release_lease(robot_id) -> None       # 選用

runtime 端由 ``SdkTrafficAdapter`` 橋接為 ``wmr_sim.traffic/v1`` 的
``TrafficPlan``；``pass_side`` / ``yield_to`` / ``encounter_type`` 會被寫入
command metadata，``wait_duration_sec`` 對應 ``dispatch_after``。
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from wmr_sim.sdk.dataclasses import (CustomerTrafficPlanResult, Pose2D)
from wmr_sim.sdk.interfaces import BaseTrafficPlugin

ENCOUNTER_NONE = "none"
ENCOUNTER_HEAD_ON = "head_on"
ENCOUNTER_SAME = "same"
ENCOUNTER_CROSSING = "crossing"


class CustomerTrafficManager(BaseTrafficPlugin):
    """靠右通行 (keep-right) + 直行優先的示範交管演算法。"""

    name = "customer_traffic"
    version = "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        self.detection_range_m = float(config.get("detection_range_m", 6.0))
        self.corridor_half_angle_rad = math.radians(
            float(config.get("corridor_half_angle_deg", 60.0)))
        self.head_on_threshold_deg = float(config.get("head_on_threshold_deg", 120.0))
        self.yield_duration_sec = float(config.get("yield_duration_sec", 1.5))
        self.keep_right = bool(config.get("keep_right", True))

    # ------------------------------------------------------------------ #
    # 主要介面
    # ------------------------------------------------------------------ #
    def plan_traffic(
        self,
        robot_id: str,
        requested_path: List[Pose2D],
        fleet_states: Dict[str, Pose2D],
    ) -> CustomerTrafficPlanResult:
        """Evaluate and coordinate traffic route for a robot."""
        if not requested_path:
            return CustomerTrafficPlanResult(accepted=False, reason="empty path")

        self_pose = fleet_states.get(robot_id, requested_path[0])
        self_heading = requested_path[0].theta_rad

        conflict_id, encounter = self._find_conflict(
            robot_id, self_pose, self_heading, requested_path, fleet_states)

        if conflict_id is None:
            return CustomerTrafficPlanResult(
                accepted=True,
                pass_side=(+1 if self.keep_right else 0),
                encounter_type=ENCOUNTER_NONE,
                reason="clear",
            )

        # 優先權：robot_id 字典序較小者優先（示範用；實務請用 priority 欄位）
        should_yield = conflict_id < robot_id and encounter in (
            ENCOUNTER_HEAD_ON, ENCOUNTER_CROSSING)

        return CustomerTrafficPlanResult(
            accepted=True,
            pass_side=(+1 if self.keep_right else -1),
            yield_to=conflict_id if should_yield else "",
            wait_duration_sec=self.yield_duration_sec if should_yield else 0.0,
            encounter_type=encounter,
            reason=(f"yield to {conflict_id} ({encounter})" if should_yield
                    else f"proceed, keep-right vs {conflict_id} ({encounter})"),
        )

    def release_lease(self, robot_id: str) -> None:
        """示範用：本演算法無狀態，無需釋放資源。"""
        return None

    # ------------------------------------------------------------------ #
    # 內部：衝突偵測
    # ------------------------------------------------------------------ #
    def _find_conflict(self, robot_id: str, self_pose: Pose2D, self_heading: float,
                       requested_path: List[Pose2D],
                       fleet_states: Dict[str, Pose2D]):
        best_id, best_encounter, best_distance = None, ENCOUNTER_NONE, math.inf

        for other_id, other_pose in fleet_states.items():
            if other_id == robot_id:
                continue
            dx = other_pose.x - self_pose.x
            dy = other_pose.y - self_pose.y
            distance = math.hypot(dx, dy)
            if distance > self.detection_range_m or distance >= best_distance:
                continue

            bearing = math.atan2(dy, dx)
            relative = abs(self._normalize_angle(bearing - self_heading))
            # 不在前方走廊內 → 不構成衝突
            if relative > self.corridor_half_angle_rad:
                continue

            encounter = self._classify(self_heading, other_pose.theta_rad, relative)
            if encounter == ENCOUNTER_NONE:
                continue

            best_id, best_encounter, best_distance = other_id, encounter, distance

        return best_id, best_encounter

    def _classify(self, self_heading: float, other_heading: float,
                  relative_bearing: float) -> str:
        diff = abs(self._normalize_angle(other_heading - self_heading))
        if diff > math.radians(self.head_on_threshold_deg):
            return ENCOUNTER_HEAD_ON
        if diff < math.radians(45.0):
            return ENCOUNTER_SAME
        if relative_bearing < math.radians(60.0):
            return ENCOUNTER_CROSSING
        return ENCOUNTER_NONE

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        return (angle + math.pi) % (2.0 * math.pi) - math.pi
