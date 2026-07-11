.PHONY: setup test smoke run watch clean-build

setup:
	./scripts/setup.sh

test:
	.venv/bin/pytest -q

smoke:
	.venv/bin/mt-run --episodes 4 --workers 4 --max-steps 3000

run:
	.venv/bin/mt-run --episodes 100 --workers 4

watch:
	.venv/bin/mt-watch

clean-build:
	rm -rf vendor/nle/build vendor/nle/_skbuild

