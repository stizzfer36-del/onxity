.PHONY: bootstrap test smoke doctor

bootstrap:
	./scripts/bootstrap.sh

test:
	PYTHONPATH=. pytest -q

smoke:
	./scripts/smoke_runtime.sh

doctor:
	python -m onxity.cli doctor
