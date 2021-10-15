#!/bin/bash

amixer set PCM 100%

cd /home/pi/papaguy-tamer
git pull
source ./venv/bin/activate
nohup python -m papaguy-tamer &

exit 0

# connect to papaguy i.e. like
# curl localhost:8080/autoconn
