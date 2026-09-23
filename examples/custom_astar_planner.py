"""Custom A* Global Planner sample using wmr-sim-sdk.

Copyright (C) 2026 宇集創新科技. All Rights Reserved.
Sample code for SDK users — this sample itself is provided for reference use.

契約（wmr_sim.sdk.interfaces.BaseGlobalPlanner）::

    initialize(config: Dict[str, Any]) -> None
    plan_path(start: Pose2D, goal: Pose2D,
              grid_map: OccupancyGridData,
              costmap: Optional[OccupancyGridData] = None) -> List[Pose2D]
    cancel_planning() -> None            # 選用

本範例在佔用網格上實作 8 連通 A*，並將結果簡化為航點序列。
若起點／終點不可通行或無解，則退化為直線內插（保證永遠回傳可用路徑）。
"""

from __future__ import annotations

import heapq
import math
from typing import Any, Dict, List, Optional, Tuple

from wmr_sim.sdk.dataclasses import OccupancyGridData, Pose2D
from wmr_sim.sdk.interfaces import BaseGlobalPlanner

# 佔用機率 >= 此值視為障礙
OCCUPIED_THRESHOLD = 50
# 8 連通移動成本（直走 / 斜走）
_STRAIGHT, _DIAGONAL = 1.0, math.sqrt(2.0)
_NEIGHBOURS: Tuple[Tuple[int, int, float], ...] = (
    (1, 0, _STRAIGHT), (-1, 0, _STRAIGHT), (0, 1, _STRAIGHT), (0, -1, _STRAIGHT),
    (1, 1, _DIAGONAL), (1, -1, _DIAGONAL), (-1, 1, _DIAGONAL), (-1, -1, _DIAGONAL),
)


class CustomerAStarPlanner(BaseGlobalPlanner):
    """Example custom global planner implementation for wmrSim."""

    #: 由 PluginDiscoverer / manifest 讀取之用
    name = "customer_astar"
    version = "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        """由 runtime 呼叫；讀取 manifest ``parameters`` 之值。"""
        self.occupied_threshold = int(config.get("occupied_threshold", OCCUPIED_THRESHOLD))
        self.allow_diagonal = bool(config.get("allow_diagonal", True))
        self.weight = float(config.get("heuristic_weight", 1.0))
        self.max_expansions = int(config.get("max_expansions", 200000))
        self._cancelled = False

    # ------------------------------------------------------------------ #
    # 主要介面
    # ------------------------------------------------------------------ #
    def plan_path(
        self,
        start: Pose2D,
        goal: Pose2D,
        grid_map: OccupancyGridData,
        costmap: Optional[OccupancyGridData] = None,
    ) -> List[Pose2D]:
        """Compute global path from start to goal (world frame)."""
        self._cancelled = False

        start_cell = self._world_to_cell(grid_map, start.x, start.y)
        goal_cell = self._world_to_cell(grid_map, goal.x, goal.y)

        if start_cell is None or goal_cell is None:
            return self._straight_line(start, goal)

        cells = self._astar(grid_map, start_cell, goal_cell)
        if not cells:
            return self._straight_line(start, goal)

        waypoints = self._simplify(grid_map, cells)
        path = [self._cell_to_pose(grid_map, c, i, waypoints) for i, c in enumerate(waypoints)]
        # 保證端點精確等於請求的起點／終點
        path[0] = Pose2D(start.x, start.y, path[0].theta_rad, start.level)
        path[-1] = Pose2D(goal.x, goal.y, path[-1].theta_rad, goal.level)
        return path

    def cancel_planning(self) -> None:
        """runtime 要求中止長時間規劃時呼叫。"""
        self._cancelled = True

    # ------------------------------------------------------------------ #
    # 內部：座標轉換
    # ------------------------------------------------------------------ #
    def _world_to_cell(self, grid: OccupancyGridData,
                       x: float, y: float) -> Optional[Tuple[int, int]]:
        col = int((x - grid.origin_x) / grid.resolution_m)
        row = int((y - grid.origin_y) / grid.resolution_m)
        if 0 <= col < grid.width and 0 <= row < grid.height:
            return row, col
        return None

    def _cell_to_world(self, grid: OccupancyGridData, cell: Tuple[int, int]) -> Tuple[float, float]:
        row, col = cell
        return (grid.origin_x + (col + 0.5) * grid.resolution_m,
                grid.origin_y + (row + 0.5) * grid.resolution_m)

    def _cell_to_pose(self, grid: OccupancyGridData, cell: Tuple[int, int],
                      index: int, waypoints: List[Tuple[int, int]]) -> Pose2D:
        x, y = self._cell_to_world(grid, cell)
        nxt = waypoints[index + 1] if index + 1 < len(waypoints) else None
        if nxt is None:
            heading = 0.0
        else:
            nx, ny = self._cell_to_world(grid, nxt)
            heading = math.atan2(ny - y, nx - x)
        return Pose2D(x, y, heading)

    def _is_free(self, grid: OccupancyGridData, cell: Tuple[int, int]) -> bool:
        row, col = cell
        if not (0 <= col < grid.width and 0 <= row < grid.height):
            return False
        value = grid.data[row * grid.width + col]
        # -1 表未知：保守起見視為不可通行，避免規劃穿越未建圖區域
        return 0 <= value < self.occupied_threshold

    # ------------------------------------------------------------------ #
    # 內部：A*
    # ------------------------------------------------------------------ #
    def _astar(self, grid: OccupancyGridData,
               start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        if not self._is_free(grid, start) or not self._is_free(grid, goal):
            return []

        neighbours = _NEIGHBOURS if self.allow_diagonal else _NEIGHBOURS[:4]
        open_heap: List[Tuple[float, Tuple[int, int]]] = [
            (self._heuristic(start, goal), start)
        ]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0.0}
        closed = set()
        expansions = 0

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current == goal:
                return self._reconstruct(came_from, current)
            if current in closed:
                continue
            closed.add(current)

            expansions += 1
            if self._cancelled or expansions > self.max_expansions:
                return []

            for d_row, d_col, cost in neighbours:
                nxt = (current[0] + d_row, current[1] + d_col)
                if nxt in closed or not self._is_free(grid, nxt):
                    continue
                tentative = g_score[current] + cost
                if tentative < g_score.get(nxt, math.inf):
                    came_from[nxt] = current
                    g_score[nxt] = tentative
                    f = tentative + self.weight * self._heuristic(nxt, goal)
                    heapq.heappush(open_heap, (f, nxt))
        return []

    @staticmethod
    def _heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        # 八方向啟發式（octile distance）
        d_row, d_col = abs(a[0] - b[0]), abs(a[1] - b[1])
        return (d_row + d_col) + (_DIAGONAL - 2.0) * min(d_row, d_col)

    @staticmethod
    def _reconstruct(came_from: Dict[Tuple[int, int], Tuple[int, int]],
                     current: Tuple[int, int]) -> List[Tuple[int, int]]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _simplify(self, grid: OccupancyGridData,
                  cells: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """移除共線中間點，僅保留轉折處（降低 Nav2 下游負擔）。"""
        if len(cells) <= 2:
            return list(cells)
        simplified = [cells[0]]
        for i in range(1, len(cells) - 1):
            prev, cur, nxt = cells[i - 1], cells[i], cells[i + 1]
            if (cur[0] - prev[0], cur[1] - prev[1]) != (nxt[0] - cur[0], nxt[1] - cur[1]):
                simplified.append(cur)
        simplified.append(cells[-1])
        return simplified

    @staticmethod
    def _straight_line(start: Pose2D, goal: Pose2D, step_m: float = 0.25) -> List[Pose2D]:
        """退化路徑：無網格或無解時的直線內插。"""
        dx, dy = goal.x - start.x, goal.y - start.y
        distance = math.hypot(dx, dy)
        steps = max(1, int(distance / max(step_m, 1e-3)))
        heading = math.atan2(dy, dx) if distance > 1e-6 else start.theta_rad
        path = [Pose2D(start.x, start.y, heading, start.level)]
        for i in range(1, steps):
            ratio = i / steps
            path.append(Pose2D(round(start.x + dx * ratio, 4),
                               round(start.y + dy * ratio, 4),
                               heading, start.level))
        path.append(Pose2D(goal.x, goal.y, heading, goal.level))
        return path
