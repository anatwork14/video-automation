PYTHON ?= python3
.PHONY: deps check strict test test-external prepare report draft hashes render qa release
deps:
	$(PYTHON) -m pip install -r requirements.txt
check:
	$(PYTHON) validate.py
strict:
	$(PYTHON) validate.py --strict
test:
	$(PYTHON) -m unittest discover -s tests -v
test-external:
	RUN_EXTERNAL=1 $(PYTHON) -m unittest discover -s tests_external -v
prepare:
	$(PYTHON) pipeline.py prepare
report:
	$(PYTHON) footage_report.py
draft:
	$(PYTHON) draft.py
hashes:
	$(PYTHON) review_hashes.py
render:
	$(PYTHON) pipeline.py render
qa:
	$(PYTHON) qa.py
release:
	$(PYTHON) release_check.py --export-final
