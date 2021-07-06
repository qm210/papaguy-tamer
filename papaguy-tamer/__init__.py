VERSION = "0.999"
PACKAGE_NAME = "papaguy-tamer"
PRODUCTION = True

BASE_DIR = "./papaguy-tamer"
MOVES_DIR = BASE_DIR + "/moves"

TIME_RESOLUTION_IN_SEC = 0.05

# track.name from BeRos array will be mapped to a short integer ("target") for the papaguy-itself
MESSAGE_MAP = {
    'body_tilt': 1,
    'wings': 2,
    'head_tilt': 3,
    'head_rotate': 4,
    'beak': 5,

    'ENVELOPE': 17,

    'eyes': 20,
    'fog': 23,
}

class GENERAL_MESSAGE:
    ROTATE_HEAD = 4 # this is different from the other servos, because direction-dependent (reacts to radars)
    EMULATE_RADAR = 101
    ARE_YOU_ALIVE = 63
    DEACTIVATE = 125
    REACTIVATE = 126
    RESET = 127

# all these targets will receive the position [0..1023] from the generated wav envelope
# could probably use some offset / scaling. TODO

# the associated directions (in servo units from 0 .. 180 degrees) of the radars for the head
RADAR_DIRECTION = [
    20,
    55,
    90,
    125,
    160
]

MESSAGE_NORM = 1023