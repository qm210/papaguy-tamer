from flask import Flask, render_template, send_from_directory, redirect, url_for
from time import time, ctime, sleep
from serial import Serial
from dataclasses import dataclass, field
from threading import Thread, Timer
from playsound import playsound
from enum import Enum
import json
import os

from . import VERSION

app = Flask(__name__)


BASE_DIR = "./papaguy-tamer"
MOVES_DIR = BASE_DIR + "/moves"

TIME_RESOLUTION_IN_MS = 50
server_start_time = time()

@dataclass
class PapaGuyItself:
    log: list[str] = field(default_factory=list)
    port: str = None
    connection = None

papaguy = PapaGuyItself()

known_moves = []

# track.name from BeRos array will be mapped to a short integer ("message name") for the papaguy-itself
MESSAGE_NAME_MAP = {
    'head': 1,
}

@app.route('/')
def index():
    return render_template(
        'home.html',
        title=f"papaguy-tamer v{VERSION} is running since {ctime(server_start_time)}, thanks for checking by.",
        message=f"qm is wondering: Who the fuck implemented that time string formatting??",
    )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/moves')
def list_moves():
    global known_moves
    known_moves = get_available_moves()
    return render_template(
        'moves.html',
        title="Moves",
        message=f"{len(known_moves)} moves known.",
        list=known_moves
    )

def get_available_moves():
    result = []
    for file in os.listdir(MOVES_DIR):
        [name, ending] = file.split(".")
        try:
            existing_entry = next((that for that in result if that['id'] == name))
        except StopIteration:
            existing_entry = {'id': name}
            result.append(existing_entry)
        process_move(existing_entry, file, name, ending)

    return result

def process_move(entry, filename, name, ending):
    ending = ending.lower()

    entry['broken'] = entry.get('broken', False)
    if ending in ['wav', 'wave']:
        entry['sample'] = filename
    elif ending in ['manual', 'auto', 'idle', 'move']:
        try:
            with open(f"{MOVES_DIR}/{filename}") as fp:
                entry['move'] = json.load(fp)
            entry['trigger'] = ending
        except json.decoder.JSONDecodeError as err:
            entry['broken'] = True
            entry.pop('move', None)
            print("Uh. Broken", err, entry)
    else:
        return

    if not entry['broken'] or 'sample' in entry:
        entry['href'] = '/moves/' + name

    entry['type'] = 'move & sample' if 'sample' in entry and 'move' in entry \
        else 'move only' if 'move' in entry \
        else 'sample only' if 'sample' in entry \
        else '??'


@app.route('/moves/<id>')
def initiate_move(id=None):
    try:
        existing_move = next((move for move in get_available_moves() if move['id'] == id))
    except:
        return f"Move \"{id}\" not found"

    if 'sample' in existing_move:
        playsound(MOVES_DIR + '/' + existing_move['sample'], block=False)

    if 'move' in existing_move:
        thread = Thread(target=execute_move, args=(existing_move,))
        thread.start()

    return f"Executing {existing_move['id']} [{existing_move['type']}]"
    #return redirect(url_for('list_moves'))

def execute_move(move):
    print("execute that move, keep track", move)
    start_time = time()


@app.route('/serial/<port>')
def connect_serial(port=None):
    global papaguy
    if papaguy.connection is not None:
        return render_template(
            'list.html',
            title="Running.",
            message=f"this thing is now blocking port {papaguy.port}",
            list=papaguy.log
        )

    papaguy.port = port
    papaguy.connection = Serial(port, baudrate=115200, timeout=.1)

    thread = Thread(target=serial_log)
    thread.start()
    return f"Started on port {papaguy.port}. Have fün."

def serial_log():
    global papaguy
    while True:
        sleep(1)
        data = papaguy.connection.readline()
        papaguy.log.append(data)
        print("DATA:", data)
