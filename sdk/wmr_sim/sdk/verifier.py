"""wmrSim SDK Plugin Verifier.

Benchmark & validation testbed tool for customer-submitted plugins.
"""

import time
import traceback
from typing import Any, List

from .dataclasses import (
    Pose2D,
    Velocity2D,
    OccupancyGridData,
    PluginStatus,
    PluginValidationReport,
)
from .interfaces import (BaseTrafficPlugin, BaseGlobalPlanner,
                         BaseLocalController, BaseTaskManager)


class PluginVerifier:
    """Automated benchmark & contract compliance testbed for customer plugins."""

    @staticmethod
    def verify_traffic_plugin(plugin: Any, num_benchmark_runs: int = 10) -> PluginValidationReport:
        report = PluginValidationReport(
            status=PluginStatus.VALID,
            plugin_name=plugin.__class__.__name__,
            checks_passed=[],
            checks_failed=[]
        )

        if not isinstance(plugin, BaseTrafficPlugin):
            report.status = PluginStatus.INVALID_INTERFACE
            report.checks_failed.append("Must inherit from BaseTrafficPlugin")
            report.error_message = "Plugin does not inherit from BaseTrafficPlugin"
            return report

        report.checks_passed.append("Interface Inheritance Check")

        # Mock inputs
        dummy_path = [Pose2D(0.0, 0.0), Pose2D(5.0, 0.0), Pose2D(10.0, 0.0)]
        dummy_fleet = {"wmr_1": Pose2D(5.0, 1.0)}

        latencies = []
        try:
            plugin.initialize({})
            report.checks_passed.append("Initialization Check")

            for _ in range(num_benchmark_runs):
                t0 = time.perf_counter()
                res = plugin.plan_traffic("wmr_0", dummy_path, dummy_fleet)
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000.0)

            report.avg_latency_ms = sum(latencies) / len(latencies)
            report.checks_passed.append("Execution Latency Check")

            if report.avg_latency_ms > 50.0:
                report.checks_failed.append(f"Latency ({report.avg_latency_ms:.2f}ms) exceeds 50ms SLA threshold")
                report.status = PluginStatus.TIMEOUT

        except Exception as e:
            report.status = PluginStatus.RUNTIME_ERROR
            report.error_message = str(e) + "\n" + traceback.format_exc()
            report.checks_failed.append(f"Runtime Exception: {e}")

        return report

    @staticmethod
    def verify_task_manager(plugin: Any, num_benchmark_runs: int = 10) -> PluginValidationReport:
        """Benchmark a customer TaskManager plugin (``wmr_sim.task/v1``)."""
        report = PluginValidationReport(
            status=PluginStatus.VALID,
            plugin_name=plugin.__class__.__name__,
            checks_passed=[],
            checks_failed=[],
        )
        if not isinstance(plugin, BaseTaskManager):
            report.status = PluginStatus.INVALID_INTERFACE
            report.checks_failed.append("Must inherit from BaseTaskManager")
            report.error_message = "Plugin does not inherit from BaseTaskManager"
            return report

        report.checks_passed.append("Interface Inheritance Check")
        latencies = []
        try:
            plugin.initialize({})
            report.checks_passed.append("Initialization Check")
            for _ in range(max(1, int(num_benchmark_runs))):
                start = time.perf_counter()
                plugin.plan_tasks([], [])
                latencies.append((time.perf_counter() - start) * 1000.0)
            report.avg_latency_ms = sum(latencies) / len(latencies)
            report.checks_passed.append("Execution Latency Check")
            if report.avg_latency_ms > 50.0:
                report.checks_failed.append(
                    f"Latency ({report.avg_latency_ms:.2f}ms) exceeds 50ms SLA threshold")
                report.status = PluginStatus.TIMEOUT
        except Exception as exc:
            report.status = PluginStatus.RUNTIME_ERROR
            report.error_message = str(exc) + "\n" + traceback.format_exc()
            report.checks_failed.append(f"Runtime Exception: {exc}")
        return report

    @staticmethod
    def verify_global_planner(plugin: Any, num_benchmark_runs: int = 10) -> PluginValidationReport:
        report = PluginValidationReport(
            status=PluginStatus.VALID,
            plugin_name=plugin.__class__.__name__,
            checks_passed=[],
            checks_failed=[]
        )

        if not isinstance(plugin, BaseGlobalPlanner):
            report.status = PluginStatus.INVALID_INTERFACE
            report.checks_failed.append("Must inherit from BaseGlobalPlanner")
            report.error_message = "Plugin does not inherit from BaseGlobalPlanner"
            return report

        report.checks_passed.append("Interface Inheritance Check")

        dummy_grid = OccupancyGridData(
            width=20, height=20, resolution_m=0.05, origin_x=0.0, origin_y=0.0, data=[0] * 400
        )
        start = Pose2D(0.0, 0.0)
        goal = Pose2D(0.5, 0.5)

        latencies = []
        try:
            plugin.initialize({})
            report.checks_passed.append("Initialization Check")

            for _ in range(num_benchmark_runs):
                t0 = time.perf_counter()
                path = plugin.plan_path(start, goal, dummy_grid)
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000.0)

            report.avg_latency_ms = sum(latencies) / len(latencies)
            report.checks_passed.append("Path Execution Check")
        except Exception as e:
            report.status = PluginStatus.RUNTIME_ERROR
            report.error_message = str(e)
            report.checks_failed.append(f"Runtime Exception: {e}")

        return report

    @staticmethod
    def verify_local_controller(plugin: Any, num_benchmark_runs: int = 10) -> PluginValidationReport:
        report = PluginValidationReport(
            status=PluginStatus.VALID,
            plugin_name=plugin.__class__.__name__,
            checks_passed=[],
            checks_failed=[]
        )

        if not isinstance(plugin, BaseLocalController):
            report.status = PluginStatus.INVALID_INTERFACE
            report.checks_failed.append("Must inherit from BaseLocalController")
            report.error_message = "Plugin does not inherit from BaseLocalController"
            return report

        report.checks_passed.append("Interface Inheritance Check")

        pose = Pose2D(0.0, 0.0, 0.0)
        vel = Velocity2D(0.0, 0.0, 0.0)
        target_path = [Pose2D(1.0, 0.0), Pose2D(2.0, 0.0)]

        latencies = []
        try:
            plugin.initialize({})
            report.checks_passed.append("Initialization Check")

            for _ in range(num_benchmark_runs):
                t0 = time.perf_counter()
                cmd_vel = plugin.compute_velocity(pose, vel, target_path, dt_sec=0.1)
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000.0)

            report.avg_latency_ms = sum(latencies) / len(latencies)
            report.checks_passed.append("Velocity Calculation Check")
        except Exception as e:
            report.status = PluginStatus.RUNTIME_ERROR
            report.error_message = str(e)
            report.checks_failed.append(f"Runtime Exception: {e}")

        return report
