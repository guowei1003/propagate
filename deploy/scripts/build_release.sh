#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

OUTPUT_DIR=""
BUNDLE_PREFIX="propagate-release"
RUN_TESTS="0"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmjs.org/}"

usage() {
  cat <<'EOF'
用法:
  deploy/scripts/build_release.sh --output-dir <目录> [选项]

选项:
  -o, --output-dir <目录>   必填，构建产物输出目录
  -n, --bundle-name <名称>  可选，产物名前缀，默认 propagate-release
      --with-tests          可选，构建前执行后端 pytest 和前端 vitest
      --npm-registry <URL>  可选，覆盖 npm registry
  -h, --help                显示帮助

产物:
  1. <输出目录>/<名称>-<时间戳>/        解包后的发布目录
  2. <输出目录>/<名称>-<时间戳>.tar.gz  压缩包
EOF
}

log() {
  printf '[build-release] %s\n' "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf '缺少命令: %s\n' "$1" >&2
    exit 1
  fi
}

copy_tree() {
  local source="$1"
  local target="$2"
  mkdir -p "$target"
  cp -R "$source" "$target"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    -n|--bundle-name)
      BUNDLE_PREFIX="${2:-}"
      shift 2
      ;;
    --with-tests)
      RUN_TESTS="1"
      shift
      ;;
    --npm-registry)
      NPM_REGISTRY="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '未知参数: %s\n' "$1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$OUTPUT_DIR" ]]; then
  printf '必须指定 --output-dir\n' >&2
  usage
  exit 1
fi

require_cmd uv
require_cmd node
require_cmd npm
require_cmd tar

TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
RELEASE_NAME="${BUNDLE_PREFIX}-${TIMESTAMP}"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT_DIR")" && pwd)/$(basename "$OUTPUT_DIR")"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/propagate-release.XXXXXX")"
STAGE_DIR="${WORK_DIR}/${RELEASE_NAME}"
WEB_DIR="${ROOT_DIR}/apps/web"

cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

mkdir -p "$OUTPUT_DIR" "$STAGE_DIR"

log "输出目录: ${OUTPUT_DIR}"
log "临时工作目录: ${WORK_DIR}"
log "同步 Python 依赖"
if [[ "$RUN_TESTS" == "1" ]]; then
  (cd "$ROOT_DIR" && uv sync --all-extras --all-groups)
else
  (cd "$ROOT_DIR" && uv sync)
fi

if [[ "$RUN_TESTS" == "1" ]]; then
  log "运行后端测试"
  (cd "$ROOT_DIR" && .venv/bin/pytest apps/api/tests -q)
fi

log "安装前端依赖"
if [[ -f "${WEB_DIR}/package-lock.json" ]]; then
  if ! (cd "$WEB_DIR" && npm ci --registry="$NPM_REGISTRY"); then
    log "npm ci 失败，回退到 npm install"
    rm -rf "${WEB_DIR}/node_modules"
    (cd "$WEB_DIR" && npm install --registry="$NPM_REGISTRY")
  fi
else
  (cd "$WEB_DIR" && npm install --registry="$NPM_REGISTRY")
fi

if [[ "$RUN_TESTS" == "1" ]]; then
  log "运行前端测试"
  (cd "$WEB_DIR" && npm test)
fi

log "构建前端静态资源"
(cd "$WEB_DIR" && npm run build)

log "编译 Python 源码"
(cd "$ROOT_DIR" && .venv/bin/python -m compileall -q apps/api/app)

log "整理发布目录"
mkdir -p "${STAGE_DIR}/apps"

copy_tree "${ROOT_DIR}/apps/api" "${STAGE_DIR}/apps"
mkdir -p "${STAGE_DIR}/apps/web"
copy_tree "${ROOT_DIR}/apps/web/dist" "${STAGE_DIR}/apps/web"
cp "${ROOT_DIR}/apps/web/package.json" "${STAGE_DIR}/apps/web/package.json"
cp "${ROOT_DIR}/apps/web/package-lock.json" "${STAGE_DIR}/apps/web/package-lock.json"
if [[ -f "${ROOT_DIR}/AGENTS.md" ]]; then
  cp "${ROOT_DIR}/AGENTS.md" "${STAGE_DIR}/AGENTS.md"
fi
copy_tree "${ROOT_DIR}/agents" "${STAGE_DIR}"
copy_tree "${ROOT_DIR}/deploy" "${STAGE_DIR}"
copy_tree "${ROOT_DIR}/docs" "${STAGE_DIR}"
copy_tree "${ROOT_DIR}/evals" "${STAGE_DIR}"
cp "${ROOT_DIR}/README.md" "${STAGE_DIR}/README.md"
if [[ -f "${ROOT_DIR}/dev.sh" ]]; then
  cp "${ROOT_DIR}/dev.sh" "${STAGE_DIR}/dev.sh"
fi
cp "${ROOT_DIR}/pyproject.toml" "${STAGE_DIR}/pyproject.toml"
cp "${ROOT_DIR}/uv.lock" "${STAGE_DIR}/uv.lock"
cp "${ROOT_DIR}/.env.example" "${STAGE_DIR}/.env.example"

cat > "${STAGE_DIR}/BUILD_INFO.txt" <<EOF
release_name=${RELEASE_NAME}
build_time=${TIMESTAMP}
root_dir=${ROOT_DIR}
npm_registry=${NPM_REGISTRY}
run_tests=${RUN_TESTS}
EOF

log "复制到目标目录"
rm -rf "${OUTPUT_DIR:?}/${RELEASE_NAME}"
cp -R "${STAGE_DIR}" "${OUTPUT_DIR}/"

log "生成压缩包"
tar -C "$WORK_DIR" -czf "${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz" "${RELEASE_NAME}"

log "完成"
printf 'release_dir=%s\n' "${OUTPUT_DIR}/${RELEASE_NAME}"
printf 'release_tar=%s\n' "${OUTPUT_DIR}/${RELEASE_NAME}.tar.gz"
