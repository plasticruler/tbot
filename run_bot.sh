#!/bin/bash
source $HOME/dev/github/tbot/.venv/bin/activate
pushd $HOME/dev/github/tbot
export FLASK_APP=tbot.py
export FLASK_DEBUG=1
python $HOME/dev/github/tbot/distractobot.py
popd
deactivate
