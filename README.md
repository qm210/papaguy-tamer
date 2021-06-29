# papaguy-tamer
intermediate-level code to parse BeRo's json output and talk with the papaguy-itself
qm210, one week before UC11

needs Python 3.9, and make sure to use the right interpreter for your system (you might need to write python3.9, pip3.9 and pay attention to your $PATH)

you might need some general packages like python3-dev, libasound2-dev (for portaudio), ... installed.

then, after checkout, go the virtualenv way:

python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt

run with
python -m papaguy-tamer

let's see whether that works.
enjoy, QM
