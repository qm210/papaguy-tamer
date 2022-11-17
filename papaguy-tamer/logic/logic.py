import string
from collections import deque
from typing import Any


class Moves:
    current = None
    all = []
    on_idle = []
    remember_last_ids = deque([], 10)
    next_idle_seconds = 0
    last_move_executed_at = 0
    next_idle_timer = None


class Logic:

    @classmethod
    def name(cls):
        return cls.__name__

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

    def toggle_random_moves(self, value):
        pass

    def execute_move(self, move) -> bool:
        pass

    def get_moves(self):
        pass


