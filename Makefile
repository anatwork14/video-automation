PYTHON ?= python3
.PHONY: deps check test prepare render
deps:
	$(PYTHON) -m pip install -r requirements.txt
check:
	$(PYTHON) validate.py
test:
	$(PYTHON) -m unittest discover -s tests -v
prepare:
	$(PYTHON) pipeline.py prepare
render:
	$(PYTHON) pipeline.py render
