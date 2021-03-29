# Autodocumented Makefile
# see: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html

# GLOBAL VARIABLES
# Set Virtualenv directory name
VENV = "venv"

CHECK_CMAKE = $(shell command -v cmake 2> /dev/null)
CHECK_OTB = $(shell command -v otbcli_ReadImageInfo 2> /dev/null)

CHECK_NUMPY = $(shell ${VENV}/bin/python -m pip list|grep numpy)
CHECK_FIONA = $(shell ${VENV}/bin/python -m pip list|grep Fiona)
CHECK_RASTERIO = $(shell ${VENV}/bin/python -m pip list|grep rasterio)
CHECK_PYGDAL = $(shell ${VENV}/bin/python -m pip list|grep pygdal)

GDAL_VERSION = $(shell gdal-config --version)

# TARGETS
.PHONY: help venv install test lint format docs docker clean

help: ## this help
	@echo "      CARS MAKE HELP"
	@echo "  Dependencies: Install OTB and VLFEAT before !\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

check: ## check if cmake, OTB, VLFEAT, GDAL is installed
	@[ "${CHECK_CMAKE}" ] || ( echo ">> cmake not found"; exit 1 )
	@[ "${CHECK_OTB}" ] || ( echo ">> OTB not found"; exit 1 )
	@[ "${OTB_APPLICATION_PATH}" ] || ( echo ">> OTB_APPLICATION_PATH is not set"; exit 1 )
	@[ "${GDAL_DATA}" ] || ( echo ">> GDAL_DATA is not set"; exit 1 )
	@[ "${GDAL_VERSION}" ] || ( echo ">> GDAL_VERSION is not set"; exit 1 )
	@[ "${VLFEAT_INCLUDE_DIR}" ] || ( echo ">> VLFEAT_INCLUDE_DIR is not set"; exit 1 )

venv: check ## create virtualenv in "venv" dir if not exists
	@test -d ${VENV} || virtualenv -p `which python3` ${VENV}
	@${VENV}/bin/python -m pip install --upgrade pip setuptools # no check to upgrade each time
	@touch ${VENV}/bin/activate

install-deps: venv
	@[ "${CHECK_NUMPY}" ] ||${VENV}/bin/python -m pip install --upgrade cython numpy
	@[ "${CHECK_FIONA}" ] ||${VENV}/bin/python -m pip install --no-binary fiona fiona
	@[ "${CHECK_RASTERIO}" ] ||${VENV}/bin/python -m pip install --no-binary rasterio rasterio
	@[ "${CHECK_PYGDAL}" ] ||${VENV}/bin/python -m pip install pygdal==$(GDAL_VERSION).*

install: install-deps  ## install and set env
	@test -f ${VENV}/bin/cars || ${VENV}/bin/pip install --verbose .
	@echo "\n --> CARS installed in virtualenv ${VENV}"
	@chmod +x ${VENV}/bin/register-python-argcomplete
	@echo "CARS venv usage : source ${VENV}/bin/activate; source ${VENV}/bin/env_cars.sh; cars -h"

install-dev: install-deps ## install cars in dev mode and set env
	@test -f ${VENV}/bin/cars || ${VENV}/bin/pip install --verbose -e .[dev]
	@echo "\n --> CARS installed in virtualenv ${VENV}"
	@test -f .git/hooks/pre-commit || echo "  Install pre-commit hook"
	@test -f .git/hooks/pre-commit || ${VENV}/bin/pre-commit install -t pre-commit
	@chmod +x ${VENV}/bin/register-python-argcomplete
	@echo "CARS venv usage : source ${VENV}/bin/activate; source ${VENV}/bin/env_cars.sh; cars -h"

test: install-dev ## run all tests (depends install) from dev mode
	@echo "Please source ${VENV}/bin/env_cars.sh before launching tests\n"
	@${VENV}/bin/pytest -m "unit_tests or pbs_cluster_tests" -o log_cli=true -o log_cli_level=INFO --cov-config=.coveragerc --cov-report html --cov

lint: install-dev  ## run lint tools (depends install)
	@${VENV}/bin/isort --check **/*.py
	@${VENV}/bin/black --check **/*.py
	@${VENV}/bin/flake8 **/*.py
	@${VENV}/bin/pylint **/*.py

format: install-dev  ## run black and isort (depends install)
	@${VENV}/bin/isort **/*.py
	@${VENV}/bin/black **/*.py

docs:  ## build sphinx documentation (requires doc venv TODO)
	@cd docs/ && make clean && make html && cd ..

docker: ## Build docker image (and check Dockerfile)
	@echo "Check Dockerfile with hadolint"
	@docker pull hadolint/hadolint
	@docker run --rm -i hadolint/hadolint < Dockerfile
	@echo "Build Docker image"
	@docker build -t cars .

clean: ## clean: remove venv, cars build, cache, ...
	@rm -rf ${VENV}
	@rm -rf dist
	@rm -rf build
	@rm -rf cars.egg-info
	@rm -rf **/__pycache__
	@rm -rf .eggs
	@rm -rf dask-worker-space/
	@rm .coverage
	@rm -rf .coverage.*