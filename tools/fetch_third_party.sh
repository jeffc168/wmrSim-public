#!/usr/bin/env bash
# ==============================================================================
# wmrSim 第三方 ROS 2 套件 — 一鍵取得工具 (One-Click Fetcher)
#
# 取得 wmrSim 於 Ubuntu 24.04 / ROS 2 Jazzy 上所需之第三方套件：
#   dwb_core / dwb_critics / dwb_plugins      (BSD-3-Clause, Nav2)
#   costmap_converter(+_msgs)                 (BSD-3-Clause, TU Dortmund)
#   teb_local_planner / teb_msgs              (BSD-3-Clause / Apache-2.0, TU Dortmund)
#
# 這三個方式任選：
#   --apt       以 apt 安裝官方已收錄的套件（僅 dwb_*）
#   --bundle    下載 wmrSim 打包好的第三方原始碼包（推薦，含補丁）
#   --upstream  從上游 clone 並套用在地補丁
#
# 這些套件為第三方著作，非宇集創新科技所有，依其原始授權散布。
# 詳見 THIRD_PARTY.md。
#
# 用法:
#   bash fetch_third_party.sh --check
#   bash fetch_third_party.sh --apt
#   bash fetch_third_party.sh --bundle [URL] [--ws DIR]
#   bash fetch_third_party.sh --upstream [--ws DIR]
#   bash fetch_third_party.sh --all [--ws DIR]
# ==============================================================================
set -uo pipefail

RELEASE_VERSION="1.0.0"
BUNDLE_FILE="wmr_sim_third_party_v${RELEASE_VERSION}.tar.gz"

# 自動由本 repo 的 origin remote 推導下載來源，亦可逕行覆寫：
#   WMR_THIRD_PARTY_URL=... bash fetch_third_party.sh --bundle
_SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_REPO_SLUG="${WMR_THIRD_PARTY_REPO:-}"
if [ -z "${_REPO_SLUG}" ]; then
    _REPO_SLUG="$(git -C "${_SELF_DIR}" remote get-url origin 2>/dev/null \
        | sed -E 's#.*github\.com[:/]##; s#\.git$##')"
fi
[ -z "${_REPO_SLUG}" ] && _REPO_SLUG="jeffc168/wmrSim-sdk"

BUNDLE_URL="${WMR_THIRD_PARTY_URL:-https://github.com/${_REPO_SLUG}/releases/download/v${RELEASE_VERSION}/${BUNDLE_FILE}}"
UPSTREAM_PATCH_URL="${WMR_THIRD_PARTY_PATCH_URL:-https://raw.githubusercontent.com/${_REPO_SLUG}/v${RELEASE_VERSION}/patches/wmrsim-jazzy-portability.patch}"

WS_DIR=""
DO_CHECK=0
DO_APT=0
DO_BUNDLE=0
DO_UPSTREAM=0

APT_PKGS=(ros-jazzy-dwb-core ros-jazzy-dwb-critics ros-jazzy-dwb-plugins)
BUNDLE_PKGS=(dwb_core dwb_critics dwb_plugins costmap_converter teb_local_planner)

usage() { sed -n '2,27p' "$0"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --check)     DO_CHECK=1; shift ;;
        --apt)       DO_APT=1; shift ;;
        --bundle)    DO_BUNDLE=1; shift
                     if [ $# -gt 0 ] && [[ "$1" != --* ]]; then BUNDLE_URL="$1"; shift; fi ;;
        --upstream)  DO_UPSTREAM=1; shift ;;
        --all)       DO_APT=1; DO_BUNDLE=1; shift ;;
        --ws)        WS_DIR="$2"; shift 2 ;;
        -h|--help)   usage; exit 0 ;;
        *) echo "未知參數: $1"; usage; exit 1 ;;
    esac
done

[ $((DO_CHECK + DO_APT + DO_BUNDLE + DO_UPSTREAM)) -eq 0 ] && DO_CHECK=1
[ -z "${WS_DIR}" ] && WS_DIR="${PWD}"

log()  { printf '[fetch] %s\n' "$*"; }
warn() { printf '[fetch][WARN] %s\n' "$*" >&2; }
die()  { printf '[fetch][ERROR] %s\n' "$*" >&2; exit 1; }

echo "======================================================================"
echo " wmrSim 第三方 ROS 2 套件取得工具"
echo " 工作區: ${WS_DIR}"
echo " 來源  : ${_REPO_SLUG}"
echo " 授權  : BSD-3-Clause / Apache-2.0（第三方著作，非宇集創新科技）"
echo "======================================================================"

# ------------------------------------------------------------------ #
# --check
# ------------------------------------------------------------------ #
do_check() {
    echo "[CHK] ROS 2 環境"
    if [ -d /opt/ros/jazzy ]; then
        log "  /opt/ros/jazzy 存在 [OK]"
    else
        warn "  未偵測到 /opt/ros/jazzy"
    fi

    echo "[CHK] apt 套件"
    for p in "${APT_PKGS[@]}"; do
        if dpkg -l "$p" 2>/dev/null | grep -q "^ii"; then
            log "  ${p}: 已安裝 [OK]"
        else
            log "  ${p}: 未安裝"
        fi
    done

    echo "[CHK] 工作區原始碼 ${WS_DIR}/src"
    if [ -d "${WS_DIR}/src" ]; then
        for p in "${BUNDLE_PKGS[@]}"; do
            if [ -d "${WS_DIR}/src/${p}" ]; then
                log "  ${p}: 存在 [OK]"
            else
                log "  ${p}: 缺少"
            fi
        done
    else
        log "  ${WS_DIR}/src 不存在（尚未建立工作區）"
    fi

    echo "[CHK] 已安裝的 teb / costmap_converter"
    for p in teb_local_planner costmap_converter; do
        if ldconfig -p 2>/dev/null | grep -qi "${p}"; then
            log "  ${p}: 系統函式庫 [OK]"
        elif [ -d "/opt/ros/jazzy/share/${p}" ]; then
            log "  ${p}: /opt/ros/jazzy/share [OK]"
        else
            log "  ${p}: 未偵測到（需以 --bundle 或 --upstream 取得）"
        fi
    done
}

# ------------------------------------------------------------------ #
# --apt
# ------------------------------------------------------------------ #
do_apt() {
    [ -d /opt/ros/jazzy ] || die "未偵測到 ROS 2 Jazzy"
    log "以 apt 安裝: ${APT_PKGS[*]}"
    sudo apt-get update -qq || warn "apt-get update 失敗，仍嘗試安裝"
    sudo apt-get install -y "${APT_PKGS[@]}" || die "apt 安裝失敗"
    log "apt 安裝完成。（costmap_converter / teb_local_planner 未收錄於官方 apt，請改用 --bundle）"
}

# ------------------------------------------------------------------ #
# --bundle
# ------------------------------------------------------------------ #
do_bundle() {
    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf "${tmp}"' RETURN

    log "下載第三方套件包:"
    log "  ${BUNDLE_URL}"
    if ! curl -fL --retry 3 --connect-timeout 20 -o "${tmp}/${BUNDLE_FILE}" "${BUNDLE_URL}"; then
        die "下載失敗。請確認網路，或以 WMR_THIRD_PARTY_URL 指定其他來源。"
    fi

    log "解壓 ..."
    tar -xzf "${tmp}/${BUNDLE_FILE}" -C "${tmp}"
    local root="${tmp}/wmr_sim_third_party_v${RELEASE_VERSION}"
    [ -d "${root}/src" ] || die "套件包結構異常，找不到 src/"

    mkdir -p "${WS_DIR}/src"
    for p in "${BUNDLE_PKGS[@]}"; do
        [ -d "${root}/src/${p}" ] || { warn "套件包缺少 ${p}，略過"; continue; }
        rm -rf "${WS_DIR}/src/${p}"
        cp -r "${root}/src/${p}" "${WS_DIR}/src/"
        log "  + src/${p}"
    done

    # 授權合規：一併保存授權全文與聲明
    mkdir -p "${WS_DIR}/third_party_LICENSES"
    cp -r "${root}/LICENSES/." "${WS_DIR}/third_party_LICENSES/" 2>/dev/null || true
    cp -r "${root}/patches/."  "${WS_DIR}/third_party_LICENSES/" 2>/dev/null || true
    cp "${root}/THIRD_PARTY.md" "${WS_DIR}/third_party_LICENSES/" 2>/dev/null || true
    log "授權文件已存至 ${WS_DIR}/third_party_LICENSES/"

    cat << EOF

下一步：
  source /opt/ros/jazzy/setup.bash
  cd ${WS_DIR} && colcon build --symlink-install \\
      --packages-select costmap_converter_msgs costmap_converter \\
                        teb_msgs teb_local_planner \\
                        dwb_core dwb_critics dwb_plugins
EOF
}

# ------------------------------------------------------------------ #
# --upstream
# ------------------------------------------------------------------ #
do_upstream() {
    command -v git >/dev/null || die "需要 git"
    mkdir -p "${WS_DIR}/src"
    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf "${tmp}"' RETURN

    log "clone costmap_converter @ 0.1.2 ..."
    git clone -q --depth 1 --branch 0.1.2 \
        https://github.com/rst-tu-dortmund/costmap_converter.git \
        "${tmp}/costmap_converter" || die "clone costmap_converter 失敗"

    log "clone teb_local_planner @ ros2-master ..."
    git clone -q --depth 1 --branch ros2-master \
        https://github.com/rst-tu-dortmund/teb_local_planner.git \
        "${tmp}/teb_local_planner" || die "clone teb_local_planner 失敗"

    rm -rf "${WS_DIR}/src/costmap_converter" "${WS_DIR}/src/teb_local_planner"
    mkdir -p "${WS_DIR}/src/costmap_converter" "${WS_DIR}/src/teb_local_planner"
    cp -r "${tmp}/costmap_converter/." "${WS_DIR}/src/costmap_converter/"
    cp -r "${tmp}/teb_local_planner/." "${WS_DIR}/src/teb_local_planner/"
    find "${WS_DIR}/src/costmap_converter" "${WS_DIR}/src/teb_local_planner" \
         -maxdepth 1 -name ".git" -prune -exec rm -rf {} + 2>/dev/null || true

    log "下載在地補丁 ..."
    local patch_file="${tmp}/wmrsim-jazzy-portability.patch"
    if curl -fL --connect-timeout 20 -o "${patch_file}" "${UPSTREAM_PATCH_URL}"; then
        log "套用補丁 (p1) ..."
        if ( cd "${WS_DIR}" && patch -p1 --forward < "${patch_file}" ); then
            log "補丁套用完成"
        else
            warn "補丁未完全套用；Ubuntu 24.04 上可能需手動處理（cv_bridge.hpp、multiarch 路徑）"
        fi
        mkdir -p "${WS_DIR}/third_party_LICENSES"
        cp "${patch_file}" "${WS_DIR}/third_party_LICENSES/"
    else
        warn "補丁下載失敗，請手動套用 patches/wmrsim-jazzy-portability.patch"
    fi

    warn "dwb_* 請改用 --apt 安裝，或自 navigation2 (jazzy) 取得。"
    cat << EOF

下一步：
  source /opt/ros/jazzy/setup.bash
  cd ${WS_DIR} && colcon build --symlink-install
  # 若尚未有 dwb_*：bash $0 --apt
EOF
}

# ------------------------------------------------------------------ #
[ "${DO_CHECK}" -eq 1 ]    && do_check
[ "${DO_APT}" -eq 1 ]      && do_apt
[ "${DO_BUNDLE}" -eq 1 ]   && do_bundle
[ "${DO_UPSTREAM}" -eq 1 ] && do_upstream
exit 0
