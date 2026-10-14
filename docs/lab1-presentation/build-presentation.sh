#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

marp --pdf --allow-local-files "$SCRIPT_DIR/presentation.md"
