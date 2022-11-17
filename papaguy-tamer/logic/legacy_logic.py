from collections import deque
from threading import Thread, Timer
from random import choice, uniform, random
from time import sleep, time

from . import Logic, Moves
from .. import MESSAGE_MAP, TIME_RESOLUTION_IN_SEC
from ..func_moves import get_available_moves


MOVEMENT_OFFSET_IN_SECONDS = 0.03


class LegacyLogic(Logic):

    current_timers = []

    def __init__(self, *args, **kwargs):
        self.moves = Moves()
        self.do_random_moves = kwargs.get('do_random_moves', False)
        self.chance_of_talking = kwargs.get('chance_of_talking', 0.5)
        self.idle_seconds_min = kwargs.get('idle_seconds_min', 5)
        self.idle_seconds_max = kwargs.get('idle_seconds_max', 20)
        self.next_idle_seconds = self.idle_seconds_min

    def clear(self):
        self.clear_current_move()

    def clear_current_move(self):
        self.moves.current = None
        for timer in self.current_timers:
            timer.cancel()
        self.current_timers = []
        print("CLEAR TO EXECUTE NEXT MOVE.")

    def on_connection(self):
        Thread(target=self.load_moves).start()  # we gönn ourselves some moves

    def on_init(self):
        self.choose_next_idle_seconds()

    def on_idle_step(self):
        if self.do_random_moves:
            self.maybe_move_out_of_boredom()

    def get_moves(self):
        return self.moves.on_idle # there are no others (like radar or whatever)

    def load_moves(self):
        self.moves.all = get_available_moves()
        self.moves.on_radar = [move for move in self.moves.all if move['id'][0].isdigit()]
        self.moves.on_idle = self.moves.all
        print("LOADED MOVES.", len(self.moves.on_idle))
        return self.moves.all

    def on_message(self, action, payload):
        # used to listen on action == "RADAR", but that didn't work and so there is no action left
        pass

    def maybe_move_out_of_boredom(self):
        if self.moves.next_idle_timer is None:
            print("TIMER WAS NONE. DO SOMETHING")
            self.choose_next_idle_seconds()
            self.moves.next_idle_timer = Timer(self.next_idle_seconds, self.execute_idle_move)
            self.moves.next_idle_timer.start()
            print("TIMER STARTED FOR IN SECONDS", self.next_idle_seconds)

    def execute_idle_move(self):
        self.choose_next_idle_seconds()
        play_sound = random() < self.chance_of_talking
        print("WE MOVE OUT OF BOREDOM AND WAIT", self.next_idle_seconds, "AND DO WE SPEAK?", play_sound)
        try:
            self.execute_some_move_from(self.moves.on_idle, play_sound)
        except Exception as e:
            print("error", e)

        self.moves.next_idle_timer = None

    def choose_next_idle_seconds(self):
        self.next_idle_seconds = uniform(self.idle_seconds_min, self.idle_seconds_max)

    def is_busy(self):
        return self.moves.current is not None

    def toggle_random_moves(self, value=None):
        self.do_random_moves = not self.do_random_moves if value is None else value
        print("RANDOM MOVES ARE NOW ON?", self.do_random_moves)

    def execute_some_move_from(self, list, play_sound = True):
        try:
            chosen_from_nonrecent = choice([move for move in list if move['id'] not in self.moves.remember_last_ids])
        except IndexError:
            print("LIST EMPTY; CANNOT CHOOSE.", list)
            return
        except:
            print("some exception, ignore this")
            return

        self.execute_move(chosen_from_nonrecent, play_sound)

    def execute_move(self, move):
        self.moves.current = move

        target_list = []
        if 'move' in move and 'tracks' in move['move']:
            target_list = move['move']['tracks']
        if 'env' in move:
            target_list.append(move['env'])

        # jco hack
        if len(target_list) == 1 and 'env' in move and target_list[0]['name'] == 'ENVELOPE':
            new_tilt_target = {'name': 'body_tilt', 'automationtimepoints': []}
            new_head_tilt_target = {'name': 'head_tilt', 'automationtimepoints': []}
            new_head_rot_target = {'name': 'head_rotate', 'automationtimepoints': []}
            tilted_head = False
            for point in target_list[0]['automationtimepoints']:
                new_tilt_target['automationtimepoints'].append(
                    {'time': point['time'] + 10, 'value': point['value'] * 0.5})
                if point['value'] > 0.5 and not tilted_head and point['time'] >= 20:
                    new_head_tilt_target['automationtimepoints'].append(
                        {'time': point['time'], 'value': choice([0.0, 1.0])})
                    tilted_head = True
                if uniform(0.0, 1.0) > 0.8 and point['value'] > 0.5:
                    new_head_rot_target['automationtimepoints'].append(
                        {'time': point['time'], 'value': uniform(0.3, 0.7)})

            new_head_tilt_target['automationtimepoints'].append(
                {'time': target_list[0]['automationtimepoints'][-1]['time'], 'value': 0.5})

            target_list.append(new_tilt_target)
            target_list.append(new_head_tilt_target)
            target_list.append(new_head_rot_target)
        # end jco hack

        self.moves.remember_last_ids.append(move['id'])
        self.moves.last_move_executed_at = time()

        # here: loop over all servo positions

        max_length_sec = 0
        for target in target_list:
            try:
                target_name = MESSAGE_MAP[target['name']]
            except:  # KeyError ?
                print("!! Target name is not given in MESSAGE_MAP (__init__.py)! papaguy won't understand it!",
                      target['name'], MESSAGE_MAP)
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