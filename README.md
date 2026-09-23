# wmrSim Plugin SDK

**企業級多機器人模擬與智慧車隊調度平台 — 外掛開發介面（Open Plugin SDK）**

Copyright (C) 2026 宇集創新科技. All Rights Reserved. Release V1.0

[![License: GPL-3.0 with Exception](https://img.shields.io/badge/License-GPL--3.0--Exception-blue.svg)](#授權與社群規範)
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

## GUI（3D 視覺化）

本 repo **不含**模擬核心，GUI 需先取得授權的核心套件（`ros-jazzy-wmr-sim-core`）。

### 環境需求

| 套件 | 用途 |
|---|---|
| `python3-pyqt5` | Qt 5 視窗框架 |
| `python3-opengl` | PyOpenGL — `viz/gl_widget.py` 的 3D 渲染，**必要** |
| `ros-jazzy-ament-index-python` | 解析 `share/wmr_sim` 資源路徑（URDF、fleet_config） |
| `ros-jazzy-sensor-msgs-py` | LiDAR／點雲訊息轉換 |
| `python3-matplotlib` | `run_sim --viz` 的 2D 繪圖模式（非 PyQt GUI） |

以上已列入核心套件的 `Depends`，以核心發行包的 `bash install.sh` 安裝會自動補齊。

### 啟動

```bash
source /opt/ros/jazzy/setup.bash

# 完整模擬 + GUI
ros2 launch wmr_sim multi_robot_sim.launch.py gui:=true

# 專案啟動腳本（gui:true / gui:false 切換）
bash launch_nav2.bash gui:true

# 只開視覺化介面（可指定初始監聽車輛）
ros2 run wmr_sim viz --robots wmr_0,wmr_1
```

需要 X11 / Wayland 桌面環境。純背景執行用 `gui:=false`；
無桌面環境（Ubuntu Server、容器、遠端主機）請見
[`manuals/OPERATION_MANUAL.md`](manuals/OPERATION_MANUAL.md)
的「無桌面環境（Headless / 遠端 X11）」小節。

### 缺件時的訊息

`viz` 啟動前會檢查相依，缺少時不會抛出 traceback：

```text
[wmrSim Viz] 缺少 GUI 執行期相依套件: python3-opengl
            請執行:  sudo apt-get install -y python3-opengl
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
├── tools/fetch_third_party.sh  第三方 ROS 2 套件一鍵取得工具
├── patches/                  第三方套件的 Jazzy 可攜性補丁
├── LICENSES/                 第三方授權全文
├── THIRD_PARTY.md            第三方元件來源、版本、授權、著作權人
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
| [`manuals/OPERATION_MANUAL.md`](manuals/OPERATION_MANUAL.md) | 操作說明書：安裝、GUI 環境設定與啟動、遠端 X11、API |
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
| `ModuleNotFoundError: No module named 'OpenGL'` | 已裝核心但缺 GUI 相依：`sudo apt-get install -y python3-opengl` |
| GUI 無法開啟 | 無 `DISPLAY`。請見 [`manuals/OPERATION_MANUAL.md`](manuals/OPERATION_MANUAL.md) 的遠端 X11 設定 |

---

## 第三方元件（一鍵取得）

wmrSim 在 Ubuntu 24.04 / ROS 2 Jazzy 上使用下列**第三方套件**。
這些**不是**宇集創新科技的著作，依其原始授權散布：

| 套件 | 授權 | 取得方式 |
|---|---|---|
| `dwb_core` / `dwb_critics` / `dwb_plugins` | BSD-3-Clause (Nav2) | `--apt` 或 `--bundle` |
| `costmap_converter` (+`_msgs`) | BSD-3-Clause (TU Dortmund) | `--bundle`（未收錄於官方 apt） |
| `teb_local_planner` / `teb_msgs` | BSD-3-Clause / Apache-2.0 (TU Dortmund) | `--bundle`（未收錄於官方 apt） |

### 一鍵使用

```bash
# 先看目前狀態
bash tools/fetch_third_party.sh --check

# 全自動：apt 裝 dwb_*，並下載 costmap_converter / teb_local_planner 原始碼
bash tools/fetch_third_party.sh --all --ws ~/my_ws

# 只裝 apt 可得的
bash tools/fetch_third_party.sh --apt

# 從上游 clone 並套用 Jazzy 補丁
bash tools/fetch_third_party.sh --upstream --ws ~/my_ws
```

腳本會自動由本 repo 的 `origin` 推導下載來源；必要時可覆寫：

```bash
WMR_THIRD_PARTY_URL=https://.../wmr_sim_third_party_v1.0.0.tar.gz \
  bash tools/fetch_third_party.sh --bundle
```

### 建置

```bash
source /opt/ros/jazzy/setup.bash
cd ~/my_ws && colcon build --symlink-install
```

> **授權合規**：第三方套件的著作權聲明與授權條款已完整保留，
> 並保存於 `~/my_ws/third_party_LICENSES/`。
> 完整來源、精確版本與在地補丁清單見 [`THIRD_PARTY.md`](THIRD_PARTY.md)。

## 授權與社群規範 (License & Community)

本公開倉庫（Plugin SDK 與範例演算法）依據 **GNU General Public License v3.0 (GPL-3.0)** 搭配 **宇集外掛動態載入例外條款 (Plugin Linking Exception)** 授權釋出。

### 1. 插件開源與後續開發義務 (Reciprocal Copyleft)
- 任何基於本 SDK 開發、擴充或衍生之外掛演算法（包含 Global Planner、Local Controller、Traffic Manager、Task Manager 等），**在散布、交付或提供給他人使用時，依法必須以 GPLv3（或後續版本）完整開源其原始碼**。
- 不得以任何閉源或專有形式發行衍生外掛，確保社群改進能持續回饋與共享。

### 2. 商業核心與 GUI 隔離保護宣告 (Plugin Linking Exception)
- 宇集創新科技官方發行之 **wmrSim 商業模擬核心引擎**（`ros-jazzy-wmr-sim-core`）與 **GUI 視覺化介面**（PyQt5 3D Desktop GUI、Web Dashboard）為獨立之專有商業軟體，**不在此公開 repo 中**。
- 宇集核心與 GUI 享有明確的 **Plugin Linking Exception** 豁免授權：核心動態加載依本 SDK 開發之 GPLv3 插件，**不構成衍生著作，核心與 GUI 100% 保持商業閉源專有**。
- 嚴格禁止對商業核心二進位檔案進行逆向工程、反向編譯或反組譯。

完整條款見 [`LICENSE`](LICENSE)；第三方套件宣告見 [`NOTICE`](NOTICE) 與 [`THIRD_PARTY.md`](THIRD_PARTY.md)。

Copyright (C) 2026 宇集創新科技. All Rights Reserved.
