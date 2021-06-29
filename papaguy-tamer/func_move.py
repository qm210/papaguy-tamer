# -*- coding: future_fstrings -*-

import os
import json
from threading import Timer

from . import MOVES_DIR, TIME_RESOLUTION_IN_SEC, MESSAGE_TARGET_MAP
from .utils import generate_envelope_as_bero_format


def get_available_moves():
    directory = MOVES_DIR
    result = []
    for file in os.listdir(directory):
        [name, ending] = file.split(".")
        try:
            existing_entry = next((that for that in result if that['id'] == name))
        except StopIteration:
            existing_entry = {'id': name}
            result.append(existing_entry)
        process_move(existing_entry, f"{directory}/{file}", name, ending)

    return result


def process_move(entry, fullpath, name, ending):
    ending = ending.lower()
    entry['broken'] = entry.get('broken', False)

    if ending in ['wav', 'wave']:
        entry['sample'] = fullpath

    elif ending == 'env':
        try:
            with open(fullpath) as fp:
                entry['env'] = json.load(fp)
        except:
            entry['env'] = generate_envelope_as_bero_format(fullpath)

    elif ending in ['manual', 'auto', 'idle', 'move']:
        try:
            with open(fullpath) as fp:
                entry['move'] = json.load(fp)
            entry['trigger'] = ending
        except json.decoder.JSONDecodeError as err:
            entry['broken'] = True
            entry.pop('move', None)
            print("Uh. Broken", err, entry)

    else:
        print("Can't deal with file ending", ending)
        return

    if not entry['broken'] or 'sample' in entry:
        entry['href'] = '/moves/' + name

    entry['type'] = 'move & sample' if 'sample' in entry and 'move' in entry \
        else 'move only' if 'move' in entry \
        else 'sample only' if 'sample' in entry \
        else '??'


def execute_move(move):
    global papaguy
    print("\nexecute that move, keep track", move)
    for target in move['tracks']:
        try:
            target_name = MESSAGE_TARGET_MAP[target['name']]
        except KeyError:
            print("!! Target name is not given in MESSAGE_NAME_MAP!! papaguy won't understand it!", target['name'], MESSAGE_TARGET_MAP)
            return

        print("TARGET NAME:", target['name'], target_name)
        for point in target['automationtimepoints']:
            time_sec = point['time'] * TIME_RESOLUTION_IN_SEC
            value = point['value']
            print(time_sec, value)
            Timer(time_sec, papaguy.serial_send, args=(target_name, value))
    print('\n')


