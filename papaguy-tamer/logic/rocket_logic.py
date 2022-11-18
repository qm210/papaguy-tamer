import string
from rocket import Rocket
from rocket.controllers import TimeController
from time import sleep

from . import Logic


class RocketLogic(Logic):
    def __init__(self):
        self.send_message_func = None
        self.play_sound_func = None

    def set_callbacks(self, message_func, speak_func):
        self.send_message_func = message_func
        self.play_sound_func = speak_func
        print("SET_CALLBACKS")

    def clear(self):
        print("CLEAR")

    def on_init(self):
        print("ON_INIT")

    def on_connection(self):
        print("ON_CONNECTION")

    def on_idle_step(self):
        print("ON_IDLE_STEP")

    def on_message(self, action=None, payload=None):
        print("ON_MESSAGE", action, payload)

    def is_busy(self) -> bool:
        print("IS_BUSY")
        return False

    def is_doing_random_moves(self):
        return True

    def toggle_random_moves(self, value):
        print("TOGGLE_RANDOM_MOVES")

    def load_moves_from_file(self):
        print("LOAD_MOVES_FROM_FILE")

    def execute_move(self, move, do_play_sound=True) -> bool:
        print("EXECUTE_MOVE", move, do_play_sound)

    def get_moves(self):
        print("GET_MOVES")
        return []

    track_names = ["head_tilt", "head_rotate", "wings", "beak", "body_tilt", "eyes"]
    track_resolution = 20  # 1 sec / 20 = 50ms resolution like the legacy logic

    def process_script(self, xml_file: string):
        controller = TimeController(self.track_resolution)
        rocket = Rocket.from_project_file(controller, xml_file)
        tracks = [rocket.track(track_name) for track_name in self.track_names]
        tracks_pair = zip(tracks, self.track_names)
        steps = 200  # how else to terminate?
        print(f"tracks registered: {self.track_names}, now start the rocket ({steps} steps, don't know how to break otherwise)")
        rocket.start()
        try:
            while steps > 0:
                print(f"{steps} steps until break, rocket time {rocket.time}")
                rocket.update()
                for track, target in tracks_pair:
                    self.send_message_func(target, int(rocket.value(target)))
                steps -= 1
                sleep(1.0 / self.track_resolution)  # don't get it - why the sleep if we set the rate in TimeController?
        except KeyboardInterrupt:
            print("rocket forcefully landed.")
            return
        print("rocket landed.")
