#!/bin/bash -x

mypy --config-file pyproject.toml --check-untyped-defs --explicit-package-bases tests examples
