import logging
import string
from rocket import Rocket
from rocket.controllers import TimeController
from time import sleep
from threading import Thread

from . import Logic


class RocketLogic(Logic):

    track_names = ["head_tilt", "head_rotate", "wings", "beak", "body_tilt", "eyes"]
    track_resolution = 20  # 1 sec / 20 = 50ms resolution like the legacy logic

    def __init__(self):
        super().__init__()
        self.controller = TimeController(self.track_resolution)

    def clear(self):
        print("CLEAR")
        super().clear()

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

    def rocket_loop(self, rocket, steps):
        tracks = [rocket.track(track_name) for track_name in self.track_names]
        tracks_pair = zip(tracks, self.track_names)
        print(f"tracks registered: {self.track_names}, now start the rocket ({steps} steps, don't know how to break otherwise)")
        rocket.start()
        try:
            while steps >= 0:  # how else to terminate?
                if steps % 50 == 0:
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

    def start_rocket_thread(self, rocket, steps):
        thread = Thread(target=self.rocket_loop, args=(rocket, steps))
        thread.start()
        self.threads.append(thread)

    def process_script(self, xml_file: string, steps: int = 200):
        rocket = Rocket.from_project_file(self.controller, xml_file, log_level=logging.DEBUG)
        self.start_rocket_thread(rocket, steps)

    @staticmethod
    def connect_socket(logic, host, port, timeout_sec=-1):
        try:
            rocket = Rocket.from_socket(logic.controller, track_path="./rocket", host=host, port=int(port))
            timeout_steps = timeout_sec * logic.track_resolution
            logic.start_rocket_thread(rocket, timeout_steps)
            print(f"started rocket from socket, timeout steps: {timeout_steps} (negative = forever)")
            return True
        except Exception as ex:
            print("exception in connect_socket", repr(ex))
        return False
