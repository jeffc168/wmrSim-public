# wmrSim Customer Plugin SDK 開發範例

Copyright (C) 2026 宇集創新科技. All Rights Reserved. (Release V1.0)

本目錄提供使用 `wmr-sim-sdk` 開發自訂移動機器人演算法外掛的**可執行**範例，
所有範例皆與 `PluginVerifier` 契約一致並附帶自我驗證腳本。

> ⚠️ 這裡的範例是「客戶外掛」範例，屬於客戶可自由修改的部分；
> wmrSim 核心本身以無原始碼 Bytecode 發行。

## 內容清單

| 檔案 | 實作介面 | 外掛類型 |
|---|---|---|
| `custom_astar_planner.py` | `BaseGlobalPlanner` | `GLOBAL_PLANNER` |
| `custom_rpp_controller.py` | `BaseLocalController` | `LOCAL_CONTROLLER` |
| `custom_traffic_manager.py` | `BaseTrafficPlugin` | `TRAFFIC_MANAGER` |
| `config/plugin_manifest.json` | A* 規劃器 manifest | — |
| `config/plugin_manifest_rpp.json` | RPP 控制器 manifest | — |
| `config/plugin_manifest_traffic.json` | 交管 manifest | — |
| `verify_examples.py` | 範例自我驗證 + 端到端煙霧測試 | — |

## 安裝 SDK

```bash
# 從發行包安裝
python3 -m pip install --break-system-packages wmr_sim_sdk-1.0.0-py3-none-any.whl
source /opt/ros/jazzy/setup.bash   # 核心已安裝時
```

或於原始碼樹直接使用：

```bash
export PYTHONPATH="$PWD/sdk:$PYTHONPATH"
```

## 驗證範例（建議先做）

```bash
cd sdk/examples
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
[SMOKE] 端到端功能煙霧測試
結果: ALL PASS — 範例外掛與 SDK 契約一致
```

## 開發步驟

### 1. 繼承 SDK 介面並實作契約方法

```python
from wmr_sim.sdk import BaseGlobalPlanner
from wmr_sim.sdk.dataclasses import OccupancyGridData, Pose2D

class MyPlanner(BaseGlobalPlanner):
    def initialize(self, config: dict) -> None:
        self.weight = config.get("weight", 1.0)

    def plan_path(self, start: Pose2D, goal: Pose2D,
                  grid_map: OccupancyGridData, costmap=None) -> list[Pose2D]:
        return [start, goal]
```

### 2. 撰寫 Manifest（遵循 `plugin_manifest_v1.schema.json`）

見 `config/plugin_manifest.json`。`entrypoint` 格式為 `模組:類別`。

### 3. 註冊外掛

```bash
# 方式 A：REST API 動態注入
curl -X POST http://127.0.0.1:8080/api/v1/plugins/register \
  -H "Content-Type: application/json" \
  -d @config/plugin_manifest.json

# 方式 B：放入探索路徑後由 PluginDiscoverer 自動掃描
mkdir -p ~/.wmr_sim/plugins && cp custom_astar_planner.py ~/.wmr_sim/plugins/
```

> 第三方模組需在設定中顯式開啟信任：`"allow_external_plugins": true`。

### 4. GUI 即時切換

開啟 `wmrSim Viz`，於左側「控制器設定」面板的 Planner / Controller 下拉選單
選取新註冊的外掛即可熱切換。

## 延伸閱讀

- `manuals/PLUGIN_AUTHORING_GUIDE.md`：完整介面契約、信任邊界與除錯
- `manuals/EXAMPLES_GUIDE.md`：範例逐段解析
- `plugins/schemas/plugin_manifest_v1.schema.json`：Manifest 正式 schema
