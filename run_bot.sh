#!/bin/bash
<<<<<<< HEAD
export FLASK_APP=tbot.py
export FLASK_DEBU=1
. /home/$USER/dev/github/tbot/.venv/bin/activate
echo "activated"
pushd /home/$USER/dev/github/tbot
python /home/$USER/dev/github/tbot/distractobot.py --run
=======
source $HOME/dev/github/tbot/.venv/bin/activate
pushd $HOME/dev/github/tbot
export FLASK_APP=tbot.py
export FLASK_DEBUG=1
python $HOME/dev/github/tbot/distractobot.py
>>>>>>> 215771e1f6c6e29ff4485d6e827c69e7e4a266f2
popd
deactivate
