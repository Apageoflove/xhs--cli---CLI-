#!/bin/bash
# xhs 交互式终端启动脚本
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/.venv/bin/activate"
exec python3 "$DIR/xhs_repl.py" "$@"
