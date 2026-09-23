# wmrSim 外掛範例說明 (Examples Guide)

**產品**：wmrSim 企業級多機器人模擬與智慧車隊調度平台
**版本**：V1.0 (Release Build 1.0.0)
**著作權**：Copyright (C) 2026 宇集創新科技. All Rights Reserved.

本文件逐段解析隨附於 `sdk/examples/` 的三個官方範例外掛，並說明如何
修改、驗證與註冊。所有範例皆已與 Release V1.0 的 SDK 契約對齊，並可
透過 `verify_examples.py` 自我驗證。

---

## 目錄

1. [範例清單與檔案對照](#1-範例清單與檔案對照)
2. [執行自我驗證](#2-執行自我驗證)
3. [範例一：A* 全域規劃器](#3-範例一a-全域規劃器)
4. [範例二：RPP 局部控制器](#4-範例二rpp-局部控制器)
5. [範例三：靠右通行交通管理器](#5-範例三靠右通行交通管理器)
6. [Manifest 範例解析](#6-manifest-範例解析)
7. [端到端實作練習](#7-端到端實作練習)
8. [修改範例的檢查清單](#8-修改範例的檢查清單)

---

## 1. 範例清單與檔案對照

| 範例檔案 | 類別 | 介面 | 外掛類型 | Manifest |
|---|---|---|---|---|
| `custom_astar_planner.py` | `CustomerAStarPlanner` | `BaseGlobalPlanner` | `GLOBAL_PLANNER` | `config/plugin_manifest.json` |
| `custom_rpp_controller.py` | `CustomerRPPController` | `BaseLocalController` | `LOCAL_CONTROLLER` | `config/plugin_manifest_rpp.json` |
| `custom_traffic_manager.py` | `CustomerTrafficManager` | `BaseTrafficPlugin` | `TRAFFIC_MANAGER` | `config/plugin_manifest_traffic.json` |
| `verify_examples.py` | — | 自我驗證 + 煙霧測試 | — | — |

---

## 2. 執行自我驗證

```bash
cd sdk/examples
source /opt/ros/jazzy/setup.bash          # 若已安裝核心
python3 verify_examples.py
```

若在原始碼樹中（未安裝核心）：

```bash
PYTHONPATH=/path/to/wmrSim/src/wmr_sim python3 verify_examples.py
```

**Release V1.0 預期輸出**：

```text
======================================================================
wmrSim SDK 範例外掛自我驗證
======================================================================

[VERIFY] custom_astar_planner.py :: CustomerAStarPlanner
  status        : VALID
  avg latency   : 0.084 ms
  checks passed : Interface Inheritance Check, Initialization Check, Path Execution Check

[VERIFY] custom_rpp_controller.py :: CustomerRPPController
  status        : VALID
  avg latency   : 0.007 ms
  checks passed : Interface Inheritance Check, Initialization Check, Velocity Calculation Check

[VERIFY] custom_traffic_manager.py :: CustomerTrafficManager
  status        : VALID
  avg latency   : 0.005 ms
  checks passed : Interface Inheritance Check, Initialization Check, Execution Latency Check

[SMOKE] 端到端功能煙霧測試
  planner  : 5 waypoints, 繞牆檢查 crossed=0
  controller: vx=0.100 vtheta=0.300
  traffic  : encounter=head_on pass_side=1 yield_to='' wait=0.0

======================================================================
結果: ALL PASS — 範例外掛與 SDK 契約一致
```

---

## 3. 範例一：A* 全域規劃器

檔案：`sdk/examples/custom_astar_planner.py`

### 3.1 契約實作

```python
class CustomerAStarPlanner(BaseGlobalPlanner):
    name = "customer_astar"
    version = "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        self.occupied_threshold = int(config.get("occupied_threshold", 50))
        self.allow_diagonal = bool(config.get("allow_diagonal", True))
        self.weight = float(config.get("heuristic_weight", 1.0))
        self.max_expansions = int(config.get("max_expansions", 200000))
        self._cancelled = False

    def plan_path(self, start: Pose2D, goal: Pose2D,
                  grid_map: OccupancyGridData,
                  costmap: Optional[OccupancyGridData] = None) -> List[Pose2D]:
        ...
```

**重點**：

- 簽章必須是 `plan_path(start, goal, grid_map, costmap=None)`，
  回傳 `List[Pose2D]`。
- 航向欄位為 `theta_rad`。
- `cancel_planning()` 為選用覆寫，供 runtime 中止長規劃。

### 3.2 座標轉換（世界 ↔ 網格）

```python
def _world_to_cell(self, grid, x, y):
    col = int((x - grid.origin_x) / grid.resolution_m)
    row = int((y - grid.origin_y) / grid.resolution_m)
    if 0 <= col < grid.width and 0 <= row < grid.height:
        return row, col
    return None
```

網格資料索引為 `grid.data[row * grid.width + col]`：

- `0–49`：可通行
- `>= 50`：障礙（門檻由 `occupied_threshold` 決定）
- `-1`：未知 → 本範例**保守視為不可通行**，避免規劃穿越未建圖區域

### 3.3 A* 核心與簡化

- 8 連通（`allow_diagonal` 可關閉為 4 連通）
- Octile 啟發式；`heuristic_weight > 1.0` 即為 weighted A*（較快、非最佳）
- `max_expansions` 防止無解時無限擴展
- 規劃完成後 `_simplify()` 移除共線中間點，只保留轉折處，降低 Nav2 下游負擔
- 起點／終點不可通行或無解時，退化為 `_straight_line()` 直線內插，
  **保證永遠回傳可用路徑**（至少 2 點，端點精確等於請求值）

### 3.4 煙霧測試（`verify_examples.py`）

測試在 `x = 2.0` 處築一道牆（僅 `y ≈ 1.9` 留缺口），要求：

```python
path = planner.plan_path(Pose2D(0.2, 0.2, 0.0, "L1"),
                         Pose2D(3.5, 1.9, 0.0, "L1"), grid)
assert len(path) >= 2
assert crossed == 0     # 不得直接穿越障礙列
```

實測得到 5 個航點且未穿牆（`crossed=0`），證明 A* 正確繞行。

---

## 4. 範例二：RPP 局部控制器

檔案：`sdk/examples/custom_rpp_controller.py`

### 4.1 契約實作

```python
class CustomerRPPController(BaseLocalController):
    def initialize(self, config):
        self.lookahead_dist  = float(config.get("lookahead_dist", 0.6))
        self.max_linear_vel  = float(config.get("max_linear_vel", 0.8))
        self.max_angular_vel = float(config.get("max_angular_vel", 1.2))
        self.max_accel       = float(config.get("max_accel", 1.0))
        self.max_alpha       = float(config.get("max_alpha", 3.0))

    def compute_velocity(self, current_pose, current_vel, target_path,
                         dt_sec, local_costmap=None, obstacles=None) -> Velocity2D:
        ...

    def reset(self) -> None:
        self._previous_cmd = Velocity2D(0.0, 0.0, 0.0)
```

### 4.2 控制律逐步說明

| 步驟 | 動作 |
|---|---|
| 1 | 前視點選擇：由近而遠找第一個距離 ≥ `lookahead_dist` 的航點；若無則取終點 |
| 2 | 終點判定：與終點距離 < `goal_tolerance` 即輸出零速 |
| 3 | 航向誤差：`yaw_err = normalize(atan2(dy, dx) - theta_rad)`，正規化至 `[-π, π]` |
| 4 | 角速度：比例控制 `ω = clamp(yaw_gain · yaw_err, ±max_angular_vel)` |
| 5 | 線速度：`v = max_linear_vel · max(0, cos(yaw_err))`，並於近端 `slowdown_radius` 內線性減速 |
| 6 | 障礙減速：最近障礙距離 < `avoidance_radius` 時按比例降速 |
| 7 | 速率限制：依 `max_accel` / `max_alpha` × `dt_sec` 限制每週期速度變化，避免突波 |

### 4.3 回傳值注意事項

```python
return Velocity2D(vx=max(0.0, v), vy=0.0, vtheta_rad_s=omega)
```

- 差速車：`vy` 固定 `0.0`
- **不可**使用 `Velocity2D(linear=..., angular=...)`：欄位名是
  `vx` / `vy` / `vtheta_rad_s`

---

## 5. 範例三：靠右通行交通管理器

檔案：`sdk/examples/custom_traffic_manager.py`

### 5.1 契約實作

```python
class CustomerTrafficManager(BaseTrafficPlugin):
    def plan_traffic(self, robot_id: str, requested_path: List[Pose2D],
                     fleet_states: Dict[str, Pose2D]) -> CustomerTrafficPlanResult:
```

### 5.2 演算法邏輯

1. **衝突偵測**：掃描 `fleet_states`，取 `detection_range_m` 內最近的車輛；
   若其方位角落在前方走廊 `corridor_half_angle_rad` 內才視為候選。
2. **遭遇分類** `_classify()`：

   | 條件 | 結果 |
   |---|---|
   | 對方航向與我差異 > `head_on_threshold_deg` | `head_on`（對向） |
   | 差異 < 45° | `same`（同向） |
   | 前方 60° 內且非同向 | `crossing`（交叉） |
   | 其他 | `none` |

3. **決策**：`robot_id` 字典序較小者優先（示範用；實務請改用任務
   `priority` 欄位）。需讓路時輸出 `yield_to` + `wait_duration_sec`；
   否則輸出 `pass_side = +1`（靠右通行）。

### 5.3 輸出對照 runtime

| SDK 輸出 | runtime `command` 欄位 |
|---|---|
| `accepted=False` | `sdk_rejected: true` |
| `wait_duration_sec` | `dispatch_after` |
| `pass_side` | `pass_side` |
| `yield_to` | `yield_to` |
| `encounter_type` | `encounter_type` |
| `reason` | `sdk_reason` |

由 `SdkTrafficAdapter` 轉為 `wmr_sim.traffic/v1` 的 `TrafficPlan`，
再經 `TrafficPlanValidator` 驗證（見插件寫作指南 §8）。

### 5.4 煙霧測試

```python
result = traffic.plan_traffic(
    "wmr_0",
    [Pose2D(0.0, 0.0, 0.0, "L1"), Pose2D(5.0, 0.0, 0.0, "L1")],
    {"wmr_0": Pose2D(0.0, 0.0, 0.0, "L1"),
     "wmr_1": Pose2D(3.0, 0.1, 3.14159, "L1")})     # 對向來車
assert result.encounter_type == "head_on"
```

實測 `encounter=head_on, pass_side=1`。

---

## 6. Manifest 範例解析

`sdk/examples/config/plugin_manifest.json`（A* 規劃器）：

```json
{
  "plugin_id": "customer_fast_astar",
  "name": "Customer High-Speed A* Planner",
  "version": "1.0.0",
  "plugin_type": "GLOBAL_PLANNER",
  "entrypoint": "custom_astar_planner:CustomerAStarPlanner",
  "capabilities": ["DIFFERENTIAL_DRIVE", "TIME_SCHEDULED_ROUTING"],
  "parameters": [
    { "name": "heuristic_weight", "type": "float", "default": 1.0,
      "description": "啟發式權重", "min_value": 1.0, "max_value": 5.0 },
    { "name": "allow_diagonal", "type": "bool", "default": true },
    { "name": "occupied_threshold", "type": "int", "default": 50 }
  ]
}
```

| 欄位 | 作用 |
|---|---|
| `entrypoint` | `模組:類別`；模組需在 `sys.path` 或探索路徑中 |
| `parameters` | 展開為 dict 傳入 `initialize(config)`；`min/max_value` 供 GUI 滑桿 |
| `capabilities` | 供 GUI／上層篩選與顯示 |

**注意**：`entrypoint` 的模組名要和檔名一致。若檔名為
`custom_astar_planner.py` 並置於探索路徑中，則模組名為 `custom_astar_planner`。

---

## 7. 端到端實作練習

以「自己的 A* 變體」為例，完整流程：

```bash
# 1) 準備外掛目錄並複製範例作為起點
mkdir -p ~/.wmr_sim/plugins
cp sdk/examples/custom_astar_planner.py ~/.wmr_sim/plugins/my_astar.py

# 2) 修改類別（建議改名 MyAStarPlanner 避免混淆）
#    - 於 initialize() 讀取自訂參數
#    - 於 plan_path() 實作你的演算法

# 3) 撰寫 manifest（複製範例後改 plugin_id / entrypoint）
cat > ~/.wmr_sim/plugins/my_astar.json << 'JSON'
{
  "plugin_id": "my_astar",
  "name": "My A* Planner",
  "version": "1.0.0",
  "plugin_type": "GLOBAL_PLANNER",
  "entrypoint": "my_astar:MyAStarPlanner"
}
JSON

# 4) 先做契約驗證
PYTHONPATH=~/.wmr_sim/plugins python3 - << 'PY'
import my_astar
from wmr_sim.sdk import PluginVerifier
print(PluginVerifier.verify_global_planner(my_astar.MyAStarPlanner()).status.value)
PY

# 5) 啟動模擬與網關
source /opt/ros/jazzy/setup.bash
ros2 launch wmr_sim multi_robot_sim.launch.py gui:=true &

# 6) 註冊外掛
curl -X POST http://127.0.0.1:8080/api/v1/plugins/register \
  -H "Content-Type: application/json" -d @~/.wmr_sim/plugins/my_astar.json

# 7) 於 GUI「控制器設定」下拉選單選擇 My A* Planner，或直接熱切換
ros2 topic pub --once /wmr_sim/switch_algorithm std_msgs/msg/String \
  '{data: "{\"robot_id\": \"wmr_0\", \"plugin_type\": \"GLOBAL_PLANNER\", \"plugin_id\": \"my_astar\"}"}'
```

---

## 8. 修改範例的檢查清單

- [ ] 類別繼承正確的 SDK base class（`BaseGlobalPlanner` / `BaseLocalController` /
      `BaseTrafficPlugin` / `BaseTaskManager`）
- [ ] 方法**簽章完全一致**（參數名與順序、回傳型別）
- [ ] `Pose2D` 使用 `theta_rad`（非 `theta`）
- [ ] `Velocity2D` 使用 `vx` / `vy` / `vtheta_rad_s`（非 `linear` / `angular`）
- [ ] `plan_path` 回傳 `List[Pose2D]`，且至少 2 點、端點精確
- [ ] `plan_traffic` 回傳 `CustomerTrafficPlanResult`（不是 dict）
- [ ] `initialize()` 對缺少的參數有預設值（不可直接索引 `config["x"]`）
- [ ] `entrypoint` 模組可被匯入（`PYTHONPATH` 或已安裝）
- [ ] manifest 通過 `plugin_manifest_v1.schema.json`
- [ ] 於設定中開啟 `allow_external_plugins`
- [ ] `PluginVerifier` 回報 `VALID`，平均延遲 < 50 ms

---

## 版權宣告

```text
wmrSim 企業級多機器人模擬與智慧車隊調度平台
Copyright (C) 2026 宇集創新科技. All Rights Reserved.
Release Version: V1.0
```

`sdk/examples/` 下之範例程式碼提供客戶作為開發參考使用；
客戶基於公開 `wmr_sim.sdk` 介面自行開發之外掛，其智財權歸客戶所有。
核心著作權見 `COPYRIGHT` / `LICENSE` / `EULA.md`。
