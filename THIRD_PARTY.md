# 第三方元件清單與授權聲明 (Third-Party Components)

**專案**：wmrSim 企業級多機器人模擬與智慧車隊調度平台
**版本**：V1.0 (Release Build 1.0.0)
**發行主體**：宇集創新科技
**本文件版本**：2026

本專案 `src/` 下包含五個**第三方 ROS 2 套件**（vendored）。這些套件**不是**
宇集創新科技的著作，各自依其上游授權條款散布。本文件列出精確來源、授權、
以及本專案所施加的在地補丁。

> wmrSim 自有程式碼為 `src/wmr_sim/`，授權為 Proprietary。
> 兩者在本文件中明確區分，互不混淆。

---

## 1. 元件總表

| 套件 | 版本 | 上游來源 | 上游 ref | 授權 | 本地補丁 |
|---|---|---|---|---|---|
| `dwb_core` | 1.3.12 | [ros-navigation/navigation2](https://github.com/ros-navigation/navigation2) `nav2_dwb_controller/dwb_core` | `jazzy` | BSD-3-Clause | 無 |
| `dwb_critics` | 1.3.12 | 同上 `nav2_dwb_controller/dwb_critics` | `jazzy` | BSD-3-Clause | 無 |
| `dwb_plugins` | 1.3.12 | 同上 `nav2_dwb_controller/dwb_plugins` | `jazzy` | BSD-3-Clause | 無 |
| `costmap_converter` | 0.1.2 | [rst-tu-dortmund/costmap_converter](https://github.com/rst-tu-dortmund/costmap_converter) | `0.1.2` | BSD-3-Clause | 有（4 檔） |
| `costmap_converter_msgs` | 0.1.2 | 同上 | `0.1.2` | BSD-3-Clause | 無 |
| `teb_local_planner` | 0.9.1 | [rst-tu-dortmund/teb_local_planner](https://github.com/rst-tu-dortmund/teb_local_planner) | `ros2-master` | BSD-3-Clause | 有（15 檔） |
| `teb_msgs` | 0.0.1 | 同上 | `ros2-master` | Apache-2.0 | 無 |

### 著作權人 (Copyright Holders)

| 套件 | 著作權 |
|---|---|
| `dwb_*` | Copyright (c) 2012 Willow Garage, Inc.；2017–2018 Locus Robotics；2018 Wilco Bonestroo；2020 Samsung Research America |
| `costmap_converter*` | Copyright (c) 2016–2017 TU Dortmund — Institute of Control Theory and Systems Engineering (Lehrstuhl RST) |
| `teb_local_planner`、`teb_msgs` | Copyright (c) 2016–2017 TU Dortmund — Institute of Control Theory and Systems Engineering (Lehrstuhl RST) |

授權全文見 `LICENSES/`；各套件目錄內亦放置 `LICENSE` 檔以符合
BSD-3-Clause 第 1 條「保留著作權聲明與授權條款」之要求。

---

## 2. 本地補丁說明

本專案將上述套件移植至 **Ubuntu 24.04 LTS / ROS 2 Jazzy / GCC 13 / OpenCV 4.6+**
時，施加了最小幅度的可攜性補丁。完整內容見
`patches/wmrsim-jazzy-portability.patch`（605 行、20 檔）。

### 2.1 `costmap_converter`（4 檔）

| 檔案 | 變更 |
|---|---|
| `costmap_converter/CMakeLists.txt` | 補 `target_link_libraries(... ${OpenCV_LIBRARIES})`（2 處） |
| `include/.../background_subtractor.h` | `cv_bridge/cv_bridge.h` → `cv_bridge/cv_bridge.hpp`（Jazzy 標頭改名） |
| `include/.../costmap_to_dynamic_obstacles.h` | 同上 cv_bridge 標頭 |
| `src/.../costmap_to_dynamic_obstacles.cpp` | 同上 cv_bridge 標頭 |

### 2.2 `teb_local_planner`（15 檔）

| 分類 | 檔案 | 變更 |
|---|---|---|
| CMake 尋徑 | `cmake_modules/FindG2O.cmake` | `PATH_SUFFIXES` 加入 `lib/x86_64-linux-gnu`、`lib64`（Debian multiarch） |
| CMake 尋徑 | `cmake_modules/FindSUITESPARSE.cmake` | 同上 multiarch 路徑 |
| CMake | `CMakeLists.txt` | 依 Jazzy 相依調整、OpenCV/g2o 連結 |
| 相依宣告 | `package.xml` | 新增 `<exec_depend>nav2_bringup</exec_depend>`（空白正規化） |
| 標頭相容 | `g2o_types/penalties.h`、`g2o_types/vertex_pose.h`、`g2o_types/edge_kinematics.h`、`g2o_types/edge_obstacle.h`、`pose_se2.h`、`teb_config.h`、`misc.h` | g2o / Eigen / C++17 相容性調整 |
| 實作 | `src/optimal_planner.cpp`、`src/recovery_behaviors.cpp`、`src/teb_local_planner_ros.cpp` | Jazzy API 相容性調整 |

補丁**未變更**任何上游的演算法邏輯、著作權宣告或作者資訊。

---

## 3. 一鍵取得第三方套件

### 方式 A：APT（最快，僅涵蓋 `dwb_*`）

```bash
sudo apt-get install -y \
    ros-jazzy-dwb-core ros-jazzy-dwb-critics ros-jazzy-dwb-plugins
```

`costmap_converter` 與 `teb_local_planner` 目前**未收錄**於 ROS 2 Jazzy 官方 apt
套件庫，需以下列方式取得。

### 方式 B：下載已打包好的第三方原始碼包（建議）

本專案提供 `wmr_sim_third_party_v1.0.0.tar.gz`，內含全部 5 個套件的原始碼
（含已套用之補丁）、授權全文與安裝腳本。

```bash
bash tools/fetch_third_party.sh --bundle
```

或手動：

```bash
curl -L -o /tmp/third_party.tar.gz \
  https://github.com/<org>/<repo>/releases/download/v1.0.0/wmr_sim_third_party_v1.0.0.tar.gz
tar -xzf /tmp/third_party.tar.gz -C /tmp
cp -r /tmp/wmr_sim_third_party_v1.0.0/src/* <your_ws>/src/
```

### 方式 C：從上游取得並自行套用補丁

```bash
bash tools/fetch_third_party.sh --upstream --patches
```

等同於：

```bash
git clone --depth 1 --branch 0.1.2 https://github.com/rst-tu-dortmund/costmap_converter.git
git clone --depth 1 --branch ros2-master https://github.com/rst-tu-dortmund/teb_local_planner.git
patch -p1 < patches/wmrsim-jazzy-portability.patch
```

---

## 4. 建置

取得原始碼後置於 ROS 2 工作區之 `src/`，然後：

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select \
    costmap_converter_msgs costmap_converter \
    teb_msgs teb_local_planner \
    dwb_core dwb_critics dwb_plugins
```

系統相依（Ubuntu 24.04）：

```bash
sudo apt-get install -y \
    ros-jazzy-nav2-core ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-util \
    ros-jazzy-cv-bridge ros-jazzy-eigen3-cmake-module ros-jazzy-tf2-eigen \
    libg2o-dev libsuitesparse-dev libopencv-dev libboost-all-dev
```

---

## 5. 授權合規聲明

1. 上述第三方套件**依其原始授權條款散布**，未被重新授權為 Proprietary。
2. 各套件之著作權聲明與授權條款已完整保留（見各目錄 `LICENSE` 與 `LICENSES/`）。
3. 本地補丁以最小幅度實作，未移除任何著作權標記。
4. 本專案自有程式碼（`src/wmr_sim/`）與第三方套件在檔案系統與授權上均明確區隔。
5. 若發現任何歸屬錯誤或遺漏，請聯繫授權方更正。

---

Copyright (C) 2026 宇集創新科技. All Rights Reserved.（僅限本文件與 wmrSim 自有程式碼；
第三方套件著作權歸其各自權利人所有）
