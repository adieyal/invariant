.PHONY: help docs docs-serve docs-generate data-dictionary data-dictionary-serve test

PYTHON ?= python3
ASSETS_PATH ?= tests/integration/wazimap/fixtures
OUTPUT_DIR ?= ./data-dictionary
DOCS_DIR ?= ./site

help:
	@echo "Available targets:"
	@echo "  docs                  Build documentation site (output: $(DOCS_DIR))"
	@echo "  docs-serve            Serve documentation on localhost:8000 with live reload"
	@echo "  docs-generate         Regenerate auto-generated docs from code"
	@echo "  data-dictionary       Generate static data dictionary site"
	@echo "  data-dictionary-serve Generate and serve data dictionary on localhost:8000"
	@echo "  test                  Run all tests"

docs-generate:
	$(PYTHON) scripts/generate_docs.py

docs: docs-generate
	mkdocs build -d $(DOCS_DIR)
	@echo "Documentation built at $(DOCS_DIR)/index.html"

docs-serve: docs-generate
	mkdocs serve

data-dictionary:
	PYTHONPATH=src $(PYTHON) -m invariant_contrib.datadictionary export \
		--assets $(ASSETS_PATH) \
		--output $(OUTPUT_DIR) \
		--with-renderer
	@echo "Data dictionary generated at $(OUTPUT_DIR)/index.html"

data-dictionary-serve: data-dictionary
	@echo "Serving data dictionary at http://localhost:8000"
	$(PYTHON) -m http.server 8000 -d $(OUTPUT_DIR)

test:
	$(PYTHON) -m pytest tests/ -q
