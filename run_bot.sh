#!/bin/bash
export FLASK_APP=tbot.py
export FLASK_DEBUG=1
source /home/$USER/dev/github/tbot/.venv/bin/activate
pushd /home/$USER/dev/github/tbot
python /home/$USER/dev/github/tbot/distractobot.py --run
popd
deactivate
