.PHONY: help data-dictionary data-dictionary-serve test

PYTHON ?= python3
ASSETS_PATH ?= tests/integration/wazimap/fixtures
OUTPUT_DIR ?= ./data-dictionary

help:
	@echo "Available targets:"
	@echo "  data-dictionary       Generate static data dictionary site"
	@echo "  data-dictionary-serve Generate and serve data dictionary on localhost:8000"
	@echo "  test                  Run all tests"

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
