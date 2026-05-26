.PHONY: dev lint type-check test test-integration test-e2e build all

dev:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

type-check:
	mypy src/ --strict

test:
	pytest tests/ -v --cov=src/couplingguard --cov-report=term-missing --cov-report=xml

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

build:
	python -m build

all: lint type-check test
