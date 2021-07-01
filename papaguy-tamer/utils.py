from .PythonAudioEnvelope import gen_envelope
from contextlib import redirect_stdout
from simpleaudio import WaveObject
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
    wave_obj = WaveObject.from_wave_file(wavefile)
    wave_obj.play()
    wave_obj.wait_done()

