.PHONY: all clean build test unit install

all: test build

clean:
	rm -rf build dist surrect.egg-info

build:
	./setup.py bdist_wheel

test: unit

unit:
	python -m unittest discover -t ./ -s ./test/

install:
	pip install --user -I ./dist/surrect-*.whl
