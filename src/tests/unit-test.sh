#!/bin/sh

USE_VENV=$1 #any argument will trigger using the virtual env
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

echo $SCRIPTPATH

cd "$SCRIPTPATH"


if [ ! -z "$USE_VENV" ] ; then
	pipenv shell
fi

#Note: pytest MUST be run from the src directory because of the src/config.ini that is required for the grlc library...
cd ../
pytest tests/unit_tests --cov


# quit if there are Python syntax errors or undefined names
pipenv run flake8 . --count --select=E9,F63,F7,F82,W191 --show-source --statistics
# exit-zero treats all errors as warnings
pipenv run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics --extend-ignore=E203,E501 --select=C,E,F,W,B,B950