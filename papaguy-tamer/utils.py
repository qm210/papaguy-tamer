import string

from .PythonAudioEnvelope import gen_envelope
from contextlib import redirect_stdout
from simpleaudio import WaveObject
from serial import Serial
from os import devnull

from . import TIME_RESOLUTION_IN_SEC


def generate_envelope_as_bero_format(wavfile):
    with open(devnull, 'w') as dev_null:
        with redirect_stdout(dev_null):
            result = gen_envelope(wavfile, TIME_RESOLUTION_IN_SEC)
    return {
        'name': 'ENVELOPE',
        'automationtimepoints': [
            {'time': step, 'value': env} for (step, env) in enumerate(result)
        ]
    }

def play_sound(wavefile):
    playing_object = WaveObject.from_wave_file(wavefile).play()
    playing_object.wait_done()


def read_string_from(connection: Serial) -> string:
    if connection is None:
        return ""
    line = connection.readline()
    try:
        return line.decode('utf-8').strip()
    except UnicodeDecodeError:
        print("UnicodeDecodeError in line", line)
        return line.strip()