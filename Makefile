VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: venv run test demo clean test-no-venv test-ci test-integration2-live

venv:
	python3 -m venv $(VENV)
	$(PIP) install -e .

run:
	$(PYTHON) -m uvicorn emotiond.api:app --host 127.0.0.1 --port 18080

test:
	$(PYTHON) -m pytest tests/

test-no-venv:
	python3 -m pytest tests/

demo:
	$(PYTHON) scripts/demo_cli.py

clean:
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info

# Run CI test suite locally
test-ci: ## Run CI test suite locally
	./tools/test_emotiond_deterministic.sh agent test_ci care
	./tools/test_emotiond_deterministic.sh agent test_ci betrayal
	./tools/test_identity_separation.sh
	./tools/test_enforcer_bypass.sh

# Start local emotiond service and run Integration-2 live tests
test-integration2-live:
	@set -e; \
	PIDFILE=.emotiond-test.pid; \
	$(PYTHON) -m uvicorn emotiond.api:app --host 127.0.0.1 --port 18080 >/tmp/emotiond-test.log 2>&1 & echo $$! > $$PIDFILE; \
	trap "kill `cat $$PIDFILE` 2>/dev/null || true; rm -f $$PIDFILE" EXIT; \
	for i in $$(seq 1 40); do \
		if curl -fsS http://127.0.0.1:18080/health >/dev/null; then break; fi; \
		sleep 0.25; \
	done; \
	EMOTIOND_URL=http://127.0.0.1:18080 $(PYTHON) -m pytest tests/test_openclaw_integration2.py -q
