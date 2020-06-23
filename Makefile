SRC=.

.PHONY: all
all: format test

.PHONY: format
format:
	python3 -m black --line-length=120 --target-version=py27 -v $(SRC)

.PHONY: test
test: clean
	tox $(SRC)

.PHONY: coverage
coverage:
	pytest --cov-report=html --cov $(SRC)

.PHONY: clean
clean:
	rm -rf .pytest_cache/
	find $(SRC) -maxdepth 2 -name '*.pyc' -delete
