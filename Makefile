.PHONY: setup build test clean

setup:
	git config core.hooksPath .githooks

build:
	cargo build -p matplotlib-python

test: build
	target/debug/matplotlib-python -m pytest python/matplotlib/tests/

clean:
	cargo clean
