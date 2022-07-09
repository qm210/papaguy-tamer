from math import e
from serial import Serial
from time import sleep, time
from struct import pack
from threading import Timer, Thread
from continuous_threading import ContinuousThread
from collections import deque
from random import choice, uniform, random
import serial.tools.list_ports

from . import GENERAL_MESSAGE, TIME_RESOLUTION_IN_SEC, MESSAGE_MAP, \
    RADAR_DIRECTION, MESSAGE_NORM, COMMUNICATION_DISABLED, VERBOSE, \
    SECONDS_TO_IDLE_AT_LEAST, SECONDS_TO_IDLE_AT_MOST, \
    CHANCE_OF_TALKING, RANDOM_MOVES_ON_DEFAULT

from .func_moves import get_available_moves
from .utils import play_sound

SERIAL_BAUD = 115200

WAITING_FOR_RESPONSE_ATTEMPTS = 20

MOVEMENT_OFFSET_IN_SECONDS = 0.03

class PapaGuyItself:

    log = deque([], 100)
    port = None
    connection = None
    current_timers = []
    do_random_moves = RANDOM_MOVES_ON_DEFAULT

    class Moves:
        current = None
        all = []
        on_radar = []
        on_idle = []
        remember_last_ids = deque([], 10)
        next_idle_seconds = 0
        last_move_executed_at = 0
        next_idle_timer = None


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


    def reset_log(self, single_message = ""):
        self.log.clear()
        if single_message != "":
            self.log.append(single_message)


    def get_portlist(self):
        return [port.device for port in serial.tools.list_ports.comports()]


    def connect(self, port) -> bool:
        self.port = port
        print("ATTEMPT CONNECTION AT", self.port)
        self.connection = Serial(port, baudrate=SERIAL_BAUD)

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
            self.reset_log("Timeout. No Response")
            self.disconnect()
            return False

        self.reset_log(alive_signal)
        print("PapaGuy appears to be alive.")

        ContinuousThread(target=self.communicate).start()

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
            ports = self.get_portlist()
            port = next((port for port in ports if 'COM' in port or 'USB' in port))
            return self.connect(port)
        except:
            return False


    def communicate(self):
        while self.connection is not None:
            if self.do_random_moves:
                self.maybe_move_out_of_boredom()

            sleep(0.2)
            try:
                data = self.read_string()
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

        if action == "RADAR":
            print("PARSE", action, payload)
            radar_metrics = [int(part) for part in payload.split(';') if part != '']
            if len(RADAR_DIRECTION) != len(radar_metrics):
                raise ValueError("Dimension of radar metrics have to match RADAR_DIRECTION!")
            direction = PapaGuyItself.interpolate_radar_direction(radar_metrics)
            self.handle_radar_detection(direction)


    @staticmethod
    def interpolate_radar_direction(metrics):
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
        if self.moves.next_idle_timer is None:
            print("TIMER WAS NONE. DO SOMETHING")
            if self.next_idle_seconds < SECONDS_TO_IDLE_AT_LEAST:
                self.choose_next_idle_seconds()
            self.moves.next_idle_timer = Timer(self.next_idle_seconds, self.execute_idle_move)
            self.moves.next_idle_timer.start()
            print("TIMER STARTED FOR IN SECONDS", self.next_idle_seconds)


    def execute_idle_move(self):
        self.choose_next_idle_seconds()
        play_sound = random() < CHANCE_OF_TALKING
        print("WE MOVE OUT OF BOREDOM AND WAIT", self.next_idle_seconds, "AND DO WE SPEAK?", play_sound)
        try:
            self.execute_some_move_from(self.moves.on_idle, play_sound)
        except Exception as e:
            print("error", e)

        self.moves.next_idle_timer = None


    def choose_next_idle_seconds(self):
        self.next_idle_seconds = uniform(SECONDS_TO_IDLE_AT_LEAST, SECONDS_TO_IDLE_AT_MOST)


    def send_message(self, action, payload = 0) -> bool:
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


    def load_moves_from_disk(self):

        self.moves.all = get_available_moves()
        self.moves.on_radar = [move for move in self.moves.all if move['id'][0].isdigit()]
        self.moves.on_idle = self.moves.all # we actually don't have no radar #[move for move in self.moves.all if move not in self.moves.on_radar]
        print("LOADED MOVES.", len(self.moves.on_radar), " ON RADAR, ", len(self.moves.on_idle), "ON IDLE")
        return self.moves.all


    def print_all_moves(self):
        print("ON_RADAR:", len(self.moves.on_radar))
        for move in self.moves.on_radar:
            print(move['id'], move['type'])
        print("ON_IDLE:", len(self.moves.on_idle))
        for move in self.moves.on_radar:
            print(move['id'], move['type'])


    def execute_move(self, move, do_play_sound = True) -> bool:
        if self.moves.current is not None:
            return False

        self.moves.current = move

        if 'sample' in move and do_play_sound:
            Thread(target=play_sound, args=(move['sample'],), daemon=True).start()

        target_list = []
        if 'move' in move and 'tracks' in move['move']:
            target_list = move['move']['tracks']
        if 'env' in move:
            target_list.append(move['env'])


         # jco hack
        if len(target_list) == 1 and 'env' in move and target_list[0]['name'] == 'ENVELOPE':
            new_tilt_target = { 'name':'body_tilt', 'automationtimepoints':[] }
            new_head_tilt_target = { 'name':'head_tilt', 'automationtimepoints':[] }
            new_head_rot_target = { 'name':'head_rotate', 'automationtimepoints':[] }
            tilted_head = False
            for point in target_list[0]['automationtimepoints']:
                new_tilt_target['automationtimepoints'].append( { 'time':point['time'] + 10, 'value':point['value'] * 0.5 } )
                if point['value'] > 0.5 and not tilted_head and point['time'] >= 20:
                    new_head_tilt_target['automationtimepoints'].append( { 'time':point['time'], 'value':choice([0.0, 1.0]) } )
                    tilted_head = True
                if uniform(0.0, 1.0) > 0.8 and point['value'] > 0.5:
                    new_head_rot_target['automationtimepoints'].append( { 'time':point['time'], 'value':uniform(0.3, 0.7) } )

            new_head_tilt_target['automationtimepoints'].append( {'time':target_list[0]['automationtimepoints'][-1]['time'], 'value':0.5 } )

            target_list.append(new_tilt_target)
            target_list.append(new_head_tilt_target)
            target_list.append(new_head_rot_target)
        # end jco hack

        self.moves.remember_last_ids.append(move['id'])
        self.moves.last_move_executed_at = time()

        max_length_sec = 0
        for target in target_list:
            try:
                target_name = MESSAGE_MAP[target['name']]
            except: # KeyError ?
                print("!! Target name is not given in MESSAGE_MAP (__init__.py)! papaguy won't understand it!", target['name'], MESSAGE_MAP)
                continue

            # some fixes to support BeRo's actual format
            automationtimepoints = target.get('automationtimepoints', target.get('automation', []))

            for index, point in enumerate(automationtimepoints):
                if type(point) is dict:
                    raw = point
                else:
                    raw = {'time': index, 'value': point}

                time_sec = raw['time'] * TIME_RESOLUTION_IN_SEC + MOVEMENT_OFFSET_IN_SECONDS
                value = int(raw['value'] * MESSAGE_NORM)

                timer = Timer(time_sec, self.send_message, args=(target_name, value))
                timer.start()
                self.current_timers.append(timer)
                max_length_sec = max(max_length_sec, time_sec)

        max_length_sec += TIME_RESOLUTION_IN_SEC
        # at the very end, reset the state so a new move can be started
        if 'env' in move:
            reset_timer = Timer(max_length_sec, self.send_message, args=(MESSAGE_MAP['ENVELOPE'], 0))
            reset_timer.start()
            self.current_timers.append(reset_timer)

        for safety_wing_reset in range(10):
            max_length_sec += TIME_RESOLUTION_IN_SEC
            reset_wings_timer = Timer(max_length_sec, self.send_message, args=(MESSAGE_MAP['wings'], 0))
            reset_wings_timer.start()
            self.current_timers.append(reset_wings_timer)

        max_length_sec += TIME_RESOLUTION_IN_SEC
        Timer(max_length_sec, self.clear_current_move).start()
        return True


    def execute_some_move_from(self, list, play_sound = True):
        try:
            chosen_from_nonrecent = choice([move for move in list if move['id'] not in self.moves.remember_last_ids])
        except IndexError:
            print("LIST EMPTY; CANNOT CHOOSE.", list)
            return
        except:
            print("some exception, don't care, move on")

        self.execute_move(chosen_from_nonrecent, play_sound)


    def toggle_random_moves(self, value = None):
        self.do_random_moves = not self.do_random_moves if value is None else value


papaguy = PapaGuyItself()
