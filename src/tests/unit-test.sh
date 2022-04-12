#!/bin/sh

USE_VENV=$1 #any argument will trigger using the virtual env
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

echo $SCRIPTPATH

cd "$SCRIPTPATH"


if [ ! -z "$USE_VENV" ] ; then
	pipenv shell
fi

cd ../
pytest

# check lint rules (configured in .flake8)
pipenv run flake8

# check code style (configured in pyproject.toml)
pipenv run black --check .
