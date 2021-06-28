from flask import Flask, render_template, send_from_directory, redirect, url_for
from time import time, ctime, sleep
from serial import Serial
from dataclasses import dataclass, field
from threading import Thread
from playsound import playsound
import json
import os

from . import VERSION

app = Flask(__name__)

BASE_DIR = "./papaguy-tamer"
MOVES_DIR = BASE_DIR + "/moves"

start_time = time()

@dataclass
class PapaGuyItself:
    log: list[str] = field(default_factory=list)
    port: str = None
    connection = None

papaguy = PapaGuyItself()

@app.route('/')
def index():
    return render_template(
        'home.html',
        title=f"papaguy-tamer v{VERSION} is running since {ctime(start_time)}, thanks for checking by.",
        message=f"qm is wondering: Who the fuck implemented that time string formatting??",
    )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/moves')
def list_moves():
    available_moves = get_available_moves()
    return render_template(
        'moves.html',
        title="Moves",
        message=f"{len(available_moves)} moves found.",
        list=available_moves
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
        process_move_entry(existing_entry, file, name, ending)

    print(result)
    return result

def process_move_entry(entry, filename, name, ending):
    ending = ending.lower()

    if ending in ['wav', 'wave']:
        entry['sample'] = filename
    elif ending == 'move':
        try:
            with open(f"{MOVES_DIR}/{filename}") as fp:
                entry['move'] = json.load(fp)
        except:
            entry['broken'] = True
    else:
        return

    if not entry.get('broken', False):
        entry['href'] = '/moves/' + name


@app.route('/moves/<id>')
def do_move(id=None):
#    {"tracks": [ {"name":"bla", "automationtimepoints": [ {"time":123,  "value":0.5 }, ... ] }, ... ] }
    try:
        existing_move = next((move for move in get_available_moves() if move['id'] == id))
    except:
        return f"Move \"{id}\" not found"

    if 'sample' in existing_move:
        playsound(MOVES_DIR + '/' + existing_move['sample'], block=False)
        return f"Playing {existing_move['sample']}"

    return redirect(url_for('list_moves'))


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

    def serial_log():
        while True:
            sleep(1)
            data = papaguy.connection.readline()
            papaguy.log.append(data)
            print("DATA:", data)

    thread = Thread(target=serial_log)
    thread.start()
    return f"Started on port {papaguy.port}. Have fün."