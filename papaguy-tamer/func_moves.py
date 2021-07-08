import os
import json

from . import MOVES_DIR
from .utils import generate_envelope_as_bero_format


def get_available_moves():
    directory = MOVES_DIR
    result = []
    for file in os.listdir(directory):
        try:
            [name, ending] = file.split(".")
        except ValueError:
            continue

        try:
            existing_entry = next((that for that in result if that['id'] == name))
        except StopIteration:
            existing_entry = {'id': name}
            result.append(existing_entry)
        process_move(existing_entry, f"{directory}/{file}", name, ending)

    result.sort(key=lambda a: a.get('id'))
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

    elif ending in ['json', 'move']:
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


