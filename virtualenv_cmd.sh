#!/bin/bash

VIRTUAL_ENV=$1
WORKING_DIRECTORY=$2
if [ -z $VIRTUAL_ENV ] || [ -z $WORKING_DIRECTORY ]; then
  echo "usage: $0 </path/to/virtualenv> </working_directory> <cmd>"
  exit 1
fi

. $VIRTUAL_ENV/bin/activate
pushd $WORKING_DIRECTORY
shift 2
exec "$@"
popd
deactivate
