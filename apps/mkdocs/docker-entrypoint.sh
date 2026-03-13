#!/usr/bin/env bash

set -e

# Build the static site before serving
mkdocs build

# Evaluating passed command:
exec "$@"
