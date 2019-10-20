#!/bin/bash
. /home/romeo/dev/github/tbot/.venv/bin/activate
echo "activated"
pushd /home/romeo/dev/github/tbot
. /home/romeo/dev/github/tbot/distractobot.py
popd
deactivate
