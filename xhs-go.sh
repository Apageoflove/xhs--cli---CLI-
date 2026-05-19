#!/bin/bash
# Go version wrapper
# Usage: ./xhs-go.sh [command] [args...]
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/xhs-cli-go/bin/xhs" "$@"
