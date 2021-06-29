VERSION = "0.1"
PACKAGE_NAME = "papaguy-tamer"
PRODUCTION = False

BASE_DIR = "./papaguy-tamer"
MOVES_DIR = BASE_DIR + "/moves"

TIME_RESOLUTION_IN_SEC = 0.05

# track.name from BeRos array will be mapped to a short integer ("target") for the papaguy-itself
MESSAGE_TARGET_MAP = {
    'head': 1,
    'wing_left': 2,
    'wing_right': 3,
    'ENVELOPE': 17,
}
# all these targets will receive the position [0..1023] from the generated wav envelope
# could probably use some offset / scaling. TODO
