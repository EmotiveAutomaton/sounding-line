# Sounding Line — convenience targets.
# On Windows without `make`, run the underlying commands directly; each is a single line.

PYTHON ?= .venv/Scripts/python.exe

.PHONY: help locks test hashes gate1 clean

help:           ## list targets
	@grep -E '^[a-z0-9]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

locks:          ## verify every hash-locked artifact still matches (run before anything else)
	$(PYTHON) -m soundingline.locks

test:           ## full test suite; includes the lock checks and the control on the control
	$(PYTHON) -m pytest -q

hashes:         ## print current hashes of the lockable artifacts, for a deviation entry
	$(PYTHON) -c "from soundingline.hashlock import hash_file; \
	  [print(f'{hash_file(p)}  {p}') for p in ['SOUNDING_LINE_SPEC.md', \
	   'docs/gate0/LITERATURE.md','soundingline/family/family_v1.yaml','prereg/gate1.py'])]"

gate1:          ## print the Gate 1 pre-registration hashes
	$(PYTHON) prereg/gate1.py

clean:          ## remove caches; never touches results/ or corpora/
	$(PYTHON) -c "import shutil,pathlib; [shutil.rmtree(p,ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	$(PYTHON) -c "import shutil; shutil.rmtree('.pytest_cache',ignore_errors=True)"
