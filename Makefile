PYTHON ?= python3
DATA = $(wildcard data/*.json)

.PHONY: render check examples test release install

render: $(DATA)
	@set -e; for f in $(DATA); do $(PYTHON) engine/render.py --data $$f; done

check: render
	@set -e; for f in $(DATA); do $(PYTHON) tools/ocr_check.py --data $$f; done

examples: check

test:
	$(PYTHON) -m pytest tests -q

install:
	$(PYTHON) -m pip install -e .

release: test
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*
