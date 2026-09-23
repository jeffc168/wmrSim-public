# Changelog

本專案遵循 [Semantic Versioning](https://semver.org/)。

## [1.0.0] — 2026 — Release V1.0

首個公開發行版本（Plugin SDK）。

### Added

- **外掛 SDK**（`wmr_sim.sdk`）
  - `interfaces.py`：`BaseGlobalPlanner` / `BaseLocalController` /
    `BaseTrafficPlugin` / `BaseTaskManager` 四大抽象基底類別
  - `dataclasses.py`：`Pose2D`、`Velocity2D`（別名 `Twist2D`）、
    `OccupancyGridData`、`CustomerTrafficPlanResult`、`CustomerTaskPlanResult`、
    `PluginManifest`、`PluginValidationReport`、`PointCloud3DData` 等
  - `verifier.py`：`PluginVerifier` 契約檢驗與延遲量測（SLA 50 ms）
  - `discovery.py`：`PluginDiscoverer` 外掛探索
  - `adapters.py`：SDK ↔ runtime 橋接（`SdkTrafficAdapter` / `SdkTaskAdapter`）
- **外掛 Manifest JSON Schema**
  - `plugin_manifest_v1.schema.json`
  - `plugin_registration_v1.schema.json`
- **可執行範例**（`examples/`）
  - `custom_astar_planner.py`：8 連通 A* 全域規劃器（含繞障與退化直線路徑）
  - `custom_rpp_controller.py`：Regulated Pure Pursuit 局部控制器
    （前視點、航向比例控制、加速度限幅、障礙減速）
  - `custom_traffic_manager.py`：靠右通行 + 直行優先交通管理器
  - `verify_examples.py`：範例自我驗證 + 端到端煙霧測試
- **對外開放手冊**（`manuals/`）
  - 操作說明書、插件寫作指南、範例說明
- **授權文件**：`LICENSE`、`COPYRIGHT`、`NOTICE`、`EULA.md`
- **第三方元件一鍵取得**
  - `tools/fetch_third_party.sh`：`--check` / `--apt` / `--bundle` /
    `--upstream` / `--all`，自動由 repo `origin` 推導下載來源
  - `third_party/`：第三方 ROS 2 套件原始碼包
    （`wmr_sim_third_party_v1.0.0.tar.gz`，含已套用之 Jazzy 補丁）
  - `patches/wmrsim-jazzy-portability.patch`：相對上游的 20 檔可攜性補丁
  - `LICENSES/`：第三方授權全文
  - `THIRD_PARTY.md`：來源、版本、授權、著作權人與補丁說明

### Changed

- **SDK 可獨立匯入**：`wmr_sim.sdk.__init__` 改為惰性載入 `adapters`。
  先前在未安裝模擬核心的環境下 `import wmr_sim.sdk` 會因
  `wmr_sim.task_management` 不存在而失敗，導致無法離線開發外掛。
  現在介面、資料結構、`PluginVerifier`、`PluginDiscoverer` 均可獨立使用；
  僅 `SdkTrafficAdapter` / `SdkTaskAdapter` 需核心。

### Fixed (third-party compliance)

- 補齊第三方套件缺失的授權檔：`dwb_core`、`dwb_critics`、`dwb_plugins`、
  `costmap_converter`、`teb_msgs` 原均無 `LICENSE`，現已補附完整
  BSD-3-Clause / Apache-2.0 全文與著作權人標示，符合
  BSD-3-Clause 第 1 條「保留著作權聲明與授權條款」之要求。

### Fixed

- 範例與 SDK 契約不一致（會直接拋出例外）：
  - `plan_path` 缺少 `grid_map` 參數、使用不存在的 `Pose2D.theta`
  - `compute_velocity` 缺少 `target_path` / `dt_sec`
  - 使用不存在的 `Velocity2D(linear=, angular=)` 參數
- 修正後範例簽章與 `PluginVerifier` 完全一致，實測 `ALL PASS`。

---

Copyright (C) 2026 宇集創新科技. All Rights Reserved.
