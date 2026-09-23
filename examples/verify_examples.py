#!/usr/bin/env python3
"""Self-verification runner for the wmrSim SDK sample plugins.

Copyright (C) 2026 宇集創新科技. All Rights Reserved.

用途：確認範例外掛與已安裝之 SDK 契約一致，並通過 PluginVerifier 的
介面／延遲檢驗。可作為客戶開發自有外掛時的參考測試骨架。

執行::

    python3 verify_examples.py            # 需先安裝 wmr_sim SDK / 核心
    python3 verify_examples.py --plain    # 使用同目錄範例，不依賴套件內建範例
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import Any, Tuple

HERE = pathlib.Path(__file__).resolve().parent

SAMPLES = (
    ("custom_astar_planner.py", "CustomerAStarPlanner", "verify_global_planner"),
    ("custom_rpp_controller.py", "CustomerRPPController", "verify_local_controller"),
    ("custom_traffic_manager.py", "CustomerTrafficManager", "verify_traffic_plugin"),
)


def load_sample(filename: str, class_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(
        pathlib.Path(filename).stem, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)()


def main() -> int:
    try:
        from wmr_sim.sdk import PluginVerifier
        from wmr_sim.sdk.dataclasses import (OccupancyGridData, Pose2D, Velocity2D)
    except Exception as exc:  # pragma: no cover
        print(f"[FAIL] 無法匯入 wmr_sim.sdk: {exc}")
        print("       請先安裝核心 .deb 與 SDK wheel，並 source /opt/ros/jazzy/setup.bash")
        return 2

    failures = 0
    print("=" * 70)
    print("wmrSim SDK 範例外掛自我驗證")
    print("=" * 70)

    for filename, class_name, verifier_name in SAMPLES:
        print(f"\n[VERIFY] {filename} :: {class_name}")
        try:
            plugin = load_sample(filename, class_name)
        except Exception as exc:
            print(f"  [FAIL] 載入失敗 -> {type(exc).__name__}: {exc}")
            failures += 1
            continue

        report = getattr(PluginVerifier, verifier_name)(plugin)
        print(f"  status        : {report.status.value}")
        print(f"  avg latency   : {report.avg_latency_ms:.3f} ms")
        print(f"  checks passed : {', '.join(report.checks_passed) or '-'}")
        if report.checks_failed:
            print(f"  checks failed : {', '.join(report.checks_failed)}")
        if report.error_message:
            print(f"  error         : {report.error_message}")
        if report.status.value != "VALID":
            failures += 1

    # --- 端到端功能煙霧測試 ------------------------------------------- #
    print("\n[SMOKE] 端到端功能煙霧測試")
    try:
        planner = load_sample("custom_astar_planner.py", "CustomerAStarPlanner")
        planner.initialize({})
        grid = OccupancyGridData(width=40, height=40, resolution_m=0.1,
                                 origin_x=0.0, origin_y=0.0, data=[0] * 1600)
        # 於 x=2.0 處築一道牆，僅留 y 缺口
        for row in range(40):
            if row != 20:
                grid.data[row * 40 + 20] = 100
        path = planner.plan_path(Pose2D(0.2, 0.2, 0.0, "L1"),
                                 Pose2D(3.5, 1.9, 0.0, "L1"), grid)
        assert len(path) >= 2, "planner 回傳路徑過短"
        # 路徑必須繞過牆（不得直接穿越 x=2.0 的障礙列）
        crossed = sum(1 for p in path if abs(p.x - 2.05) < grid.resolution_m
                      and abs(p.y - 0.2) < 0.3)
        print(f"  planner  : {len(path)} waypoints, 繞牆檢查 crossed={crossed}")
        assert crossed == 0, "planner 路徑穿越障礙"

        controller = load_sample("custom_rpp_controller.py", "CustomerRPPController")
        controller.initialize({})
        cmd = controller.compute_velocity(Pose2D(0.0, 0.0, 0.0, "L1"),
                                          Velocity2D(), path, 0.1)
        print(f"  controller: vx={cmd.vx:.3f} vtheta={cmd.vtheta_rad_s:.3f}")
        assert cmd.vx >= 0.0

        traffic = load_sample("custom_traffic_manager.py", "CustomerTrafficManager")
        traffic.initialize({})
        result = traffic.plan_traffic(
            "wmr_0",
            [Pose2D(0.0, 0.0, 0.0, "L1"), Pose2D(5.0, 0.0, 0.0, "L1")],
            {"wmr_0": Pose2D(0.0, 0.0, 0.0, "L1"),
             "wmr_1": Pose2D(3.0, 0.1, 3.14159, "L1")})
        print(f"  traffic  : encounter={result.encounter_type} "
              f"pass_side={result.pass_side} yield_to='{result.yield_to}' "
              f"wait={result.wait_duration_sec}")
        assert result.encounter_type == "head_on", "對向衝突未被偵測"
    except AssertionError as exc:
        print(f"  [FAIL] {exc}")
        failures += 1
    except Exception as exc:
        print(f"  [FAIL] {type(exc).__name__}: {exc}")
        failures += 1

    print("\n" + "=" * 70)
    if failures:
        print(f"結果: FAILED ({failures} 項)")
        return 1
    print("結果: ALL PASS — 範例外掛與 SDK 契約一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
