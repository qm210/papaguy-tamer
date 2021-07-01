from glob import glob
import os
import json

from . import MOVES_DIR
from .utils import generate_envelope_as_bero_format


def batch_jobs(force = False):
    batch_precalc_wav_envelopes(force)


def batch_precalc_wav_envelopes(force = False):
    TARGET_ENDING = '.env'
    for wavfile in glob(f"{MOVES_DIR}/*.wav"):
        envfile = wavfile.replace('.wav', TARGET_ENDING)
        if not force and os.path.exists(envfile):
            continue
        precalc_wav_envelope(wavfile, envfile)

def precalc_wav_envelope(wavfile, envfile):
    bero_format = generate_envelope_as_bero_format(wavfile)
    with open(envfile, 'w') as fp:
        json.dump(bero_format, fp)
    print("written:", envfile)


if __name__ == '__main__':
    batch_jobs()
