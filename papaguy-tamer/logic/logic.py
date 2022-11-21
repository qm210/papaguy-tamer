import string
from typing import Any
from threading import Thread


class Logic:

    def __init__(self):
        self.send_message_func = None
        self.play_sound_func = None
        self.threads: list[Thread] = []

    @classmethod
    def name(cls):
        return cls.__name__

    def set_callbacks(self, message_func, speak_func):
        self.send_message_func = message_func
        self.play_sound_func = speak_func

    def clear(self):
        for thread in self.threads:
            thread.join()

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

    def process_script(self, script: string, **kwargs) -> Any:
        raise NotImplementedError()
