from .PythonAudioEnvelope import gen_envelope
from contextlib import redirect_stdout
from os import devnull

from . import TIME_RESOLUTION_IN_SEC

def generate_envelope_as_bero_format(wavfile):
    with open(devnull, 'w') as dev_null:
        with redirect_stdout(dev_null):
            result = gen_envelope(wavfile, TIME_RESOLUTION_IN_SEC)
    return {
        'name': 'ENVELOPE',
        'automationtimepoint': [
            {'time': step, 'value': env} for (step, env) in enumerate(result)
        ]
    }