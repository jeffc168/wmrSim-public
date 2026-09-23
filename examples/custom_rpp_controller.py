"""Custom Regulated Pure Pursuit (RPP) Local Controller sample using wmr-sim-sdk.

Copyright (C) 2026 宇集創新科技. All Rights Reserved.
Sample code for SDK users — this sample itself is provided for reference use.

契約（wmr_sim.sdk.interfaces.BaseLocalController）::

    initialize(config: Dict[str, Any]) -> None
    compute_velocity(current_pose: Pose2D,
                     current_vel: Velocity2D,
                     target_path: List[Pose2D],
                     dt_sec: float,
                     local_costmap: Optional[OccupancyGridData] = None,
                     obstacles: Optional[List[Pose2D]] = None) -> Velocity2D
    reset() -> None                       # 選用

注意：``Velocity2D`` 欄位為 ``vx`` / ``vy`` / ``vtheta_rad_s``
（差速車請將 ``vy`` 保持 0.0）。
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from wmr_sim.sdk.dataclasses import (OccupancyGridData, Pose2D, Velocity2D)
from wmr_sim.sdk.interfaces import BaseLocalController

# 與 wmrSim 差速底盤一致的預設限制
DEFAULT_MAX_LINEAR = 0.8        # m/s
DEFAULT_MAX_ANGULAR = 1.2       # rad/s
DEFAULT_MAX_ACCEL = 1.0         # m/s^2
DEFAULT_MAX_ALPHA = 3.0         # rad/s^2


class CustomerRPPController(BaseLocalController):
    """Example custom local controller implementation for wmrSim."""

    name = "customer_rpp"
    version = "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        """由 runtime 呼叫；讀取 manifest ``parameters`` 之值。"""
        self.lookahead_dist = float(config.get("lookahead_dist", 0.6))
        self.max_linear_vel = float(config.get("max_linear_vel", DEFAULT_MAX_LINEAR))
        self.max_angular_vel = float(config.get("max_angular_vel", DEFAULT_MAX_ANGULAR))
        self.max_accel = float(config.get("max_accel", DEFAULT_MAX_ACCEL))
        self.max_alpha = float(config.get("max_alpha", DEFAULT_MAX_ALPHA))
        self.goal_tolerance = float(config.get("goal_tolerance", 0.10))
        self.yaw_gain = float(config.get("yaw_gain", 2.0))
        self.slowdown_radius = float(config.get("slowdown_radius", 0.5))
        self.avoidance_radius = float(config.get("avoidance_radius", 0.6))
        self.reset()

    def reset(self) -> None:
        """清除積分項／快取（runtime 於新任務開始時呼叫）。"""
        self._previous_cmd = Velocity2D(0.0, 0.0, 0.0)

    # ------------------------------------------------------------------ #
    # 主要介面
    # ------------------------------------------------------------------ #
    def compute_velocity(
        self,
        current_pose: Pose2D,
        current_vel: Velocity2D,
        target_path: List[Pose2D],
        dt_sec: float,
        local_costmap: Optional[OccupancyGridData] = None,
        obstacles: Optional[List[Pose2D]] = None,
    ) -> Velocity2D:
        """Compute linear and angular velocity commands for local path tracking."""
        if not target_path:
            return self._rate_limit(Velocity2D(0.0, 0.0, 0.0), dt_sec)

        # 1. 取得前視點 (pure pursuit lookahead)
        target = self._select_lookahead(current_pose, target_path)
        dx, dy = target.x - current_pose.x, target.y - current_pose.y
        distance = math.hypot(dx, dy)

        # 2. 到達終點：停車
        goal = target_path[-1]
        if math.hypot(goal.x - current_pose.x, goal.y - current_pose.y) < self.goal_tolerance:
            return self._rate_limit(Velocity2D(0.0, 0.0, 0.0), dt_sec)

        # 3. 航向誤差（正規化到 [-pi, pi]）
        target_yaw = math.atan2(dy, dx)
        yaw_err = self._normalize_angle(target_yaw - current_pose.theta_rad)

        # 4. 角速度：比例控制 + 限幅
        omega = max(-self.max_angular_vel,
                    min(self.max_angular_vel, self.yaw_gain * yaw_err))

        # 5. 線速度：受航向誤差與近端減速調節（regulated）
        v = self.max_linear_vel * max(0.0, math.cos(yaw_err))
        if distance < self.slowdown_radius:
            v *= max(0.1, distance / self.slowdown_radius)

        # 6. 障礙物減速（本範例為簡化式；實務請搭配動態視窗法）
        clearance = self._min_obstacle_clearance(current_pose, obstacles)
        if clearance is not None and clearance < self.avoidance_radius:
            v *= max(0.0, clearance / self.avoidance_radius)

        cmd = Velocity2D(vx=max(0.0, v), vy=0.0, vtheta_rad_s=omega)
        return self._rate_limit(cmd, dt_sec)

    # ------------------------------------------------------------------ #
    # 內部工具
    # ------------------------------------------------------------------ #
    def _select_lookahead(self, pose: Pose2D,
                          path: List[Pose2D]) -> Pose2D:
        """由近而遠尋找第一個距離 >= lookahead_dist 的航點。"""
        for point in path:
            if math.hypot(point.x - pose.x, point.y - pose.y) >= self.lookahead_dist:
                return point
        return path[-1]

    def _rate_limit(self, cmd: Velocity2D, dt_sec: float) -> Velocity2D:
        """依加速度上限對速度命令做速率限制（避免突波）。"""
        dt = max(float(dt_sec), 1e-3)
        prev = self._previous_cmd
        max_dv = self.max_accel * dt
        max_dw = self.max_alpha * dt
        vx = prev.vx + max(-max_dv, min(max_dv, cmd.vx - prev.vx))
        omega = prev.vtheta_rad_s + max(-max_dw, min(max_dw, cmd.vtheta_rad_s - prev.vtheta_rad_s))
        limited = Velocity2D(vx=vx, vy=0.0, vtheta_rad_s=omega)
        self._previous_cmd = limited
        return limited

    def _min_obstacle_clearance(self, pose: Pose2D,
                                obstacles: Optional[List[Pose2D]]) -> Optional[float]:
        if not obstacles:
            return None
        distances = [math.hypot(o.x - pose.x, o.y - pose.y) for o in obstacles]
        return min(distances) if distances else None

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        return (angle + math.pi) % (2.0 * math.pi) - math.pi
