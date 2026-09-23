# wmrSim Plugin SDK

**企業級多機器人模擬與智慧車隊調度平台 — 外掛開發介面（Open Plugin SDK）**

Copyright (C) 2026 宇集創新科技. All Rights Reserved. Release V1.0

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](#授權)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![ROS 2 Jazzy](https://img.shields.io/badge/ROS%202-Jazzy-22314E.svg)](https://docs.ros.org/en/jazzy/)

本 repo 提供 **wmrSim 平台的外掛開發介面**：四大演算法插槽的抽象契約、
資料結構、Manifest JSON Schema、外掛驗證器、探索器，以及可直接執行的範例。

> **注意**：wmrSim **模擬核心**（導航、交通管制、電梯協同、視覺化引擎）為專有軟體，
> 以無原始碼 Bytecode 二進位形式獨立發行，**不在此 repo 中**。
> 本 repo 的介面已設計為可獨立開發與測試——不需要核心也能撰寫並驗證外掛。

---

## 四大外掛插槽

| 介面 | 用途 | `plugin_type` |
|---|---|---|
| `BaseGlobalPlanner` | 全域路徑規劃 | `GLOBAL_PLANNER` |
| `BaseLocalController` | 局部軌跡追蹤與避障 | `LOCAL_CONTROLLER` |
| `BaseTrafficPlugin` | 多車交通協調仲裁 | `TRAFFIC_MANAGER` |
| `BaseTaskManager` | 任務指派與排程 | `TASK_MANAGER` |

所有介面位於 `wmr_sim.sdk`：

```python
from wmr_sim.sdk import (
    BaseGlobalPlanner, BaseLocalController, BaseTrafficPlugin, BaseTaskManager,
    Pose2D, Velocity2D, OccupancyGridData,
    CustomerTrafficPlanResult, CustomerTaskPlanResult,
    PluginVerifier, PluginDiscoverer,
)
```

---

## 安裝

### 方式 A：使用本地 SDK 原始碼（開發用）

```bash
git clone https://github.com/<your-account>/<repo>.git
cd <repo>
export PYTHONPATH="$PWD/sdk:$PYTHONPATH"
python3 -c "import wmr_sim.sdk as s; print(s.__version__)"
```

### 方式 B：建置並安裝 wheel

```bash
cd sdk
python3 -m pip install build --break-system-packages   # 只需一次
python3 -m build --wheel
python3 -m pip install --break-system-packages dist/*.whl
```

---

## 快速開始

```bash
cd examples
python3 verify_examples.py
```

預期輸出：

```text
[VERIFY] custom_astar_planner.py :: CustomerAStarPlanner
  status        : VALID
[VERIFY] custom_rpp_controller.py :: CustomerRPPController
  status        : VALID
[VERIFY] custom_traffic_manager.py :: CustomerTrafficManager
  status        : VALID
結果: ALL PASS — 範例外掛與 SDK 契約一致
```

## Repo 結構

```text
.
├── sdk/wmr_sim/sdk/          外掛 SDK 原始碼（公開介面）
│   ├── interfaces.py         4 大抽象基底類別
│   ├── dataclasses.py        Pose2D / Velocity2D / OccupancyGridData / Plan 結果
│   ├── verifier.py           PluginVerifier：契約檢驗 + 延遲量測
│   ├── discovery.py          PluginDiscoverer：外掛探索
│   └── adapters.py           SDK ↔ runtime 橋接（需核心才會載入）
├── examples/                 3 支可執行範例 + Manifest + 自我驗證
├── plugins/schemas/          plugin_manifest_v1 / plugin_registration_v1 JSON Schema
├── manuals/                  操作說明書、插件寫作指南、範例說明
├── LICENSE                   專有軟體授權條款
├── COPYRIGHT                 著作權宣告
├── NOTICE                    第三方元件聲明
└── EULA.md                   終端使用者授權合約
```

## 文件

| 文件 | 內容 |
|---|---|
| [`manuals/PLUGIN_AUTHORING_GUIDE.md`](manuals/PLUGIN_AUTHORING_GUIDE.md) | 介面契約、信任邊界、Manifest、註冊、驗證、除錯 |
| [`manuals/EXAMPLES_GUIDE.md`](manuals/EXAMPLES_GUIDE.md) | 三個範例逐段解析與端到端練習 |
| [`manuals/OPERATION_MANUAL.md`](manuals/OPERATION_MANUAL.md) | 平台操作說明書（安裝、啟動、GUI、API） |
| [`plugins/schemas/`](plugins/schemas/) | 外掛宣告與註冊的正式 JSON Schema |

## 最小範例

```python
from typing import Any, Dict, List, Optional
from wmr_sim.sdk import BaseGlobalPlanner, OccupancyGridData, Pose2D


class MyPlanner(BaseGlobalPlanner):
    def initialize(self, config: Dict[str, Any]) -> None:
        self.weight = config.get("heuristic_weight", 1.0)

    def plan_path(self, start: Pose2D, goal: Pose2D,
                  grid_map: OccupancyGridData,
                  costmap: Optional[OccupancyGridData] = None) -> List[Pose2D]:
        return [start, goal]


from wmr_sim.sdk import PluginVerifier
print(PluginVerifier.verify_global_planner(MyPlanner()).status.value)  # VALID
```

## 常見陷阱

| 症狀 | 原因 |
|---|---|
| `'Pose2D' object has no attribute 'theta'` | 欄位是 **`theta_rad`** |
| `unexpected keyword argument 'linear'` | `Velocity2D` 欄位是 **`vx` / `vy` / `vtheta_rad_s`** |
| `ModuleNotFoundError: wmr_sim.task_management` | 你呼叫了 `SdkTrafficAdapter` / `SdkTaskAdapter`，這兩者需要核心 |

---

## 授權

本 SDK 為專有軟體（Proprietary），著作權屬 **宇集創新科技** 所有。

- **客戶外掛智財權**：你基於本 repo 公開介面所開發的演算法外掛，
  其智慧財產權**完全歸屬於你**。
- 禁止對核心二進位檔案進行逆向工程、反向編譯或反組譯。
- 完整條款見 [`LICENSE`](LICENSE) 與 [`EULA.md`](EULA.md)；
  第三方元件見 [`NOTICE`](NOTICE)。

Copyright (C) 2026 宇集創新科技. All Rights Reserved.
