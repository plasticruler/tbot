#!/bin/bash
VIRTUAL_ENV=$1
WORKING_DIRECTORY=$2
if [ -z $VIRTUAL_ENV ] || [ -z $WORKING_DIRECTORY ]; then
  echo "usage: $0 </path/to/virtualenv> </working_directory> <cmd>"
  exit 1
fi
echo "activating virtual env with $VIRTUAL_ENV/bin/activate"
. $VIRTUAL_ENV/bin/activate
echo "activated"
pushd $WORKING_DIRECTORY
echo "pushd $WORKING_DIRECTORY"
shift 2
echo "$@"
exec "$@"
popd
deactivate