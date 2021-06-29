from flask import Flask, render_template, send_from_directory, redirect, url_for
from time import time, ctime
from threading import Thread
from playsound import playsound
import os

from . import VERSION
from .func_papaguy_itself import papaguy
from .func_move import get_available_moves, execute_move

app = Flask(__name__)

server_start_time = time()

known_moves = []


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
        message=f"Found {len(known_moves)} thingies.",
        list=known_moves
    )


@app.route('/moves/<id>')
def initiate_move(id=None):
    global known_moves
    try:
        existing_move = next((move for move in known_moves if move['id'] == id))
    except:
        return f"Move \"{id}\" not found. Maybe refresh the main 'moves' page."

    if 'sample' in existing_move:
        playsound(existing_move['sample'], block=False)

    if 'env' in existing_move:
        pass

    if 'move' in existing_move:
        thread = Thread(target=execute_move, args=(existing_move['move'],))
        thread.start()

    return f"Executing {existing_move['id']} [{existing_move['type']}]"
    #return redirect(url_for('list_moves'))


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

    papaguy.connect(port)

    thread = Thread(target=papaguy.serial_log)
    thread.start()
    return f"Started on port {papaguy.port}. Have fün."
