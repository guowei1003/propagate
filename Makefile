PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip

.PHONY: bootstrap-backend install-frontend build-frontend migrate-v2 run-v2 compose-up compose-down package-bundle

bootstrap-backend:
	./scripts/v2/bootstrap_backend.sh

install-frontend:
	./scripts/v2/install_frontend.sh

build-frontend:
	./scripts/v2/build_frontend.sh

migrate-v2:
	./scripts/v2/apply_v2_migration.sh

run-v2:
	./scripts/v2/run_v2_api.sh

compose-up:
	./scripts/v2/compose_up.sh

compose-down:
	./scripts/v2/compose_down.sh

package-bundle:
	./scripts/v2/package_bundle.sh $(RUN_ID)

health-check:
	./scripts/v2/health_check.sh

smoke-test:
	./scripts/v2/smoke_test.sh
