# papaguy-tamer
intermediate-level code to parse BeRo's json output and talk with the papaguy-itself
qm210, one week before UC11

was written with Python 3.9, but seems to work with Python 3.7.3 (current standard Python3 for Raspberry Pi OS). Make sure to use the right interpreter for your system:
* you might need to write python3, pip3 and pay attention to your $PATH
* *the following seems not to be required with the current Raspberry Pi OS (2021-05-07);* but you might need some general packages like python3-dev, libasound2-dev (for portaudio), ... installed via your package manager beforehand, in case the following "pip install -r requirements.txt" isn't enough.

then, after checkout, go the virtualenv way:

```
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

run with
```
python -m papaguy-tamer
```

let's see whether that works.
enjoy, QM

---
You might need some script for autorun. What worked for UC was the following script (and I guess it was called in the .bashrc, but I guess you could also call it inside /etc/rc.local or via a @reboot line in your crontab, or...)

```
#!/bin/bash

# it might be that your default alsamixer volume is not 100%. which is, of course, garbage.
amixer set PCM 100%

# adjust working directory, and maybe python -> python3
cd /home/pi/papaguy-tamer
git pull
source ./venv/bin/activate
nohup python -m papaguy-tamer &

exit 0
```