import wave
import struct
import sys

# generates an envelope for a wav file. only 44.1Khz and 16bit signed supported because lazy.
# fname = file name
# smoothing = release/fall coefficient. 0.9999 should work fine. experiment for best results. values < 0.999 probably do not make sense.
# normalize = if true, normalizes the envelope to peak at 1
# returns a float array with the envelope in fixed one-per-10ms values.
def gen_envelope(fname, time_step_in_secs = 0.05, smoothing = 0.9999, normalize = True):
    wf = wave.open(fname, 'rb')
    chunk = 1024

    print("Sample bytes: " + str(wf.getsampwidth()))
    print("Channels: " + str(wf.getnchannels()))
    print("Rate: " + str(wf.getframerate()))

    env = []

    if (wf.getsampwidth() != 2):
        print("Only 16 bit signed integer wav is supported.")
        return env

    if (wf.getframerate() != 44100):
        print("Only 44KHz is supported")
        return env

    if (wf.getnchannels() > 2):
        print ("Only mono or stereo samples are supported.")
        return env

    data = wf.readframes(chunk)

    channels = wf.getnchannels()

    count = 0
    curenv = 0
    curmax = 0

    def add_to_env(sample):
        nonlocal count
        nonlocal curenv
        nonlocal smoothing
        nonlocal curmax
        curenv = max(abs(sample), curenv * smoothing)
        count = count + 1

        if (count >= 44100 * time_step_in_secs): # snapshots equidistant in given steps, default 50ms
            count = 0
            env.append(curenv)
            curmax = max(curmax, curenv)


    while len(data) > 0:

        curs = 0.0

        if (channels == 1):
            for s in struct.iter_unpack("<h", data):
                curs = s[0] / 32768.0
                add_to_env(curs)
        elif (channels == 2):
            for s in struct.iter_unpack("<hh", data):
                curs = (s[0] + s[1]) / 65536.0
                add_to_env(curs)


        data = wf.readframes(chunk)

    if (normalize and curmax > 0.0000001):
        nfac = 1.0 / curmax
        env = [x * nfac for x in env]

    return env


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("call as:\n", sys.argv[0], "<wav file>")
        quit()
    filename = sys.argv[1]
    env = gen_envelope(filename)
    print("\nENVELOPE:")
    print(env)
