#!/bin/bash
export FLASK_APP=tbot.py
export FLASK_DEBU=1
. /home/$USER/dev/github/tbot/.venv/bin/activate
echo "activated"
pushd /home/$USER/dev/github/tbot
python /home/$USER/dev/github/tbot/distractobot.py --run
popd
deactivate
