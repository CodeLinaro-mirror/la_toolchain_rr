#!/usr/bin/env bash

set -e
set -x

THIS_DIR=$(cd "$(dirname "$0")" && pwd)
TOP=$THIS_DIR/../../..
PYTHON=$TOP/prebuilts/python/linux-x86/bin/python3
$PYTHON $THIS_DIR/build.py "$@"