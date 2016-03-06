.PHONY: test unit

test: unit

unit:
	python -m unittest discover -t ./ -s ./test/
