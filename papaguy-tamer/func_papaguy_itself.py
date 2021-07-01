from serial import Serial
from time import sleep, time
from struct import pack
from threading import Timer, Thread
from collections import deque
from random import choice, uniform
import serial.tools.list_ports

from . import GENERAL_MESSAGE, TIME_RESOLUTION_IN_SEC, MESSAGE_MAP, RADAR_DIRECTION, MESSAGE_NORM
from .func_moves import get_available_moves
from .utils import play_sound

SERIAL_BAUD = 115200

WAITING_FOR_RESPONSE_ATTEMPTS = 20

SECONDS_TO_IDLE_AT_LEAST = 3
SECONDS_TO_IDLE_AT_MOST = 10


class PapaGuyItself:

    log = deque([], 100)
    port = None
    connection = None
    current_timers = []

    class Moves:
        current = None
        all = []
        on_radar = []
        on_idle = []
        remember_last_ids = deque([], 10)
        next_idle_seconds = 0
        last_time_when_idle_triggered = 0


    def __init__(self):
        self.moves = self.Moves()
        self.clear_connection()
        self.choose_next_idle_seconds()
        print("PapaGuyItself constructed.")


    def clear_connection(self):
        self.port = None
        self.connection = None
        self.clear_current_move()


    def clear_current_move(self):
        self.moves.current = None
        for timer in self.current_timers:
            timer.cancel()
        self.current_timers = []
        print("CLEAR TO EXECUTE NEXT MOVE.")


    def get_portlist(self):
        return [port.device for port in serial.tools.list_ports.comports()]


    def connect(self, port) -> bool:
        self.port = port
        print("ATTEMPT CONNECTION AT", self.port)
        self.connection = Serial(port, baudrate=SERIAL_BAUD, timeout=.1)

        Thread(target=self.load_moves_from_disk).start() # we gönn ourselves some moves

        attempt = 0
        while attempt < WAITING_FOR_RESPONSE_ATTEMPTS and self.connection is not None:
            self.send_message(GENERAL_MESSAGE.ARE_YOU_ALIVE)
            alive_signal = self.read_string()
            print("Waiting for response...", attempt, " / ", WAITING_FOR_RESPONSE_ATTEMPTS)
            if len(alive_signal) > 0:
                break
            sleep(0.5)
            attempt += 1

        if len(alive_signal) == 0 or self.connection is None:
            self.log.clear()
            self.log.append("Timeout. No Response")
            self.disconnect()
            return False

        self.log.clear()
        self.log.append(alive_signal)
        print("PapaGuy appears to be alive.")

        return True


    def read_string(self) -> str:
        if self.connection is None:
            return ""
        line = self.connection.readline()
        try:
            return line.decode('utf-8').strip()
        except UnicodeDecodeError:
            print("UnicodeDecodeError in line", line)
            return line.strip()


    def disconnect(self) -> bool:
        if self.connection is None:
            print("Couldn't disconnect, cause nothing is connected :|")
            return False
        self.connection.close()
        self.clear_connection()
        print("Disconnected.")
        return True


    def communicate(self):
        while self.connection is not None:
            self.maybe_move_out_of_boredom()

            sleep(0.5)
            data = self.read_string()
            if len(data) == 0:
                continue

            self.interpret_message(data)

            self.log.append(data)
            print("DATA:", list(self.log))

        print("papaguy.communicate() stopped, because connection went down")


    def interpret_message(self, message):
        try:
            action, payload = message.split('!')
        except ValueError:
            return

        if action == "RADAR":
            radar_metrics = [int(part) for part in payload.split(';')]
            if len(RADAR_DIRECTION) != len(radar_metrics):
                raise ValueError("Dimension of radar metrics have to match RADAR_DIRECTION!")
            direction = PapaGuyItself.interpolate_strongest_direction(radar_metrics)
            self.handle_radar_detection(direction)


    @staticmethod
    def interpolate_radar_detection(metrics):
        strongest_radar = -1
        second_radar = -1
        for radar, value in enumerate(metrics):
            if value > metrics[strongest_radar]:
                second_radar = strongest_radar
                strongest_radar = radar

        if strongest_radar == -1:
            print("what the fuck, nothing there??", metrics)
            return 90

        if second_radar == -1:
            return RADAR_DIRECTION[strongest_radar]

        norm = float(metrics[strongest_radar] + metrics[second_radar])
        weight = float(metrics[strongest_radar]) / norm
        return weight * RADAR_DIRECTION[strongest_radar] + (1 - weight) * RADAR_DIRECTION[second_radar]


    def handle_radar_detection(self, direction):
        normalized_direction = int(MESSAGE_NORM * max(0, min(180, direction)) / 180)
        self.send_message(GENERAL_MESSAGE.ROTATE_HEAD, normalized_direction)
        self.execute_some_move_from(self.moves.on_radar)


    def maybe_move_out_of_boredom(self):
        if time() - self.moves.last_time_when_idle_triggered > self.next_idle_seconds:
            self.choose_next_idle_seconds()
            print("WE MOVE OUT OF BOREDOM AND WAIT", self.next_idle_seconds)
            self.execute_some_move_from(self.moves.on_idle)
            self.moves.last_time_when_idle_triggered = time()


    def choose_next_idle_seconds(self):
        self.next_idle_seconds = uniform(SECONDS_TO_IDLE_AT_LEAST, SECONDS_TO_IDLE_AT_MOST)


    def send_message(self, action, payload = 0) -> bool:
        message = bytearray(pack("B", action) + pack(">H", payload))
        print("SEND MESSAGE", message)
        if self.connection is None:
            print(f"Öhm. Cannot send when connection is not initialized. Do pls.")
            return False
        self.connection.write(message)
        return True


    def load_moves_from_disk(self):
        self.moves.all = get_available_moves()
        self.moves.on_radar = [move for move in self.moves.all if move['id'][0].isdigit()]
        self.moves.on_idle = [move for move in self.moves.all if move not in self.moves.on_radar]
        print("LOADED MOVES... THAT MANY:", len(self.moves.all), len(self.moves.on_radar), len(self.moves.on_idle))
        return self.moves.all


    def execute_move(self, move) -> bool:
        print("WOULD MOVE BUT", self.moves.current)
        if self.moves.current is not None:
            return False

        print("EXECUTE MOVE:", move['id'])
        self.moves.current = move

        if 'sample' in move:
            Thread(target=play_sound, args=(move['sample'],), daemon=True).start()

        target_list = move.get('tracks', [])
        if 'env' in move:
            target_list.append(move['env'])

        print("COMBINED TARGET_LIST", target_list)

        max_length_sec = 0
        for target in target_list:
            try:
                target_name = MESSAGE_MAP[target['name']]
            except KeyError:
                print("!! Target name is not given in MESSAGE_MAP (__init__.py)! papaguy won't understand it!", target['name'], MESSAGE_MAP)
                continue

            print("TARGET NAME:", target['name'], target_name)
            for point in target['automationtimepoints']:
                time_sec = point['time'] * TIME_RESOLUTION_IN_SEC
                value = int(point['value'] * MESSAGE_NORM)
                timer = Timer(time_sec, self.send_message, args=(target_name, value))
                timer.start()
                self.current_timers.append(timer)
                max_length_sec = max(max_length_sec, time_sec)

        # at the very end, reset the state so a new move can be started
        Timer(max_length_sec + TIME_RESOLUTION_IN_SEC, self.clear_current_move).start()
        self.moves.remember_last_ids.append(move['id'])
        return True


    def execute_some_move_from(self, list):
        try:
            chosen_from_nonrecent = choice([move for move in list if move['id'] not in self.moves.remember_last_ids])
        except IndexError:
            print("LIST EMPTY; CANNOT CHOOSE.", list)
            return
        self.execute_move(chosen_from_nonrecent)


papaguy = PapaGuyItself()
