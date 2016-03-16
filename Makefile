.PHONY: all clean build test unit

all: test build

clean:
	rm -rf build dist

build:
	./setup.py bdist_wheel

test: unit

unit:
	python -m unittest discover -t ./ -s ./test/
