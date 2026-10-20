PYTHON ?= python3
DATA = $(wildcard data/*.json)
LOCALES = en fr

.PHONY: render check examples test release install

# Plain visuals render once; card definitions render once per locale.
define run_all
  set -e; for f in $(DATA); do \
    if grep -q '"locales"' $$f; then \
      for loc in $(LOCALES); do \
        $(1) --data $$f --locale $$loc; \
      done; \
    else \
      $(1) --data $$f; \
    fi; \
  done
endef

render: $(DATA)
	$(call run_all,$(PYTHON) engine/render.py)

check: render
	$(call run_all,$(PYTHON) tools/ocr_check.py)

examples: check

test:
	$(PYTHON) -m pytest tests -q

install:
	$(PYTHON) -m pip install -e .

release: test
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*
