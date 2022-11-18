from . import Logic


class RocketLogic(Logic):
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

