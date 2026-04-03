#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

./scripts/v2/backup_data.sh
./scripts/v2/compose_up.sh
./scripts/v2/health_check.sh

echo "V2 发布脚本执行完成。建议继续运行 ./scripts/v2/smoke_test.sh 做业务层校验。"
