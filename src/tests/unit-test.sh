#!/bin/sh

USE_VENV=$1 #any argument will trigger using the virtual env
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

echo $SCRIPTPATH

cd "$SCRIPTPATH"


if [ ! -z "$USE_VENV" ] ; then
	. ../../venv/bin/activate
fi

#Note: pytest MUST be run from the src directory because of the src/config.ini that is required for the grlc library...
cd ../
pytest tests/unit_tests