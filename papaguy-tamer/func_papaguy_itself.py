import string
from collections import deque
from serial import Serial
from time import sleep, time
from struct import pack
from threading import Thread
from continuous_threading import ContinuousThread
import serial.tools.list_ports

from . import GENERAL_MESSAGE, COMMUNICATION_DISABLED, VERBOSE, IGNORE_ARDUINO, MESSAGE_MAP

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
        self.logic.on_init()
        self.logic.set_callbacks(self.send_message, self.speak)

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

        Thread(target=self.logic.load_moves_from_file).start()  # we gönn ourselves some moves
        self.logic.on_connection()

        attempt = 0
        alive_signal = ""
        while attempt < WAITING_FOR_RESPONSE_ATTEMPTS and not self.connection_exists():
            self.send_message(GENERAL_MESSAGE.ARE_YOU_ALIVE)
            alive_signal = read_string_from(self.connection)
            print("Waiting for response...", attempt, " / ", WAITING_FOR_RESPONSE_ATTEMPTS)
            if len(alive_signal) > 0:
                break
            sleep(0.3)
            attempt += 1

        if len(alive_signal) == 0 or not self.connection_exists():
            self.reset_log("Timeout. No Response")
            self.disconnect()
            return False

        self.reset_log(alive_signal)
        print("PapaGuy appears to be alive.")
        ContinuousThread(target=self.run_loop).start()
        return True

    def connection_exists(self):
        return self.connection is not None or IGNORE_ARDUINO

    def disconnect(self) -> bool:
        if self.connection is None:
            if VERBOSE:
                print("Couldn't disconnect, cause nothing is connected :|")
            return False
        self.connection.close()
        self.clear_connection()
        print("Disconnected.")
        return True

    def update_moves(self):
        self.logic.load_moves_from_file()
        return self.logic.get_moves()

    def try_autoconnect(self):
        self.disconnect()
        try:
            ports = self.get_port_list()
            port = next((port for port in ports if 'COM' in port or 'USB' in port or 'ACM' in port))
            return self.connect(port)
        except StopIteration:
            print("... no port available.")
        except Exception as ex:
            print("exception", repr(ex))
        return False

    def run_loop(self):
        print("RUN_LOOP called.")
        while self.connection_exists():
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
            print("papaguy.run_loop() stopped due to break condition (i.e. connection went down or ...)")

        self.try_autoconnect()

    def interpret_message(self, message):
        try:
            action, payload = message.split('!')
        except ValueError:
            return
        self.logic.on_message(action, payload)

    def send_message(self, target: string, payload: int = 0) -> bool:
        try:
            action = MESSAGE_MAP[target]
        except KeyError:
            try:
                action = int(target)
            except ValueError:
                print(f"!! Target {target} not an integer or defined in MESSAGE_MAP. Cancel.")
                return False

        now = time()
        if IGNORE_ARDUINO or VERBOSE:
            print(f"{'WOULD ' if IGNORE_ARDUINO else ''}SEND: action {action} payload {payload} @ {now}")
        if IGNORE_ARDUINO:
            return True

        message = bytearray(pack("B", action) + pack(">H", payload))
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

        self.logic.execute_move(move, do_play_sound)
        return True

    def toggle_random_moves(self, value=None):
        self.logic.toggle_random_moves(value)

    @staticmethod
    def speak(wave_file):
        Thread(target=play_sound, args=(wave_file,), daemon=True).start()
