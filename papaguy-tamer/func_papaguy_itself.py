from math import e
from collections import deque
from serial import Serial
from time import sleep, time
from struct import pack
from threading import Timer, Thread
from continuous_threading import ContinuousThread
import serial.tools.list_ports

from . import GENERAL_MESSAGE, TIME_RESOLUTION_IN_SEC, MESSAGE_MAP, \
    MESSAGE_NORM, COMMUNICATION_DISABLED, VERBOSE

from .utils import play_sound, read_string_from
from .logic import Logic


SERIAL_BAUD = 115200

WAITING_FOR_RESPONSE_ATTEMPTS = 20


class PapaGuyItself:

    logic = None
    log = deque([], 100)
    port = None
    connection = None

    def __init__(self, logic: Logic):
        self.logic = logic
        self.clear_connection()
        print("PapaGuyItself constructed with logic", logic.name())
        self.logic.init()

    def clear_connection(self):
        self.port = None
        self.connection = None
        self.logic.clear()

    def reset_log(self, single_message=""):
        self.log.clear()
        if single_message != "":
            self.log.append(single_message)

    @staticmethod
    def get_port_list():
        return [port.device for port in serial.tools.list_ports.comports()]

    def connect(self, port) -> bool:
        self.port = port
        print("ATTEMPT CONNECTION AT", self.port)
        # TODO: could try / except serial.SerialException here
        self.connection = Serial(port, baudrate=SERIAL_BAUD)
        self.logic.on_connection()

        attempt = 0
        alive_signal = ""
        while attempt < WAITING_FOR_RESPONSE_ATTEMPTS and self.connection is not None:
            self.send_message(GENERAL_MESSAGE.ARE_YOU_ALIVE)
            alive_signal = read_string_from(self.connection)
            print("Waiting for response...", attempt, " / ", WAITING_FOR_RESPONSE_ATTEMPTS)
            if len(alive_signal) > 0:
                break
            sleep(0.3)
            attempt += 1

        if len(alive_signal) == 0 or self.connection is None:
            self.reset_log("Timeout. No Response")
            self.disconnect()
            return False

        self.reset_log(alive_signal)
        print("PapaGuy appears to be alive.")
        ContinuousThread(target=self.run_loop).start()
        return True

    def disconnect(self) -> bool:
        if self.connection is None:
            if VERBOSE:
                print("Couldn't disconnect, cause nothing is connected :|")
            return False
        self.connection.close()
        self.clear_connection()
        print("Disconnected.")
        return True

    def try_autoconnect(self):
        self.disconnect()
        try:
            ports = self.get_port_list()
            port = next((port for port in ports if 'COM' in port or 'USB' in port or 'ACM' in port))
            return self.connect(port)
        except:
            return False

    def run_loop(self):
        while self.connection is not None:
            self.logic.on_idle_step()

            sleep(0.1)
            try:
                data = read_string_from(self.connection)
                assert len(data) > 0
            except:
                continue

            self.interpret_message(data)
            self.log.append(data)

        if VERBOSE:
            print("papaguy.communicate() stopped, because connection went down")

        self.try_autoconnect()

    def interpret_message(self, message):
        try:
            action, payload = message.split('!')
        except ValueError:
            return
        self.logic.on_message(action, payload)

    def send_message(self, action, payload=0) -> bool:
        message = bytearray(pack("B", action) + pack(">H", payload))
        if VERBOSE:
            print("SEND MESSAGE", action, payload, " @ ", time())
        if self.connection is None:
            print(f"Connection is not open (anymore?)")
            return False
        if COMMUNICATION_DISABLED:
            print("Communication is disabled, make sure to check COMMUNICATION_DISABLED in __init__.py. It's only a JOKE ;)")
            return False
        self.connection.write(message)
        return True

    def print_all_moves(self):
        print("MOVES:", len(self.logic.get_moves()))
        for move in self.logic.get_moves():
            print(move['id'], move['type'])

    def execute_move(self, move, do_play_sound=True) -> bool:
        if self.logic.is_busy():
            return False

        if 'sample' in move and do_play_sound:
            Thread(target=play_sound, args=(move['sample'],), daemon=True).start()

        self.logic.execute_move(move)
        return True

    def toggle_random_moves(self, value=None):
        self.logic.toggle_random_moves(value)
