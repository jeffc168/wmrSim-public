# wmrSim Release V1.0 — 客戶文件索引 (Customer Manuals)

**產品**：wmrSim 企業級多機器人模擬與智慧車隊調度平台
**版本**：V1.0 (Release Build 1.0.0)
**著作權**：Copyright (C) 2026 宇集創新科技. All Rights Reserved.

本目錄僅包含**對外開放**之客戶文件。核心內部技術文件不在發行範圍內。

> **若你取得的是公開的 Plugin SDK repo**（僅有 `sdk/`、`examples/`、`manuals/`、
> `plugins/`），則**模擬核心不在其中**，需另行取得授權後安裝。
> 此時 `OPERATION_MANUAL.md` 第 2 節所述之完整發行包結構（`packages/`、
> `install.sh`、`verify.sh`、`config/`）會隨核心發行包一併交付；
> 若只要開發外掛，請直接參閱 `PLUGIN_AUTHORING_GUIDE.md` 與 `EXAMPLES_GUIDE.md`。

| 文件 | 說明 | 適用對象 |
|---|---|---|
| [`OPERATION_MANUAL.md`](OPERATION_MANUAL.md) | 操作說明書：安裝、啟動、GUI、設定、診斷 | 現場工程師 / 維運人員 |
| [`PLUGIN_AUTHORING_GUIDE.md`](PLUGIN_AUTHORING_GUIDE.md) | 插件寫作指南：介面契約、Manifest、註冊、驗證 | 演算法工程師 |
| [`EXAMPLES_GUIDE.md`](EXAMPLES_GUIDE.md) | 範例說明：官方範例逐段解析與實作練習 | 演算法工程師 |

## 快速連結

```bash
# 1. 安裝核心 + SDK
bash install.sh

# 2. 驗證安裝（含無源碼保護檢驗）
bash verify.sh

# 3. 啟動模擬 + GUI
source /opt/ros/jazzy/setup.bash
ros2 launch wmr_sim multi_robot_sim.launch.py gui:=true
```

## 支援

- 授權與合約：`EULA.md`
- 第三方元件授權：`NOTICE`
- 著作權宣告：`COPYRIGHT`
- 發行完整性憑證：`release_manifest.json`（SHA-256）
