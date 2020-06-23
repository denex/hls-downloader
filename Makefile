SRC=.

.PHONY: all
all: format test

.PHONY: format
format:
	python3 -m black --line-length=120 --target-version=py27 -v $(SRC)

.PHONY: test
test:
	tox $(SRC)

.PHONY: clean
clean:
	find . -name '*.pyc'
