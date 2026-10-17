#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../.marprc.yml"

marp --config-file "$CONFIG_FILE" --pdf --allow-local-files "$SCRIPT_DIR/presentation.md"
