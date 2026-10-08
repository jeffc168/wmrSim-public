#!/usr/bin/env bash
# ==============================================================================
# 組出第三方 ROS 2 原始碼包（可重現）
#
#   wmr_sim_third_party_v<version>.tar.gz 內容：
#     install.sh                  （packaging/third_party/install.sh，已修 ROS Jazzy set -u 問題）
#     src/{costmap_converter,teb_local_planner,dwb_core,dwb_critics,dwb_plugins}
#     LICENSES/  patches/  THIRD_PARTY.md
#
# 用法:
#   bash tools/pack_third_party_bundle.sh [--src DIR] [--out DIR] [--version X.Y.Z]
#
# 來源預設 ${WMR_THIRD_PARTY_SRC_DIR:-<repo>/../wmrSim/src}；
# 該目錄需含上述 5 個頂層套件目錄（costmap_converter_msgs / teb_msgs 為巢狀）。
#
# 產出後可用 gh 發布／替換 Release 資產：
#   gh release upload v<version> dist/wmr_sim_third_party_v<version>.tar.gz --clobber
# ==============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$(readlink -f -- "$0")")" && pwd)"
ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

VERSION="1.0.0"
if [ -f "${ROOT}/VERSION" ]; then
    VERSION="$(tr -d '[:space:]' < "${ROOT}/VERSION")"
fi
SRC_DIR="${WMR_THIRD_PARTY_SRC_DIR:-$(cd -- "${ROOT}/.." && pwd)/wmrSim/src}"
OUT_DIR="${ROOT}/dist"

BUNDLE_DIRS=(costmap_converter teb_local_planner dwb_core dwb_critics dwb_plugins)

usage() { sed -n '2,20p' "$0"; }
die() { echo "[PACK-THIRD-PARTY][ERROR] $*" >&2; exit 1; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --src)     SRC_DIR="$2"; shift 2 ;;
        --out)     OUT_DIR="$2"; shift 2 ;;
        --version) VERSION="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "未知參數：$1" ;;
    esac
done

BUNDLE_NAME="wmr_sim_third_party_v${VERSION}"
[ -d "${SRC_DIR}" ] || die "找不到第三方原始碼目錄：${SRC_DIR}（可用 --src 或 WMR_THIRD_PARTY_SRC_DIR 指定）"
[ -f "${ROOT}/packaging/third_party/install.sh" ] || die "缺少 packaging/third_party/install.sh"
[ -d "${ROOT}/LICENSES" ] || die "缺少 LICENSES/"
[ -f "${ROOT}/THIRD_PARTY.md" ] || die "缺少 THIRD_PARTY.md"

echo "======================================================================"
echo " 第三方原始碼包打包"
echo "   來源      : ${SRC_DIR}"
echo "   輸出      : ${OUT_DIR}/${BUNDLE_NAME}.tar.gz"
echo "   版本      : ${VERSION}"
echo "======================================================================"

STAGE="$(mktemp -d)"
cleanup() { rm -rf -- "${STAGE}"; }
trap cleanup EXIT

mkdir -p "${STAGE}/${BUNDLE_NAME}/src"
for d in "${BUNDLE_DIRS[@]}"; do
    [ -d "${SRC_DIR}/${d}" ] || die "缺少 ${SRC_DIR}/${d}"
    cp -r "${SRC_DIR}/${d}" "${STAGE}/${BUNDLE_NAME}/src/"
    echo "  + src/${d}"
done

cp -r "${ROOT}/LICENSES" "${STAGE}/${BUNDLE_NAME}/"
cp -r "${ROOT}/patches" "${STAGE}/${BUNDLE_NAME}/"
cp "${ROOT}/THIRD_PARTY.md" "${STAGE}/${BUNDLE_NAME}/"
cp "${ROOT}/packaging/third_party/install.sh" "${STAGE}/${BUNDLE_NAME}/install.sh"
chmod +x "${STAGE}/${BUNDLE_NAME}/install.sh"

# 確保不含版本控管或快取產物
find "${STAGE}/${BUNDLE_NAME}" -name '.git' -prune -exec rm -rf {} + 2>/dev/null || true
find "${STAGE}/${BUNDLE_NAME}" -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

mkdir -p "${OUT_DIR}"
# 決定性打包：固定排序／mtime／owner，gzip 不寫入名稱與時間 →
# 相同輸入永遠得到相同 sha256（Release 資產與發行包內嵌副本才會一致）
( cd "${STAGE}" && tar --sort=name --mtime='UTC 2026-01-01' --owner=0 --group=0 --numeric-owner \
    -cf - "${BUNDLE_NAME}" | gzip -9n > "${OUT_DIR}/${BUNDLE_NAME}.tar.gz" )
( cd "${OUT_DIR}" && sha256sum "${BUNDLE_NAME}.tar.gz" > "${BUNDLE_NAME}.tar.gz.sha256" )

echo
echo "[PACK-THIRD-PARTY] 完成："
echo "  ${OUT_DIR}/${BUNDLE_NAME}.tar.gz  ($(stat -c%s "${OUT_DIR}/${BUNDLE_NAME}.tar.gz") bytes)"
echo "  ${OUT_DIR}/${BUNDLE_NAME}.tar.gz.sha256"
echo "  發布／替換資產： gh release upload v${VERSION} ${OUT_DIR}/${BUNDLE_NAME}.tar.gz --clobber"
