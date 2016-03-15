.PHONY: all build test unit

all: test build

build:
	./setup.py build


test: unit

unit:
	python -m unittest discover -t ./ -s ./test/
