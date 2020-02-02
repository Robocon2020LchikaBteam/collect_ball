#!/bin/bash
sphinx-apidoc -f -o ./sphinx/ .
sphinx-build -b html ./sphinx/ ./docs/