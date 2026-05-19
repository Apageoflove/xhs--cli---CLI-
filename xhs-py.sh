#!/bin/bash
# Python version wrapper
# Usage: ./xhs-py.sh [command] [args...]
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/.venv/bin/activate"
exec xhs "$@"
