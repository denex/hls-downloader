SRC=.

.PHONY: all
all: format test

.PHONY: format
format:
	uv format -- --line-length 120 $(SRC)

.PHONY: test
test: clean
	tox $(SRC)

.PHONY: coverage
coverage:
	uv run pytest --cov-report=html --cov $(SRC)

.PHONY: clean
clean:
	rm -rf .pytest_cache/
	find $(SRC) -maxdepth 2 -name '*.pyc' -delete
