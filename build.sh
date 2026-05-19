#!/bin/bash
# Build script for both Python and Go versions of xhs CLI
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "=== Building Python version ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -e ".[dev]" -q
echo "Python version: $(xhs --version)"
echo ""

echo "=== Building Go version ==="
export GOROOT=/usr/lib/go
export PATH=$GOROOT/bin:$PATH
export GOPATH="$DIR/xhs-cli-go/.gopath"
export GOBIN="$DIR/xhs-cli-go/bin"
cd "$DIR/xhs-cli-go"
go build -o bin/xhs ./cmd/xhs/
echo "Go version: $(./bin/xhs --help 2>&1 | head -1)"
echo ""

echo "=== Done ==="
echo "Python: $DIR/xhs-py.sh"
echo "Go:     $DIR/xhs-go.sh"
