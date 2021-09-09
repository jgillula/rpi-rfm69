#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

cd "$SCRIPT_DIR"
python3 -m venv venv_build
source venv_build/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build twine
cd ..
changelog_version=$(head -n 3 CHANGELOG.md | tail -n 1 | sed 's/##//' | tr -d '[:space:]')
version_string=$(cat VERSION | tr -d '[:space:]')
if [[ "$version_string" == *"$changelog_version"* ]]; then
    rm -rf dist
    python3 -m build
else
    echo
    echo "ERROR: VERSION=$version_string, but the changelog has only been updated to version $changelog_version"
fi

