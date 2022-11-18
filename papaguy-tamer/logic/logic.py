import string
from typing import Any


class Logic:

    @classmethod
    def name(cls):
        return cls.__name__

    def set_callbacks(self, message_func, speak_func):
        pass

    def clear(self):
        pass

    def on_init(self):
        pass

    def on_connection(self):
        pass

    def on_idle_step(self):
        pass

    def on_message(self, action: string, payload: Any):
        pass

    def is_busy(self) -> bool:
        pass

    def is_doing_random_moves(self):
        pass

    def toggle_random_moves(self, value):
        pass

    def load_moves_from_file(self):
        pass

    def execute_move(self, move, do_play_sound) -> bool:
        pass

    def get_moves(self):
        pass


