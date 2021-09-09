#!/bin/bash

cwd=$( pwd )
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

cd "$SCRIPT_DIR"
rm -rf venv_build
rm -rf ../dist
rm -rf ../rpi_rfm69.egg-info

cd "$cwd"
