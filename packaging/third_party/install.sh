#!/usr/bin/env bash
# ==============================================================================
# wmrSim 第三方 ROS 2 套件 — 建置與安裝腳本
#
# 用於 wmr_sim_third_party_v<version>.tar.gz 解壓後執行。
# 這些套件為第三方著作（BSD-3-Clause / Apache-2.0），非宇集創新科技所有，
# 依其原始授權散布。詳見 THIRD_PARTY.md。
#
# 用法:
#   bash install.sh                    # 建置到 ~/wmr_sim_third_party_ws
#   bash install.sh --ws /path/to/ws   # 指定工作區
#   bash install.sh --deps-only        # 只安裝系統相依
#   bash install.sh --no-build         # 只複製原始碼，不建置
#   bash install.sh --no-deps          # 不安裝系統相依
#
# 注意：ROS 2 的 setup 腳本**不相容 `set -u`**（會出現
#       AMENT_TRACE_SETUP_FILES / AMENT_PYTHON_EXECUTABLE: unbound variable），
#       因此本腳本只使用 `set -eo pipefail`，並在 source ROS 前後明確處理 set -u。
# ==============================================================================
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="${HOME}/wmr_sim_third_party_ws"
DO_DEPS=1
DO_BUILD=1

# 原始碼包內的頂層目錄（costmap_converter_msgs / teb_msgs 巢狀於其中）
BUNDLE_DIRS=(costmap_converter teb_local_planner dwb_core dwb_critics dwb_plugins)
PACKAGES=(costmap_converter_msgs costmap_converter teb_msgs teb_local_planner
          dwb_core dwb_critics dwb_plugins)

usage() { sed -n '2,19p' "$0"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --ws)         WS_DIR="$2"; shift 2 ;;
        --deps-only)  DO_BUILD=0; shift ;;
        --no-build)   DO_BUILD=0; shift ;;
        --no-deps)    DO_DEPS=0; shift ;;
        -h|--help)    usage; exit 0 ;;
        *) echo "未知參數: $1" >&2; usage; exit 2 ;;
    esac
done

echo "======================================================================"
echo " wmrSim 第三方 ROS 2 套件安裝程式"
echo " 元件: ${PACKAGES[*]}"
echo " 工作區: ${WS_DIR}"
echo " 授權: BSD-3-Clause / Apache-2.0（第三方著作，非宇集創新科技）"
echo "======================================================================"

# 1. 環境檢查
if [ ! -d /opt/ros/jazzy ]; then
    echo "[ERROR] 未偵測到 ROS 2 Jazzy (/opt/ros/jazzy)。" >&2
    echo "        請先安裝：https://docs.ros.org/en/jazzy/Installation.html" >&2
    exit 1
fi
set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
set -u
echo "[1/4] ROS 2 Jazzy 環境已載入。"

# 2. 系統相依
if [ "${DO_DEPS}" -eq 1 ]; then
    echo "[2/4] 安裝系統相依（需要 sudo）..."
    if ! sudo -n true 2>/dev/null; then
        echo "      [INFO] 需要 sudo 權限；若已具備相依可改用 --no-deps。"
    fi
    sudo apt-get update -qq
    sudo apt-get install -y \
        ros-jazzy-nav2-core ros-jazzy-nav2-costmap-2d ros-jazzy-nav2-util \
        ros-jazzy-nav2-msgs ros-jazzy-cv-bridge ros-jazzy-eigen3-cmake-module \
        ros-jazzy-tf2-eigen ros-jazzy-pluginlib ros-jazzy-visualization-msgs \
        libg2o-dev libsuitesparse-dev libopencv-dev libboost-all-dev \
        build-essential cmake
else
    echo "[2/4] 略過系統相依安裝 (--no-deps)。"
fi

# 3. 佈署原始碼至工作區
echo "[3/4] 佈署原始碼至 ${WS_DIR}/src ..."
mkdir -p "${WS_DIR}/src"
for d in "${BUNDLE_DIRS[@]}"; do
    if [ ! -d "${SCRIPT_DIR}/src/${d}" ]; then
        echo "      [WARN] 找不到 src/${d}，略過。" >&2
        continue
    fi
    rm -rf "${WS_DIR}/src/${d}"
    cp -r "${SCRIPT_DIR}/src/${d}" "${WS_DIR}/src/"
    echo "      + ${d}"
done
# 授權全文一併複製，確保散布時合規
mkdir -p "${WS_DIR}/third_party_LICENSES"
cp -r "${SCRIPT_DIR}/LICENSES/." "${WS_DIR}/third_party_LICENSES/" 2>/dev/null || true
cp "${SCRIPT_DIR}/THIRD_PARTY.md" "${WS_DIR}/third_party_LICENSES/" 2>/dev/null || true

# 4. 建置
if [ "${DO_BUILD}" -eq 1 ]; then
    echo "[4/4] colcon build ..."
    if ! ( cd "${WS_DIR}" && colcon build --symlink-install --packages-select "${PACKAGES[@]}" ); then
        echo "[ERROR] colcon build 失敗（常見原因：缺少 libg2o-dev / libsuitesparse-dev）。" >&2
        exit 1
    fi
    echo
    echo "======================================================================"
    echo " [SUCCESS] 第三方套件建置完成。"
    echo " 載入方式: source ${WS_DIR}/install/setup.bash"
    echo " 授權文件: ${WS_DIR}/third_party_LICENSES/"
    echo "======================================================================"
else
    echo "[4/4] 略過建置。原始碼位於 ${WS_DIR}/src"
fi
