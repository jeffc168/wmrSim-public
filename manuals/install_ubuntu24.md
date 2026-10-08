# wmrSim-public 本地安裝與驗證指南 (Ubuntu 24.04)

本指南說明如何從 GitHub 下載 `wmrSim-public` 專案內容，並在本地 **Ubuntu 24.04 LTS (Noble Numbat)** 環境中完成安裝與驗證。

> **文件定位**：本文件是**外掛 SDK 開發者**的本地安裝與驗證指南，發布後為公開庫的 `manuals/install_ubuntu24.md`。
> 商業版模擬器的一般使用者安裝請看公開庫根目錄的 `install.md`（商業版一鍵安裝指南）。

---

## 1. 系統需求與前置安裝 (Prerequisites)

在開始前，請確保您的系統為 **Ubuntu 24.04 LTS (amd64)**，並安裝基礎開發工具與 Python 相依：

```bash
# 更新系統套件庫清單
sudo apt update

# 安裝 Git、Python 3 及套件建置工具
sudo apt install -y git python3 python3-pip python3-setuptools python3-wheel python3-numpy
```

---

## 2. 下載專案 (Clone Repository)

使用 `git clone` 將公開倉庫下載至本地：

```bash
# 複製公開倉庫
git clone https://github.com/jeffc168/wmrSim-public.git

# 進入專案目錄
cd wmrSim-public
```

---

## 3. 建置並安裝 Plugin SDK

本公開專案提供獨立的演算法外掛開發工具包（`wmr_sim.sdk`）。請選擇以下任一種方式安裝：

### 方式 A：建置 Wheel 並安裝至系統（建議：正式環境）

```bash
cd sdk

# 建置獨立的 Python Wheel 套件
python3 setup.py bdist_wheel

# 安裝產出的 Wheel 套件（Ubuntu 24.04 請加上 --break-system-packages，或在 Python 虛擬環境中安裝）
pip install --break-system-packages dist/*.whl

# 返回專案根目錄
cd ..
```

### 方式 B：可編輯模式安裝（建議：需修改或追蹤 SDK 源碼時）

```bash
pip install -e ./sdk --break-system-packages
```

---

## 4. 快速驗證 (Self-Verification)

安裝完成後，執行隨附的範例外掛合約自驗證腳本，驗證全域規劃器（Global Planner）、局部控制器（Local Controller）與交通管理器（Traffic Manager）之介面契約與延遲：

```bash
cd examples
python3 verify_examples.py
```

### 預期通過輸出：

```text
======================================================================
wmrSim SDK 範例外掛自我驗證
======================================================================

[VERIFY] custom_astar_planner.py :: CustomerAStarPlanner
  status        : VALID
  avg latency   : 0.045 ms
  checks passed : Interface Inheritance Check, Initialization Check, Path Execution Check

[VERIFY] custom_rpp_controller.py :: CustomerRPPController
  status        : VALID
  avg latency   : 0.007 ms
  checks passed : Interface Inheritance Check, Initialization Check, Velocity Calculation Check

[VERIFY] custom_traffic_manager.py :: CustomerTrafficManager
  status        : VALID
  avg latency   : 0.067 ms
  checks passed : Interface Inheritance Check, Initialization Check, Execution Latency Check

[SMOKE] 端到端功能煙霧測試
  planner  : 5 waypoints, 繞牆檢查 crossed=0
  controller: vx=0.100 vtheta=0.300
  traffic  : encounter=head_on pass_side=1 yield_to='' wait=0.0

======================================================================
結果: ALL PASS — 範例外掛與 SDK 契約一致
```

> **免安裝快速驗證**：若剛 clone 專案尚未執行 `pip install`，直接在 `examples/` 目錄執行 `python3 verify_examples.py`，腳本內建自適應尋徑機制，會自動優先引用同專案下的 `../sdk` 原始碼完成測試。

---

## 5. 取得第三方 ROS 2 導航相依

> ⚠️ **這是必要步驟（非選用）**：商業版核心以 `<exec_depend>` 宣告 `teb_local_planner`，
> 並在 `plugin_registry` 註冊；`wmrsim doctor` 亦強制檢查 `teb_local_planner` 與
> `costmap_converter`。兩者**不在 ROS 官方 apt 內**。

需要 7 個套件：`costmap_converter_msgs`、`costmap_converter`、`teb_msgs`、
`teb_local_planner`、`dwb_core`、`dwb_critics`、`dwb_plugins`。

**方式 A：使用官方第三方原始碼包（含 Jazzy 可攜性補丁）**

> ⚠️ 原始碼包內附的 `install.sh` 以 `set -euo pipefail` 執行後才 source ROS setup 腳本，
> **與 ROS 2 Jazzy 不相容**（會出現 `AMENT_TRACE_SETUP_FILES` / `AMENT_PYTHON_EXECUTABLE: unbound variable`）。
> 請改用下列明確步驟；商業版安裝器則由 `scripts/install_third_party.sh` 自動完成。

```bash
mkdir -p ~/Downloads/wmrSim && cd ~/Downloads/wmrSim
curl -fLO https://github.com/jeffc168/wmrSim-public/releases/download/v1.0.0/wmr_sim_third_party_v1.0.0.tar.gz
mkdir -p ~/wmr_sim_third_party && tar -xzf wmr_sim_third_party_v1.0.0.tar.gz -C ~/wmr_sim_third_party
BUNDLE=~/wmr_sim_third_party/wmr_sim_third_party_v1.0.0
mkdir -p ~/my_ws/src && cp -r "$BUNDLE"/src/* ~/my_ws/src/

# 系統相依（teb 需要 g2o / suitesparse）
sudo apt-get install -y libg2o-dev libsuitesparse-dev libopencv-dev libboost-all-dev ros-jazzy-nav2-core ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-util ros-jazzy-nav2-msgs ros-jazzy-cv-bridge ros-jazzy-eigen3-cmake-module ros-jazzy-tf2-eigen ros-jazzy-pluginlib ros-jazzy-visualization-msgs build-essential cmake

# 建置（不要在此環境啟用 set -u）
source /opt/ros/jazzy/setup.bash
cd ~/my_ws && colcon build --symlink-install --packages-select costmap_converter_msgs costmap_converter teb_msgs teb_local_planner dwb_core dwb_critics dwb_plugins
source ~/my_ws/install/setup.bash
ros2 pkg prefix teb_local_planner
```

**方式 B：使用本 repo 隨附工具（只下載原始碼；需自行裝系統相依與建置）**

```bash
# 檢查目前環境之第三方元件狀態
bash tools/fetch_third_party.sh --check

# 取得原始碼（--all = apt 安裝 dwb_* + 下載第三方原始碼）
bash tools/fetch_third_party.sh --all --ws ~/my_ws

# 系統相依（teb 需要 g2o / suitesparse）
sudo apt-get install -y libg2o-dev libsuitesparse-dev libopencv-dev libboost-all-dev ros-jazzy-nav2-core ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-util ros-jazzy-nav2-msgs ros-jazzy-cv-bridge ros-jazzy-eigen3-cmake-module ros-jazzy-tf2-eigen ros-jazzy-pluginlib ros-jazzy-visualization-msgs build-essential cmake

# 建置並載入
source /opt/ros/jazzy/setup.bash
cd ~/my_ws && colcon build --symlink-install
source ~/my_ws/install/setup.bash
ros2 pkg prefix teb_local_planner
```

> 商業版安裝器會以 `scripts/install_third_party.sh` 自動完成上述步驟，並將結果佈署到
> `/opt/wmr_sim/overlay`（`wmrsim` 與 `wmrsim doctor` 會自動 source 該處）。

---

## 6. 商業核心引擎與 3D GUI 說明（取得企業授權時）

本公開倉庫（`wmrSim-public`）依 **GPL-3.0 with Plugin Linking Exception** 釋出，內容為外掛開發介面與範例，**不包含專有之模擬核心與 3D 視覺化 GUI**。

若貴單位已取得宇集創新科技之商業核心安裝包（`ros-jazzy-wmr-sim-core_1.0.0_amd64.deb`），可透過以下步驟安裝並啟動 3D 視覺化模擬中心：

```bash
# 1. 補齊 3D 渲染與 PyQt GUI 必要套件
sudo apt install -y python3-pyqt5 python3-opengl python3-matplotlib

# 2. 安裝核心 Debian 套件
sudo dpkg -i packages/ros-jazzy-wmr-sim-core_1.0.0_amd64.deb
sudo apt install -f

# 3. 載入 ROS 2 環境變數
source /opt/ros/jazzy/setup.bash

# 4. 啟動多機器人模擬器 + 3D GUI
# 一鍵整合啟動 (模擬器 + Web Dashboard Gateway)
bash launch.sh

# 亦可單獨啟動純核心 (無 GUI)
# bash launch.sh gui:false

# 或使用原生 ROS 2 命令
ros2 launch wmr_sim multi_robot_sim.launch.py gui:=true
```

---

## 7. 常見問題與排除 (Troubleshooting)

| 症狀 / 錯誤訊息 | 可能原因 | 排除方式 |
|---|---|---|
| `ModuleNotFoundError: No module named 'wmr_sim'` | 尚未安裝 SDK 且不在 `examples/` 目錄下執行 | 執行 `pip install -e ./sdk --break-system-packages`，或設定 `export PYTHONPATH=$PWD/sdk:$PYTHONPATH` |
| `error: externally-managed-environment` | Ubuntu 24.04 預設限制 pip 寫入系統目錄 | 加入 `--break-system-packages` 參數，或使用 `python3 -m venv .venv` 建立虛擬環境 |
| `No module named 'OpenGL'` | 啟動 3D GUI 時缺少 PyOpenGL 套件 | 執行 `sudo apt install -y python3-opengl` |
| GUI 視窗無法開啟 | 遠端連線無 `DISPLAY` 環境變數 | 設定 X11 轉發（`ssh -X`）或參閱 `manuals/OPERATION_MANUAL.md` 設定純背景運行（`gui:=false`） |
