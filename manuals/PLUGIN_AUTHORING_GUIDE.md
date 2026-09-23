# wmrSim 插件寫作指南 (Plugin Authoring Guide)

**產品**：wmrSim 企業級多機器人模擬與智慧車隊調度平台
**版本**：V1.0 (Release Build 1.0.0)
**著作權**：Copyright (C) 2026 宇集創新科技. All Rights Reserved.

本指南說明如何在不接觸 wmrSim 核心原始碼（核心為無原始碼 Bytecode 發行）的前提下，
使用官方 **Customer Plugin SDK**（`wmr_sim.sdk`）開發、註冊並驗證自訂演算法外掛。

---

## 目錄

1. [外掛架構與信任邊界](#1-外掛架構與信任邊界)
2. [環境準備](#2-環境準備)
3. [四大外掛插槽介面契約](#3-四大外掛插槽介面契約)
4. [資料結構 (SDK Dataclasses)](#4-資料結構-sdk-dataclasses)
5. [外掛 Manifest 規格](#5-外掛-manifest-規格)
6. [外掛探索與註冊](#6-外掛探索與註冊)
7. [runtime 設定檔（交管 / 任務）](#7-runtime-設定檔交管--任務)
8. [runtime 驗證規則（交管契約）](#8-runtime-驗證規則交管契約)
9. [驗證與除錯](#9-驗證與除錯)
10. [打包與佈署](#10-打包與佈署)
11. [常見錯誤](#11-常見錯誤)
12. [智財歸屬](#12-智財歸屬)

---

## 1. 外掛架構與信任邊界

```text
[客戶外掛模組] ──(SDK 介面 / Manifest)──> [PluginDiscoverer] ──> [PluginVerifier]
                                                                      │
[客戶外掛模組] ──(REST / ROS Topic)─────> [Plugin Registry] ──────────┤
                                                                      ▼
                              [GUI 下拉選單 / 熱切換 Algorithm Switched]
```

- 外掛**不需要**修改 wmrSim 核心；核心對外僅暴露 `wmr_sim.sdk` 公開介面。
- 外掛於**同一行程內**（in-process）被載入執行，由 adapter 橋接至 runtime 契約。

### 信任政策（安全預設）

| 情境 | 是否允許 | 設定 |
|---|---|---|
| 內建插件（`wmr_sim.*` 命名空間） | ✅ 預設允許 | — |
| 第三方模組（`type: python`） | ❌ 預設拒絕 | `"allow_external_plugins": true` |
| SDK 介面外掛（`type: sdk`） | ❌ 預設拒絕 | 必須 `"allow_external_plugins": true` |
| 單一插件白名單 | — | 該插件加 `"allow_external": true` |
| `type: process`（out-of-process） | ✅ | 既有 `ProcessTrafficManager` |

未開啟信任時，`entrypoint` 指向外部模組會直接拋出 `ValueError`。

---

## 2. 環境準備

```bash
# 1) 安裝核心與 SDK（見 OPERATION_MANUAL.md）
bash install.sh

# 2) 載入環境
source /opt/ros/jazzy/setup.bash

# 3) 確認 SDK 可匯入
python3 -c "import wmr_sim.sdk as s; print(s.__version__)"
```

若於原始碼樹開發（未安裝）：

```bash
export PYTHONPATH=/path/to/wmrSim/src/wmr_sim:$PYTHONPATH
```

---

## 3. 四大外掛插槽介面契約

所有介面定義於 `wmr_sim.sdk.interfaces`。**方法簽章必須完全一致**，
否則 `PluginVerifier` 會回報 `INVALID_INTERFACE` 或 `RUNTIME_ERROR`。

### 3.1 `BaseGlobalPlanner` — 全域路徑規劃器

```python
from typing import Any, Dict, List, Optional
from wmr_sim.sdk.dataclasses import OccupancyGridData, Pose2D
from wmr_sim.sdk.interfaces import BaseGlobalPlanner

class MyPlanner(BaseGlobalPlanner):
    def initialize(self, config: Dict[str, Any]) -> None:
        self.weight = config.get("heuristic_weight", 1.0)

    def plan_path(self,
                  start: Pose2D,
                  goal: Pose2D,
                  grid_map: OccupancyGridData,
                  costmap: Optional[OccupancyGridData] = None) -> List[Pose2D]:
        ...

    # 選用：runtime 要求中止長時間規劃時呼叫
    def cancel_planning(self) -> None:
        ...
```

| 方法 | 必要性 | 說明 |
|---|---|---|
| `initialize(config)` | 必填 | 由 runtime 傳入 manifest `parameters` 展開後之 dict |
| `plan_path(start, goal, grid_map, costmap=None)` | 必填 | 回傳世界座標航點 `List[Pose2D]`，至少 2 點 |
| `cancel_planning()` | 選用 | 設定中止旗標 |

⚠️ `Pose2D` 的航向欄位是 **`theta_rad`**（不是 `theta`）。
⚠️ 回傳的是 `List[Pose2D]`（不是 `dict`）。

### 3.2 `BaseLocalController` — 局部控制器

```python
from wmr_sim.sdk.dataclasses import (OccupancyGridData, Pose2D, Velocity2D)
from wmr_sim.sdk.interfaces import BaseLocalController

class MyController(BaseLocalController):
    def initialize(self, config: Dict[str, Any]) -> None:
        self.lookahead = config.get("lookahead_dist", 0.6)

    def compute_velocity(self,
                         current_pose: Pose2D,
                         current_vel: Velocity2D,
                         target_path: List[Pose2D],
                         dt_sec: float,
                         local_costmap: Optional[OccupancyGridData] = None,
                         obstacles: Optional[List[Pose2D]] = None) -> Velocity2D:
        ...

    def reset(self) -> None:
        ...
```

| 方法 | 必要性 | 說明 |
|---|---|---|
| `initialize(config)` | 必填 | 參數初始化 |
| `compute_velocity(...)` | 必填 | 每控制週期呼叫一次；`dt_sec` 為週期秒數 |
| `reset()` | 選用 | 新任務開始時清除積分項／快取 |

⚠️ 回傳 `Velocity2D(vx=..., vy=..., vtheta_rad_s=...)`。
差速車請將 `vy` 固定為 `0.0`。**沒有** `linear=` / `angular=` 參數
（`Twist2D` 只是 `Velocity2D` 的別名）。

### 3.3 `BaseTrafficPlugin` — 交通管理器

```python
from typing import Any, Dict, List
from wmr_sim.sdk.dataclasses import CustomerTrafficPlanResult, Pose2D
from wmr_sim.sdk.interfaces import BaseTrafficPlugin

class MyTraffic(BaseTrafficPlugin):
    def initialize(self, config: Dict[str, Any]) -> None:
        self.range_m = config.get("detection_range_m", 6.0)

    def plan_traffic(self,
                     robot_id: str,
                     requested_path: List[Pose2D],
                     fleet_states: Dict[str, Pose2D]) -> CustomerTrafficPlanResult:
        ...

    # 選用：動態時空租約
    def request_rolling_lease(self, robot_id: str, current_pose: Pose2D,
                              forward_path: List[Pose2D],
                              lease_radius_m: float = 3.0) -> bool:
        return True

    def release_lease(self, robot_id: str) -> None:
        ...
```

| 輸入 | 說明 |
|---|---|
| `robot_id` | 本次請求所屬車輛 |
| `requested_path: List[Pose2D]` | 密集 Nav2 路徑（含 `theta_rad`、`level`） |
| `fleet_states: Dict[robot_id, Pose2D]` | 全車隊即時位姿 |

| 輸出欄位 | 說明 |
|---|---|
| `accepted` | 是否接受此路由 |
| `modified_waypoints` | 選用；改寫後的航點 |
| `wait_duration_sec` | 對應 runtime 的 `dispatch_after`（延後派發秒數） |
| `pass_side` | `+1` 靠右 / `-1` 靠左 / `0` 不指定 |
| `yield_to` | 讓路對象 `robot_id` |
| `encounter_type` | `head_on` / `crossing` / `converging` / `same` / `none` |
| `reason` | 診斷用字串，會寫入 command metadata |
| `metadata` | 任意附加資訊 |

### 3.4 `BaseTaskManager` — 任務指派管理器

```python
from typing import Any, Dict, List
from wmr_sim.sdk.dataclasses import CustomerTaskPlanResult
from wmr_sim.sdk.interfaces import BaseTaskManager

class MyTasks(BaseTaskManager):
    def initialize(self, config: Dict[str, Any]) -> None: ...

    def plan_tasks(self,
                   pending_tasks: List[Dict[str, Any]],
                   robots: List[Dict[str, Any]]) -> CustomerTaskPlanResult:
        return CustomerTaskPlanResult(
            assignments={"task-1": "wmr_0"},
            wait_durations={"task-1": 0.0},
            reason="nearest idle robot")
```

`pending_tasks` 每筆欄位：`task_id`, `priority`, `level_id`, `map_id`,
`target`, `command`。
`robots` 每筆欄位：`robot_id`, `pose`, `battery_pct`, `busy`,
`current_task_id`, `level_id`, `map_id`。

---

## 4. 資料結構 (SDK Dataclasses)

完整清單見 `wmr_sim/sdk/dataclasses.py`；以下是撰寫外掛最常使用者。

| 類別 | 欄位 |
|---|---|
| `Pose2D` | `x: float`, `y: float`, `theta_rad: float = 0.0`, `level: str = "L1"` |
| `Velocity2D`（別名 `Twist2D`） | `vx: float = 0.0`, `vy: float = 0.0`, `vtheta_rad_s: float = 0.0` |
| `OccupancyGridData` | `width`, `height`, `resolution_m`, `origin_x`, `origin_y`, `data: List[int]`（`0–100` 佔用率，`-1` 未知） |
| `CustomerTrafficPlanResult` | 見 §3.3 |
| `CustomerTaskPlanResult` | `assignments: Dict[task_id, robot_id]`, `wait_durations: Dict[task_id, sec]`, `reason`, `metadata` |
| `PluginManifest` | `plugin_id`, `name`, `version`, `plugin_type`, `entrypoint`, `author`, `description`, `capabilities`, `parameters`, `ros_package` |
| `PluginValidationReport` | `status: PluginStatus`, `plugin_name`, `avg_latency_ms`, `error_message`, `checks_passed`, `checks_failed` |
| `OccupancyGridData` 索引 | `data[row * width + col]`，`col = (x - origin_x)/resolution_m`，`row = (y - origin_y)/resolution_m` |

列舉：

- `PluginType`: `GLOBAL_PLANNER` / `LOCAL_CONTROLLER` / `TRAFFIC_MANAGER` / `TASK_MANAGER`
- `PluginStatus`: `VALID` / `INVALID_INTERFACE` / `RUNTIME_ERROR` / `TIMEOUT`
- `PluginCapability`: `DIFFERENTIAL_DRIVE`, `OMNIDIRECTIONAL`, `DYNAMIC_OBSTACLE_AVOIDANCE`,
  `TIME_SCHEDULED_ROUTING`, `MULTI_FLOOR_ROUTING`, `ROLLING_LEASE`,
  `TASK_ASSIGNMENT`, `RECIPROCAL_AVOIDANCE`

---

## 5. 外掛 Manifest 規格

正式 schema：`plugins/schemas/plugin_manifest_v1.schema.json`（`$id: wmr_sim.plugin.manifest/v1`）。

### 必填欄位

| 欄位 | 型別 | 限制 |
|---|---|---|
| `plugin_id` | string | `^[a-z0-9_-]+$`，全域唯一 |
| `name` | string | 顯示於 GUI 下拉選單 |
| `version` | string | 語意化版本，`^\d+\.\d+\.\d+` |
| `plugin_type` | enum | 四種 `PluginType` 之一 |
| `entrypoint` | string | `^[a-zA-Z0-9_.]+(:[a-zA-Z0-9_]+)?$`，即 `模組:類別` |

### 選填欄位

| 欄位 | 說明 |
|---|---|
| `author` | 開發者／組織 |
| `description` | 演算法說明 |
| `capabilities` | `PluginCapability` 陣列 |
| `parameters` | `{name, type, default, description, min_value?, max_value?}`；`type` ∈ `float/int/bool/str` |
| `ros_package` | 若來自 ROS 2 套件，填套件名 |

`parameters` 會被展開為 dict 傳入 `initialize(config)`；`min_value`/`max_value`
可供 GUI 產生滑桿範圍。

範例見 `sdk/examples/config/plugin_manifest*.json`。

---

## 6. 外掛探索與註冊

`PluginDiscoverer`（`wmr_sim.sdk.discovery`）依下列順序掃描：

1. `~/.wmr_sim/plugins/`
2. `./plugins/`（當前工作目錄）
3. `$WMR_SIM_PLUGIN_PATH`（以 `:` 分隔之多路徑）
4. ament_index 資源類別 `wmr_sim_plugins`（`RESOURCE_INDEX_CATEGORY`）

### 方式 A：REST API 動態注入

```bash
curl -X POST http://127.0.0.1:8080/api/v1/plugins/register \
  -H "Content-Type: application/json" \
  -d @sdk/examples/config/plugin_manifest.json

curl -s http://127.0.0.1:8080/api/v1/plugins | python3 -m json.tool
```

### 方式 B：ROS 2 Topic 熱切換

```bash
ros2 topic pub --once /wmr_sim/switch_algorithm std_msgs/msg/String \
  '{data: "{\"robot_id\": \"wmr_0\", \"plugin_type\": \"GLOBAL_PLANNER\", \"plugin_id\": \"customer_fast_astar\"}"}'
```

### 方式 C：設定檔宣告

於 `traffic_manager.json` / `task_manager.json` 的 `plugins.<name>` 指向
entrypoint，並把 `active` 設為該名稱（見 §7）。

### 方式 D：ROS 2 套件自動探索

於套件 `share/<pkg>/resource_index/wmr_sim_plugins/manifest.json` 放置 manifest。

---

## 7. runtime 設定檔（交管 / 任務）

`traffic_manager.json`：

```json
{
  "schema_version": 1,
  "api_version": "wmr_sim.traffic/v1",
  "active": "customer_traffic",
  "default": "default_priority",
  "allow_external_plugins": true,
  "plugins": {
    "default_priority": {
      "enabled": true, "type": "builtin",
      "entrypoint": "wmr_sim.traffic.plugins.default_priority:DefaultPriorityTrafficManager"
    },
    "customer_traffic": {
      "enabled": true, "type": "sdk",
      "entrypoint": "custom_traffic_manager:CustomerTrafficManager",
      "parameters": { "detection_range_m": 8.0, "keep_right": true }
    }
  }
}
```

`type` 可為：`builtin`（核心內建）、`python`（實作 runtime 介面）、
`sdk`（實作 SDK 介面，經 adapter 橋接）、`process`（out-of-process）。

`task_manager.json` 同理，`api_version` 為 `wmr_sim.task/v1`。

---

## 8. runtime 驗證規則（交管契約）

`TrafficPlanValidator`（核心內）會拒絕以下情形，外掛必須遵守：

- `api_version` / `epoch` 不符，或 plan 已過期
- 遺漏或增加命令、重複 `task_id`、改動 `robot_id`
- 改動 `level_id` / `map_id` / 命令類型 / 宣告目的地 / 最終 waypoint
- `dispatch_after` 非有限值或超過 `max_dispatch_delay_sec`
- 時空碰撞（以 `nominal_speed` 取樣，clearance = `r1 + r2 + safety_distance`）

> **關鍵觀念**：外掛的職責是決定「**何時、如何派發既有命令**」
> （delay／讓路提示／改寫 waypoint），而**不是**更換任務目的地。

---

## 9. 驗證與除錯

`PluginVerifier`（`wmr_sim.sdk.verifier`）提供四個靜態檢驗：

```python
from wmr_sim.sdk import PluginVerifier

report = PluginVerifier.verify_global_planner(MyPlanner(), num_benchmark_runs=10)
report = PluginVerifier.verify_local_controller(MyController())
report = PluginVerifier.verify_traffic_plugin(MyTraffic())
report = PluginVerifier.verify_task_manager(MyTasks())

print(report.status.value, report.avg_latency_ms, report.checks_failed)
```

檢驗項目：介面繼承 → `initialize({})` → 以 mock 輸入執行 → 平均延遲。
**延遲 SLA 為 50 ms**，超過會被標記為 `TIMEOUT`。

官方範例附自我驗證腳本，可直接作為骨架：

```bash
cd sdk/examples && python3 verify_examples.py
```

除錯建議：

1. 先看 log：`~/.wmr_sim/logs/`、`~/.ros/log/`
2. 用 `PluginVerifier` 確認契約與延遲
3. 檢查信任設定是否開啟
4. 確認 `entrypoint` 模組可被 Python 匯入（`PYTHONPATH` / 已 pip 安裝）

---

## 10. 打包與佈署

### 10.1 純 Python 模組

```bash
mkdir -p ~/.wmr_sim/plugins
cp my_planner.py ~/.wmr_sim/plugins/
```

### 10.2 Python Wheel

```bash
python3 -m pip wheel . --no-deps -w dist/
python3 -m pip install --break-system-packages dist/my_plugin-1.0.0-py3-none-any.whl
```

### 10.3 ROS 2 套件（標準目錄）

```text
my_wmr_plugins/
├── config/my_plugins.json          # Manifest
├── my_wmr_plugins/__init__.py
├── my_wmr_plugins/custom_astar_planner.py
├── package.xml
├── setup.py
└── setup.cfg
```

於 `setup.py` 的 `data_files` 將 manifest 安裝至
`share/<pkg>/resource_index/wmr_sim_plugins/` 即可被 ament_index 探索。

---

## 11. 常見錯誤

| 錯誤 | 原因 | 修正 |
|---|---|---|
| `AttributeError: 'Pose2D' object has no attribute 'theta'` | 用了舊欄位名 | 改用 `theta_rad` |
| `TypeError: Velocity2D.__init__() got an unexpected keyword argument 'linear'` | 用了舊參數名 | 改用 `vx=` / `vtheta_rad_s=` |
| `ValueError` on load | 外部模組未授權 | 設 `allow_external_plugins: true` |
| `INVALID_INTERFACE` | 未繼承正確 base class | 繼承 `BaseGlobalPlanner` 等 |
| `RUNTIME_ERROR` | 方法簽章不符 | 對照 §3 修正參數 |
| `TIMEOUT` | 單次呼叫 > 50 ms | 最佳化演算法；長規劃改用 `cancel_planning` 配合 |
| 外掛未出現在下拉選單 | 未註冊／未探索到 | 檢查 `/api/v1/plugins` 與探索路徑 |
| `dispatch_after` 被拒 | 超過 `max_dispatch_delay_sec` | 縮小 `wait_duration_sec` |

---

## 12. 智財歸屬

- 客戶基於公開 `wmr_sim.sdk` 介面自行開發之外掛、演算法與業務邏輯，
  其智慧財產權**完整歸屬於客戶**。
- 外掛以動態載入方式與核心隔離；授權方不對客戶外掛原始碼主張任何權利。
- 客戶不得以非公開方式 Hook、繞過或破壞核心之驗證、授權與安全機制。
- wmrSim 核心著作權：Copyright (C) 2026 宇集創新科技. All Rights Reserved.

完整條款見 `LICENSE` 與 `EULA.md`。
