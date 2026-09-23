"""Adapters exposing the customer SDK contracts to the runtime contracts.

The SDK (``wmr_sim.sdk``) is the customer-facing surface; the runtime uses
``TrafficManager`` / ``TaskManager``. These adapters let a third-party plugin
written against the SDK be loaded and executed by the runtime unchanged, so a
customer only has to implement the documented input/output contract.
"""

from __future__ import annotations

import time
from typing import Any, Mapping, Sequence

from wmr_sim.sdk.dataclasses import Pose2D
from wmr_sim.task_management.interfaces import TaskManager
from wmr_sim.task_management.models import (TaskAssignment, TaskAssignmentPlan)
from wmr_sim.traffic.interfaces import TrafficManager
from wmr_sim.traffic.models import (FleetSnapshot, PlannedCommand, TrafficPlan,
                                    TrafficRequest)


class SdkTrafficAdapter(TrafficManager):
    """Expose an SDK ``BaseTrafficPlugin`` as a runtime ``TrafficManager``."""

    name = "sdk_traffic_adapter"

    def __init__(self, plugin=None):
        self.plugin = plugin

    def configure(self, config: Mapping[str, Any]) -> None:
        super().configure(config)
        if self.plugin is not None:
            self.plugin.initialize(dict(config))

    def plan(self, requests: Sequence[TrafficRequest],
             snapshot: FleetSnapshot, epoch: int) -> TrafficPlan:
        if self.plugin is None:
            raise RuntimeError("SDK traffic plugin 未設定")
        fleet_states = {
            robot_id: Pose2D(robot.pose[0], robot.pose[1], robot.pose[2],
                             robot.level_id)
            for robot_id, robot in snapshot.robots.items()
        }
        commands = []
        for request in requests:
            path = [Pose2D(x, y, yaw, request.level_id)
                    for x, y, yaw in request.waypoints]
            result = self.plugin.plan_traffic(request.robot_id, path, fleet_states)
            command = dict(request.command)
            if not getattr(result, "accepted", True):
                command["sdk_rejected"] = True
            reason = str(getattr(result, "reason", "") or "")
            if reason:
                command["sdk_reason"] = reason
            pass_side = int(getattr(result, "pass_side", 0) or 0)
            if pass_side:
                command["pass_side"] = pass_side
            yield_to = str(getattr(result, "yield_to", "") or "")
            if yield_to:
                command["yield_to"] = yield_to
            encounter = str(getattr(result, "encounter_type", "") or "")
            if encounter:
                command["encounter_type"] = encounter
            commands.append(PlannedCommand(
                request.robot_id, command,
                max(0.0, float(getattr(result, "wait_duration_sec", 0.0) or 0.0))))
        now = time.time()
        return TrafficPlan(plan_id=f"sdk-traffic-{epoch}-{time.time_ns()}",
                           algorithm=self.name, epoch=epoch,
                           commands=tuple(commands), created_at=now,
                           valid_until=now + 5.0,
                           metadata={"adapter": "sdk_traffic"})

    def cancel(self, task_id: str) -> None:
        release = getattr(self.plugin, "release_lease", None)
        if callable(release):
            release(task_id)


class SdkTaskAdapter(TaskManager):
    """Expose an SDK ``BaseTaskManager`` as a runtime ``TaskManager``."""

    name = "sdk_task_adapter"

    def __init__(self, plugin=None):
        self.plugin = plugin

    def configure(self, config: Mapping[str, Any]) -> None:
        super().configure(config)
        if self.plugin is not None:
            self.plugin.initialize(dict(config))

    def plan_assignments(self, tasks, robots, epoch: int) -> TaskAssignmentPlan:
        if self.plugin is None:
            raise RuntimeError("SDK task plugin 未設定")
        payload_tasks = [
            {"task_id": task.task_id, "priority": task.priority,
             "level_id": task.level_id, "map_id": task.map_id,
             "target": dict(task.target), "command": dict(task.command)}
            for task in tasks
        ]
        payload_robots = [
            {"robot_id": robot.robot_id, "pose": list(robot.pose),
             "battery_pct": robot.battery_pct, "busy": robot.busy,
             "current_task_id": robot.current_task_id,
             "level_id": robot.level_id, "map_id": robot.map_id}
            for robot in robots
        ]
        result = self.plugin.plan_tasks(payload_tasks, payload_robots)
        assignment_map = dict(getattr(result, "assignments", {}) or {})
        waits = dict(getattr(result, "wait_durations", {}) or {})
        reason = str(getattr(result, "reason", "") or "sdk")
        assignments = [
            TaskAssignment(str(task_id), str(robot_id),
                           float(waits.get(task_id, 0.0) or 0.0), reason=reason)
            for task_id, robot_id in assignment_map.items() if robot_id
        ]
        assigned_ids = {item.task_id for item in assignments}
        unassigned = tuple((task.task_id, "unassigned by sdk plugin")
                           for task in tasks if task.task_id not in assigned_ids)
        return TaskAssignmentPlan(
            plan_id=f"sdk-task-{epoch}-{time.time_ns()}", algorithm=self.name,
            assignments=tuple(assignments), unassigned=unassigned,
            created_at=time.time(), metadata={"adapter": "sdk_task"})
