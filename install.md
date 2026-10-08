# wmrSim 安裝指南（Ubuntu 24.04）

本指南適用於乾淨的 **Ubuntu 24.04 LTS amd64**。一般桌面使用者請依序完成「下載、校驗、安裝、啟動」；安裝器會在需要時設定 ROS 2 Jazzy 官方套件來源並安裝執行相依。安裝需要網路連線與一次管理員授權。

> **文件定位**：本文件是**商業版一鍵安裝指南**（一般使用者），發布時置換版本號後即為公開庫的 `install.md`。
> 外掛 SDK 開發者請另見 `manuals/install_ubuntu24.md`。

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

輸入 Ubuntu 使用者密碼後，等待 apt 安裝完成。過程需要網路連線；安裝器會檢查 Ubuntu 版本及 amd64 架構，然後依序：

1. 安裝 ROS 2 Jazzy 與 Nav2（依 `--profile` 為 desktop 或 base）；
2. 安裝 wmrSim 核心 `.deb` 與外掛 SDK wheel；
3. **以發行包內附的第三方原始碼包建置導航相依**（`teb_local_planner`、`costmap_converter`、`dwb_*`；包含 apt 系統相依與 `colcon build`，通常需要數分鐘），並把建置結果佈署到 `/opt/wmr_sim/overlay`；
4. 執行安裝診斷（`wmrsim doctor`）。

請等候看到「安裝完成」訊息；任何錯誤都代表流程尚未完成。第 3 步是核心的必要相依（見 §4.1）；若該步未完成，`wmrsim doctor` 會以**退出碼 3** 結束並印出修復指引。

> 請以一般登入使用者啟動 wmrSim，不要使用 `sudo wmrsim`。

## 4. 確認安裝並啟動

> ⚠️ **安裝器已自動處理 §4.1**：若安裝器已完成第三方導航相依建置，本節可直接執行 `wmrsim doctor`。
> 若曾中斷、或診斷顯示「缺少第三方導航相依」，請依 §4.1 補做。

先執行診斷：

```bash
wmrsim doctor
```

### 4.1 取得第三方導航相依（必要）

核心以 `<exec_depend>` 宣告 `teb_local_planner`，並在 `plugin_registry` 註冊；
`wmrsim doctor` 會強制檢查 `teb_local_planner` 與 `costmap_converter`。
這兩者**不在 ROS 官方 apt 內，也不在核心 .deb 內**，必須另外取得並建置
（BSD-3-Clause / Apache-2.0，非宇集創新科技著作）。

安裝器（`install.sh` / `.run`）會自動執行下列步驟，並把建置結果佈署到 `/opt/wmr_sim/overlay`。
若安裝中斷、或診斷顯示「缺少第三方導航相依」，請依你的安裝方式補做：

**方式一：`tar.gz` 發行包（發行樹仍在）**

```bash
cd ~/Downloads/wmrSim-bundle/wmr_sim_commercial_v1.0.0
sudo bash scripts/install_third_party.sh --release-root "$PWD" --offline   # 使用包內 third_party/ 原始碼包
sudo bash scripts/install_third_party.sh --release-root "$PWD"             # 允許由網路取得時

# 驗收
wmrsim doctor                     # 應全部 PASS
```

**方式二：`.run` 單檔安裝器（發行樹為暫存目錄，安裝後已刪除）**

`.run` 會把內容解壓到暫存目錄、安裝完成後刪除，因此事後無法再執行 `scripts/install_third_party.sh`。請擇一：

```bash
# A. 重新執行安裝器（會重跑第三方建置）
sudo ./wmr_sim_commercial_v1.0.0_ubuntu24.04_amd64.run --profile desktop --yes

# B. 另外下載 tar.gz 發行包並解開，改採「方式一」

# C. 改用「方式三」的公開 SDK repo 步驟
```

**方式三：公開 SDK repo 的手動步驟（不需發行包）**

若沒有發行包，可改用公開 SDK repo 隨附工具自行建置：

```bash
bash tools/fetch_third_party.sh --bundle --ws ~/wmr_sim_third_party_ws
sudo apt-get install -y libg2o-dev libsuitesparse-dev libopencv-dev libboost-all-dev ros-jazzy-nav2-core ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-util ros-jazzy-nav2-msgs ros-jazzy-cv-bridge ros-jazzy-eigen3-cmake-module ros-jazzy-tf2-eigen ros-jazzy-pluginlib ros-jazzy-visualization-msgs build-essential cmake
source /opt/ros/jazzy/setup.bash
cd ~/wmr_sim_third_party_ws && colcon build --symlink-install --packages-select costmap_converter_msgs costmap_converter teb_msgs teb_local_planner dwb_core dwb_critics dwb_plugins
sudo mkdir -p /opt/wmr_sim/overlay && sudo cp -r ~/wmr_sim_third_party_ws/install/. /opt/wmr_sim/overlay/
```

> `wmrsim` 與 `wmrsim doctor` 都會自動 source `/opt/wmr_sim/overlay/local_setup.bash`，
> 因此建置結果佈署到該處後，不需每次手動 `source`。
>
> ⚠️ **不要直接執行第三方原始碼包內的 `install.sh`**：它以 `set -euo pipefail` 執行後才 source
> ROS setup 腳本，與 ROS 2 Jazzy 不相容（`AMENT_TRACE_SETUP_FILES: unbound variable`）。
> 請使用 `scripts/install_third_party.sh`，或依上方手動步驟自行建置。

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
- **診斷顯示「缺少第三方導航相依」（退出碼 3）**：安裝流程的第三方建置未完成或曾中斷。請依 **§4.1** 補做（`.run` 安裝請重新執行安裝器或改用 tar.gz 發行包），再重新執行 `wmrsim doctor`。
- **第三方建置失敗（`colcon build` 錯誤）**：最常見原因是系統相依未裝齊（`libg2o-dev`、`libsuitesparse-dev`、`libopencv-dev`、`libboost-all-dev`）或網路中斷。確認網路與 ROS/Ubuntu 套件來源後重試；安裝器會印出缺少的套件。
- **離線安裝找不到第三方原始碼包**：離線安裝要求發行包內含 `third_party/wmr_sim_third_party_v*.tar.gz`；若企業流程裁剪發行包而移除該目錄，請改用線上安裝或使用未裁剪的原始發行包。

## 7. 使用手冊

下載同一發布目錄中的 `user_manual.html`，以瀏覽器開啟，即可查閱 wmrSim 功能與操作說明。
