PY       := python3.14
VENV     := .venv
VPY      := $(VENV)/bin/python
VPIP     := $(VENV)/bin/pip
PKG_SRC  := src

.PHONY: help venv install install-dev clean prd001 prd002 imagery-ingest docker-build docker-run

help:
	@echo "make venv          — create .venv with Python 3.14"
	@echo "make install       — install runtime deps into .venv"
	@echo "make install-dev   — install runtime + dev deps"
	@echo "make prd001        — run PRD-001 pipeline (data foundation)"
	@echo "make prd002        — run PRD-002 pipeline (buildings intermediate model)"
	@echo "make imagery-ingest PARCEL=N-44  — scaffold image manifest for parcel"
	@echo "make docker-build  — build the project Docker image"
	@echo "make docker-run    — open a shell inside the Docker container"
	@echo "make clean         — remove .venv + generated artefacts"

venv:
	$(PY) -m venv $(VENV)
	$(VPIP) install --upgrade pip setuptools wheel

install: venv
	$(VPIP) install -r requirements.txt

install-dev: venv
	$(VPIP) install -r requirements.txt
	$(VPIP) install -e ".[dev]"

prd001:
	PYTHONPATH=$(PKG_SRC) $(VPY) -m hums prd001

prd002:
	PYTHONPATH=$(PKG_SRC) $(VPY) -m hums prd002

prd003:
	PYTHONPATH=$(PKG_SRC) $(VPY) -m hums prd003

render-building:
	@test -n "$(PARCEL)" || (echo "usage: make render-building PARCEL=N-40"; exit 2)
	PYTHONPATH=$(PKG_SRC) $(VPY) -m hums render-building $(PARCEL)

diagnostic-map:
	PYTHONPATH=$(PKG_SRC) $(VPY) -m hums diagnostic-map

imagery-ingest:
	@test -n "$(PARCEL)" || (echo "usage: make imagery-ingest PARCEL=N-44"; exit 2)
	PYTHONPATH=$(PKG_SRC) $(VPY) -m hums imagery-ingest $(PARCEL)

docker-build:
	docker build -t hums:latest .

docker-run:
	docker run --rm -it -v $(PWD):/work -w /work hums:latest bash

clean:
	rm -rf $(VENV) data/parsed __pycache__
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
