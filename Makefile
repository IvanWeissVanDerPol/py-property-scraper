.PHONY: install run run-source clean-data clean quality-report merge csv catalog pipeline lint test

install:
	python3 -m venv venv && venv/bin/pip install -r requirements.txt

run:
	venv/bin/python -m src.orchestrator

run-source:
	venv/bin/python -m src.orchestrator --source $(S)

clean-data:
	rm -rf data/*

clean:
	rm -rf data/* __pycache__ .pytest_cache

quality-report:
	venv/bin/python -m src.utils.clean

merge:
	venv/bin/python -m src.utils.merge merge

csv:
	venv/bin/python -m src.utils.merge csv

catalog:
	venv/bin/python -m src.utils.merge catalog

pipeline: quality-report merge csv catalog
	@echo "Pipeline complete"

lint:
	venv/bin/python -m py_compile src/scrapers/*.py src/utils/*.py

test:
	venv/bin/pytest tests/ -v
