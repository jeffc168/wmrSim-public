# wmrSim 操作說明書 (Operation Manual)

**產品**：wmrSim 企業級多機器人模擬與智慧車隊調度平台
**版本**：V1.0 (Release Build 1.0.0)
**著作權**：Copyright (C) 2026 宇集創新科技. All Rights Reserved.
**適用平台**：Ubuntu 24.04 LTS (Noble) / ROS 2 Jazzy Jalisco / Python 3.12

---

## 目錄

1. [系統需求](#1-系統需求)
2. [發行包結構](#2-發行包結構)
3. [安裝](#3-安裝)
4. [安裝驗證](#4-安裝驗證)
5. [啟動模擬](#5-啟動模擬)
6. [圖形介面操作](#6-圖形介面操作)
7. [命令列節點清單](#7-命令列節點清單)
8. [設定檔說明](#8-設定檔說明)
9. [HTTP 網關 API](#9-http-網關-api)
10. [啟用自訂外掛](#10-啟用自訂外掛)
11. [日誌與診斷](#11-日誌與診斷)
12. [解除安裝](#12-解除安裝)
13. [常見問題](#13-常見問題)
14. [版權宣告](#14-版權宣告)

---

## 1. 系統需求

| 項目 | 需求 |
|---|---|
| 作業系統 | Ubuntu 24.04 LTS (amd64) |
| ROS 2 | Jazzy Jalisco（安裝於 `/opt/ros/jazzy`） |
| Python | 3.12 |
| 顯示 | X11/Wayland 桌面（使用 GUI 時）；純背景運行可免 |
| 硬體 | 4 核心 CPU / 8 GB RAM 以上（建議 16 GB） |
| 磁碟 | 約 500 MB（含相依套件） |

核心套件之相依項目已宣告於 Debian control 檔，安裝時以 `apt-get install -f` 自動補齊。

---

## 2. 發行包結構

解壓後目錄如下：

```text
wmr_sim_v1.0.0_ubuntu24.04_amd64/
├── README.md                 快速開箱說明
├── LICENSE                   專有軟體授權條款
├── COPYRIGHT                 著作權宣告（宇集創新科技, 2026, V1.0）
├── NOTICE                    第三方元件授權聲明
├── EULA.md                   終端使用者授權合約
├── install.sh                一鍵安裝（連結至 scripts/install.sh）
├── verify.sh                 安裝診斷（連結至 scripts/verify.sh）
├── packages/
│   └── ros-jazzy-wmr-sim-core_1.0.0_amd64.deb   核心（純 Bytecode，無原始碼）
├── sdk/
│   ├── wmr_sim_sdk-1.0.0-py3-none-any.whl       客戶端外掛 SDK
│   └── examples/                                外掛開發範例
├── plugins/
│   └── schemas/              外掛宣告 JSON Schema（對外開放契約）
├── manuals/                  本操作與插件文件
├── config/                   生產環境設定樣板
├── scripts/                  安裝與診斷腳本
└── release_manifest.json     發行檔案 SHA-256 完整性清單
```

> **注意**：核心內部技術文件（`docs/`）不對外開放，不包含於發行包中。
> 客戶可取得者為 `manuals/` 下之操作、插件寫作與範例說明文件。

---

## 3. 安裝

### 3.1 一鍵安裝（建議）

```bash
tar -xzf wmr_sim_v1.0.0_ubuntu24.04_amd64.tar.gz
cd wmr_sim_v1.0.0_ubuntu24.04_amd64
bash install.sh
```

`install.sh` 依序執行：

1. 檢查 OS 版本與 `/opt/ros/jazzy` 是否存在
2. 定位並驗證核心 `.deb` 與 SDK `.whl`
3. `sudo dpkg -i` 安裝核心，必要時以 `apt-get install -f` 補相依
4. `pip install` 安裝客戶端 SDK
5. 自動執行 `verify.sh` 診斷

### 3.2 手動安裝

```bash
# 核心
sudo dpkg -i packages/ros-jazzy-wmr-sim-core_1.0.0_amd64.deb
sudo apt-get install -f -y

# 客戶端 SDK（Ubuntu 24.04 採 PEP 668，需 --break-system-packages）
python3 -m pip install --no-deps --break-system-packages \
    sdk/wmr_sim_sdk-1.0.0-py3-none-any.whl
```

### 3.3 安裝後環境載入

```bash
source /opt/ros/jazzy/setup.bash
```

建議寫入 `~/.bashrc`：

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```

---

## 4. 安裝驗證

```bash
bash verify.sh
```

檢查項目：

| 檢查 | 通過條件 |
|---|---|
| Debian 套件狀態 | `ros-jazzy-wmr-sim-core` 已安裝並顯示版本 |
| **無原始碼保護** | `/opt/ros/jazzy/lib/python3.12/site-packages/wmr_sim` 下 `.py` 數量為 **0** |
| ament_index 註冊 | `/opt/ros/jazzy/share/ament_index/resource_index/packages/wmr_sim` 存在 |
| 可執行節點 | 7 個核心 CLI 均可執行 |
| SDK 匯入 | `import wmr_sim.sdk` 成功 |

手動確認：

```bash
python3 -c "import wmr_sim; print(wmr_sim.__version__, wmr_sim.__copyright__)"
find /opt/ros/jazzy/lib/python3.12/site-packages/wmr_sim -name "*.py"   # 應無輸出
dpkg -l | grep ros-jazzy-wmr-sim-core
```

預期輸出：

```text
1.0.0 Copyright (C) 2026 宇集創新科技. All Rights Reserved.
```

---

## 5. 啟動模擬

### 5.1 標準 ROS 2 launch

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch wmr_sim multi_robot_sim.launch.py gui:=true
```

| 參數 | 說明 | 預設 |
|---|---|---|
| `gui:=true` | 啟動 3D 視覺化圖形介面 | `true` |
| `gui:=false` | 純背景（CI／壓測用） | — |

### 5.2 專案啟動腳本

```bash
bash launch_nav2.bash gui:true     # 含 GUI
bash launch_nav2.bash gui:false    # 無介面
```

啟動後會拉起：Nav2 導航堆疊、多車里程計模擬、LiDAR／深度相機模擬、地圖發布、交通協調器、整合網關與視覺化節點。

### 5.3 選擇性啟動單一節點

```bash
ros2 run wmr_sim viz                  # 視覺化
ros2 run wmr_sim fleet_server         # 車隊管理伺服器
ros2 run wmr_sim integration_gateway  # HTTP 整合網關
ros2 run wmr_sim plugin_registry      # 外掛註冊中心
```

---

## 6. 圖形介面操作

開啟 `wmrSim Viz` 視窗後：

1. **選擇機器人**：點選左側機器人清單（如 `wmr_0`）。
2. **控制器設定面板**：
   - **全域規劃器 (Planner)** 下拉選單：切換已註冊之規劃演算法
   - **局部控制器 (Controller)** 下拉選單：切換已註冊之控制演算法
   - 選取後即時熱切換，無需重啟
3. **3D 視覺與影像演算法浮動面板**（可拖曳為獨立視窗）：
   - **近處 (3-10 m) 障礙物辨識（輔助避障）**：勾選後發布 `/{robot_id}/vision/obstacles`
   - **空間已知 Tag 辨識（輔助定位）**：進入視錐時發布 `/{robot_id}/vision/tag_pose`
   - 預設皆為關閉；開關狀態依車輛分別記憶
4. **底盤模式 (HAL)**：`sim` 純模擬 / `real` 對接實體 AGV2W 邊緣網關

命令列等效操作：

```bash
# 熱切換 wmr_0 之影像演算法
ros2 topic pub --once /wmr_0/vision/config std_msgs/msg/String \
  '{data: "{\"enable_obstacle_detection\": true, \"enable_tag_localization\": true}"}'

# 熱切換演算法外掛
ros2 topic pub --once /wmr_sim/switch_algorithm std_msgs/msg/String \
  '{data: "{\"robot_id\": \"wmr_0\", \"plugin_type\": \"GLOBAL_PLANNER\", \"plugin_id\": \"customer_fast_astar\"}"}'
```

---

## 7. 命令列節點清單

安裝後可於 `/opt/ros/jazzy/bin` 與 `/opt/ros/jazzy/lib/wmr_sim` 取得：

| 指令 | 說明 |
|---|---|
| `run_sim` | 模擬器主程式 |
| `viz` | 3D 視覺化介面 |
| `fleet_server` | 車隊管理伺服器 |
| `fleet_client` | 車隊管理客戶端 |
| `elevator_coordinator` | 跨樓層電梯協調節點 |
| `odometry_sim` | 里程計／底盤 HAL 模擬 |
| `lidar_sim` | 2D LiDAR 模擬 |
| `depth_camera_sim` | 3D 深度相機模擬 |
| `map_publisher` | 地圖發布 |
| `clock_publisher` | 模擬時鐘 |
| `amcl_diagnostics` | 定位診斷 |
| `scenario_runner` | 場景劇本執行器 |
| `integration_gateway` | HTTP/REST 整合網關 |
| `plugin_registry` | 動態外掛註冊中心 |

以 ROS 2 方式執行：`ros2 run wmr_sim <指令>`

---

## 8. 設定檔說明

安裝後設定檔位於 `/opt/ros/jazzy/share/wmr_sim/config/`：

| 檔案 | 用途 |
|---|---|
| `fleet_config.json` / `fleet_config.yaml` | 車隊成員、初始位姿、底盤參數、`hal_mode` |
| `building.json` | 樓層、區域、電梯與管理區定義 |
| `integration_gateway.yaml` | 網關監聽埠、授權與路由 |
| `traffic_manager.json` | 交通管理器外掛選擇與參數 |
| `cyclonedds.xml` | DDS 設定 |

修改現場設定時，建議複製至 `~/.wmr_sim/config/` 或於 launch 時以參數覆寫，避免升級時被覆蓋。

關鍵欄位 `hal_mode`：

```json
{ "hal_mode": "sim" }    // 純模擬差速積分
{ "hal_mode": "real" }   // MQTT 對接 AGV2W 實體底盤
```

實體模式 MQTT 主題：

| 方向 | 主題 |
|---|---|
| 下發控制 | `wmrsim/v1/site1/edge/robots/<robot_id>/fleet_command` |
| 狀態回傳 | `wmrsim/v1/site1/edge/robots/<robot_id>/fleet_state` |

---

## 9. HTTP 網關 API

啟動 `integration_gateway` 後，預設監聽 `127.0.0.1:8080`。

| 方法 | 路徑 | 說明 |
|---|---|---|
| `GET` | `/api/v1/health` | 健康檢查 |
| `GET` | `/api/v1/plugins` | 列出已註冊外掛 |
| `POST` | `/api/v1/plugins/register` | 註冊外掛 |
| `DELETE` | `/api/v1/plugins/{plugin_id}` | 移除外掛 |
| `GET` | `/api/v1/fleet/state` | 車隊即時狀態 |
| `POST` | `/api/v1/tasks` | 下發任務 |

範例：

```bash
curl -s http://127.0.0.1:8080/api/v1/health
curl -s http://127.0.0.1:8080/api/v1/plugins | python3 -m json.tool
```

---

## 10. 啟用自訂外掛

最快路徑（詳見 `PLUGIN_AUTHORING_GUIDE.md`）：

```bash
# 1. 安裝 SDK 後，將外掛模組放到探索路徑
mkdir -p ~/.wmr_sim/plugins
cp my_planner.py ~/.wmr_sim/plugins/

# 2. 註冊（REST）
curl -X POST http://127.0.0.1:8080/api/v1/plugins/register \
  -H "Content-Type: application/json" \
  -d '{"plugin_id":"my_planner","name":"My Planner","version":"1.0.0",
       "plugin_type":"GLOBAL_PLANNER",
       "entrypoint":"my_planner:MyPlanner"}'

# 3. 於 GUI 下拉選單選擇，或設定 traffic_manager.json 的 active
```

外掛探索路徑優先序：`~/.wmr_sim/plugins/` → `./plugins/` → `$WMR_SIM_PLUGIN_PATH` → ament_index 類別 `wmr_sim_plugins`。

> **信任邊界**：第三方模組預設被拒絕。需於設定中顯式開啟
> `"allow_external_plugins": true`（或單一插件 `"allow_external": true`）。
> 詳見插件寫作指南第 1 節。

---

## 11. 日誌與診斷

| 位置 | 內容 |
|---|---|
| `~/.wmr_sim/logs/` | 模擬器應用日誌（自動保留最新 50 筆） |
| `~/.ros/log/` | ROS 2 節點日誌 |
| `<workspace>/log/` | colcon/launch 輸出 |

```bash
# 最新應用日誌
tail -n 100 "$(ls -t ~/.wmr_sim/logs/wmr_sim_*.log | head -n 1)"

# 檢查日誌輪轉是否合規（應 <= 50）
ls -1 ~/.wmr_sim/logs | wc -l

# ROS 2 節點清單與主題
ros2 node list
ros2 topic list
ros2 topic hz /wmr_0/scan
```

---

## 12. 解除安裝

```bash
sudo dpkg -r ros-jazzy-wmr-sim-core
python3 -m pip uninstall -y wmr-sim-sdk
rm -rf ~/.wmr_sim
```

---

## 13. 常見問題

| 症狀 | 原因 | 處理 |
|---|---|---|
| `ros2 launch` 找不到 `wmr_sim` | 未載入 ROS 環境 | `source /opt/ros/jazzy/setup.bash` |
| 匯入 `wmr_sim` 失敗 | 核心 `.deb` 未安裝 | `sudo dpkg -i packages/*.deb && sudo apt-get install -f -y` |
| 外掛未出現在下拉選單 | 未註冊或信任未開啟 | 檢查 `/api/v1/plugins`；設定 `allow_external_plugins: true` |
| 外掛載入拋出 `ValueError` | entrypoint 指向外部模組但未授權 | 同上，顯式開啟信任 |
| GUI 無法開啟 | 無 `DISPLAY` | 以 `gui:=false` 執行，或設定 `DISPLAY=:0` |
| `pip install` 被 PEP 668 阻擋 | Ubuntu 24.04 系統 Python | 加上 `--break-system-packages` |
| 交通死鎖 | 起點 5 m 內交管鎖定 | 已內建「啟動區 5 m 內不執行交管」保護；確認 `initial_launch_zone` |

---

## 14. 版權宣告

```text
wmrSim 企業級多機器人模擬與智慧車隊調度平台
Copyright (C) 2026 宇集創新科技. All Rights Reserved.
Release Version: V1.0
```

本軟體核心以無原始碼 Bytecode (.pyc) 形式發行。嚴禁逆向工程、反向編譯或反組譯。
第三方元件授權見 `NOTICE`；完整授權條款見 `LICENSE` 與 `EULA.md`。
