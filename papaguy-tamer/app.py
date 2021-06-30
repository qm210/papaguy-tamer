from flask import Flask, render_template, send_from_directory, request, url_for, redirect
from time import time, ctime
from threading import Thread
import os

from . import VERSION
from .func_papaguy_itself import papaguy
from .func_move import get_available_moves, execute_move
from .utils import play_sound

app = Flask(__name__)
server_start_time = time()
known_moves = []


@app.route('/')
def index():
    return render_template(
        'home.html',
        title=f"papaguy-tamer v{VERSION} is running since {ctime(server_start_time)}, thanks for checking by.",
        message=f"qm is wondering: Who the fuck implemented that time string formatting??",
        connected=papaguy.connection is not None
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
        message=f"Found {len(known_moves)} thingies.",
        list=known_moves
    )


@app.route('/moves/<id>')
def initiate_move(id=None):
    global known_moves
    known_moves = get_available_moves() # wir gönnen uns
    try:
        existing_move = next((move for move in known_moves if move['id'] == id))
    except:
        return f"Move \"{id}\" not found. Maybe refresh the main 'moves' page."

    if 'sample' in existing_move:
        # block=False cannot be used on this platform yet
        Thread(target=play_sound, args=(existing_move['sample'],), daemon=True).start()

    if 'env' in existing_move:
        pass

    if 'move' in existing_move:
        thread = Thread(target=execute_move, args=(existing_move['move'],))
        thread.start()

    return f"Executing {existing_move['id']} [{existing_move['type']}]"


@app.route('/connect/<port>')
def connect_serial(port):
    if papaguy.connection is not None:
        return print_serial_log()

    papaguy.connect(port)
    thread = Thread(target=papaguy.serial_log)
    thread.start()
    return redirect(url_for('print_serial_log'))


# convenience (if any)
@app.route('/connect')
def connect_serial_by_query():
    port = request.args.get('port')
    print("QUERY:", request.args, port)
    connect_serial(port)

# linux compatibility
@app.route('/connect/dev/<port>')
def connect_serial_with_dev(port):
    connect_serial(port=f"dev/{port}")


@app.route('/portlist')
def list_serial_ports():
    ports = papaguy.get_portlist()
    links = ['./connect/' + port for port in ports]
    return render_template(
        'list.html',
        title="COM ports",
        message=f"Currently connected to port: {papaguy.port}",
        list=ports,
        href=links
    )


@app.route('/log')
def print_serial_log():
    if papaguy.connection is None:
        return render_template(
            'list.html',
            title="Not connected.",
            message=f"Log last updated at {ctime(time())}",
            footer="<a href=\"" + url_for('list_serial_ports') + "\">Check serial ports</a>",
            refresh=10
        )

    return render_template(
        'list.html',
        title=f"Running on port {papaguy.port}",
        message=f"Log last updated at {ctime(time())}",
        list=papaguy.log,
        refresh=3
    )