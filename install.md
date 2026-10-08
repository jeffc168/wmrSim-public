# wmrSim 安裝指南（Ubuntu 24.04）

本指南適用於乾淨的 **Ubuntu 24.04 LTS amd64**。一般桌面使用者請依序完成「下載、校驗、安裝、啟動」；安裝器會在需要時設定 ROS 2 Jazzy 官方套件來源並安裝執行相依。安裝需要網路連線與一次管理員授權。

## 1. 下載發布檔

從同一個 Release 下載以下兩個檔案，並放在 Ubuntu 的同一個資料夾（例如 `~/Downloads/wmrSim`）：

- `wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run`：推薦的一鍵安裝器
- `wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run.sha256`：安裝器校驗檔

下載不完整發布包時，請先重新下載，不要略過校驗。不要把安裝器放在唯讀媒體或 Windows 網路磁碟上執行。

## 2. 校驗安裝器

開啟 Ubuntu Terminal，進入下載資料夾。以下假設檔案放在該路徑：

```bash
mkdir -p ~/Downloads/wmrSim
cd ~/Downloads/wmrSim
```

確認校驗檔顯示 `OK`：

```bash
sha256sum -c wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run.sha256
```

若顯示 `FAILED`、找不到檔案或校驗檔不是從相同 Release 取得，請停止並重新下載兩個檔案。

## 3. 安裝桌面版

桌面版包含 RViz 與 Nav2，適用一般 Ubuntu 桌面：

```bash
chmod u+x wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run
sudo ./wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run --profile desktop --yes
```

輸入 Ubuntu 使用者密碼後，等待 apt 安裝完成。過程需要網路連線；安裝器會檢查 Ubuntu 版本及 amd64 架構，安裝 ROS 2 Jazzy、Nav2、wmrSim 核心與 SDK，最後執行安裝診斷。請等候看到「安裝完成」訊息；任何錯誤都代表流程尚未完成。

> 請以一般登入使用者啟動 wmrSim，不要使用 `sudo wmrsim`。

## 4. 確認安裝並啟動

> ⚠️ **先完成 §4.1**：核心執行相依 `teb_local_planner` 與 `costmap_converter` **不在 ROS 官方 apt 內**，
> 發行包也未附帶。未先取得時，`wmrsim doctor` 會失敗於「ROS 2 找不到執行相依套件：teb_local_planner」。

先執行診斷：

```bash
wmrsim doctor
```

### 4.1 取得第三方導航相依（必要）

核心以 `<exec_depend>` 宣告 `teb_local_planner`，並在 `plugin_registry` 註冊
`teb_local_planner:TebLocalPlanner`；`wmrsim doctor` 會強制檢查 `teb_local_planner`
與 `costmap_converter` 能否被 `ros2 pkg prefix` 解析。
這兩者**未收錄於 ROS 官方 apt，發行包也未附帶**，必須自行取得並建置
（BSD-3-Clause / Apache-2.0，非宇集創新科技著作）。

需要這 7 個套件：`costmap_converter_msgs`、`costmap_converter`、`teb_msgs`、
`teb_local_planner`、`dwb_core`、`dwb_critics`、`dwb_plugins`。

**方式 A：使用第三方發行包內建的安裝腳本（最快，含系統相依與建置）**

```bash
mkdir -p ~/Downloads/wmrSim && cd ~/Downloads/wmrSim
curl -fLO https://github.com/jeffc168/wmrSim-public/releases/download/v1.0.0/wmr_sim_third_party_v1.0.0.tar.gz
mkdir -p ~/wmr_sim_third_party && tar -xzf wmr_sim_third_party_v1.0.0.tar.gz -C ~/wmr_sim_third_party
cd ~/wmr_sim_third_party/wmr_sim_third_party_v1.0.0
bash install.sh                  # apt 安裝系統相依 → colcon build 至 ~/wmr_sim_third_party_ws
source ~/wmr_sim_third_party_ws/install/setup.bash
```

**方式 B：使用本 repo 的取得工具（只下載原始碼；需自行安裝系統相依並建置）**

```bash
bash tools/fetch_third_party.sh --bundle --ws ~/wmr_sim_third_party_ws

sudo apt-get install -y libg2o-dev libsuitesparse-dev libopencv-dev libboost-all-dev ros-jazzy-nav2-core ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-util ros-jazzy-nav2-msgs ros-jazzy-cv-bridge ros-jazzy-eigen3-cmake-module ros-jazzy-tf2-eigen ros-jazzy-pluginlib ros-jazzy-visualization-msgs build-essential cmake

source /opt/ros/jazzy/setup.bash
cd ~/wmr_sim_third_party_ws && colcon build --symlink-install --packages-select costmap_converter_msgs costmap_converter teb_msgs teb_local_planner dwb_core dwb_critics dwb_plugins
source ~/wmr_sim_third_party_ws/install/setup.bash
```

完成後在**同一個已 `source` 的終端機**內再確認：

```bash
bash tools/fetch_third_party.sh --check --ws ~/wmr_sim_third_party_ws
ros2 pkg prefix teb_local_planner     # 應印出安裝路徑
wmrsim doctor                         # 應全部 PASS
```

> **讓 `wmrsim start` 不必每次手動 `source`**：`wmrsim doctor` 會自動 source
> `/opt/wmr_sim/overlay/local_setup.bash`，可將建置結果放到該 overlay。

```bash
sudo mkdir -p /opt/wmr_sim/overlay
sudo cp -r ~/wmr_sim_third_party_ws/install/. /opt/wmr_sim/overlay/
```

（或每次啟動 wmrSim 前先 `source ~/wmr_sim_third_party_ws/install/setup.bash`。）

所有必要項目通過後，啟動模擬與 Dashboard：

```bash
wmrsim start
```

Dashboard 網址為 [http://127.0.0.1:8080/](http://127.0.0.1:8080/)。桌面模式會嘗試開啟瀏覽器；若沒有自動開啟，請手動把網址貼入瀏覽器。關閉正在執行的終端工作階段會停止該次模擬。

也可從 Ubuntu 應用程式清單啟動 **wmrSim**。無桌面伺服器請改用 base profile 並以 headless 模式啟動：

```bash
sudo ./wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run --profile base --yes
wmrsim doctor
wmrsim start --headless
```

## 5. 使用完整 tar.gz 發行包（替代方式）

若企業流程選擇完整 tar.gz，請一併下載其 `.sha256` 檔，放在同一目錄後校驗及解壓：

```bash
sha256sum -c wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.tar.gz.sha256
mkdir -p ~/Downloads/wmrSim-bundle
tar -xzf wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.tar.gz -C ~/Downloads/wmrSim-bundle
cd ~/Downloads/wmrSim-bundle/wmr_sim_commercial_v1.0.0
sudo bash ./install.sh --profile desktop --yes
```

安裝後的診斷及啟動方式與前述步驟相同。一般使用者不需要另外安裝 .deb 或 SDK wheel。

## 6. 常見安裝問題

- **Ubuntu 版本或架構不支援**：本發布包只支援 Ubuntu 24.04 LTS amd64；在安裝器修改系統前就會停止。
- **ROS/apt 下載失敗**：確認主機可連上 Ubuntu 與 ROS 官方套件來源，並確認公司代理或防火牆允許 apt/HTTPS 流量，再重新執行安裝器。
- **apt 提示鎖定中**：等待 Ubuntu 更新程式或其他 apt 工作完成後再重試；不要手動刪除 apt lock 檔。
- **診斷失敗**：保留終端機完整錯誤輸出，並執行 `wmrsim doctor`；不要把安裝失敗視為已完成。

## 7. 使用手冊

下載同一發布目錄中的 `user_manual.html)，以瀏覽器開啟，即可查閱 wmrSim 功能與操作說明。
