from flask import Flask, render_template, send_from_directory, request, url_for, redirect
from time import time, ctime
from threading import Thread
import os

from . import VERSION, GENERAL_MESSAGE
from .func_papaguy_itself import papaguy
from .utils import play_sound
from .batch import batch_jobs


app = Flask(__name__)
server_start_time = time()


@app.route('/')
def index():
    return render_template(
        'home.html',
        title=f"papaguy-tamer v{VERSION} is running since {ctime(server_start_time)}",
        message=f"qm says thanks for checking by.",
        connected=papaguy.connection is not None
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/moves')
def list_moves():
    known_moves = papaguy.load_moves_from_disk()
    return render_template(
        'moves.html',
        title="Moves",
        message=f"Found {len(known_moves)} thingies.",
        list=known_moves
    )


@app.route('/moves/<id>')
def initiate_move(id=None):
    known_moves = papaguy.load_moves_from_disk() # wir gönnen uns, statt einfach liste vom cache zu nehmen
    try:
        existing_move = next((move for move in known_moves if move['id'] == id))
    except:
        return f"Move \"{id}\" not found. Maybe refresh the main 'moves' page."

    this_worked = False
    if 'sample' in existing_move:
        Thread(target=play_sound, args=(existing_move['sample'],), daemon=True).start()
        this_worked = True

    if 'env' in existing_move:
        pass

    if 'move' in existing_move:
        this_worked = papaguy.execute_move(existing_move['move'])

    if this_worked:
        return f"Executing {existing_move['id']} [{existing_move['type']}]"
    else:
        return f"Didn't work. Maybe there is still a move ongoing?"


@app.route('/panic')
def cancel_all_moves():
    papaguy.clear_connection()
    # TODO: might send some reset information to the microcontroller
    return f"Cleared PapaGuy movement. Hope that saved the world."


@app.route('/connect/<port>')
def connect_serial(port):
    if papaguy.connection is not None:
        return print_serial_log()

    if papaguy.connect(port):
        Thread(target=papaguy.communicate).start()
        return redirect(url_for('print_serial_log'))
    else:
        return redirect(url_for('index'))


# convenience (if any)
@app.route('/connect')
def connect_serial_by_query():
    port = request.args.get('port')
    print("QUERY:", request.args, port)
    return connect_serial(port)

# linux compatibility
@app.route('/connect/dev/<port>')
def connect_serial_with_dev(port):
    return connect_serial(port=f"dev/{port}")


@app.route('/disconnect')
def disconnect():
    papaguy.disconnect()
    return redirect(url_for('index'))


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
        footer="<a href=\"" + url_for('disconnect') + "\">Disconnect</a>"
            + "<br/><a href=\"" + url_for('list_moves') + "\">Moves</a>"
            + "<br/><a href=\"" + url_for('emulate_radar_detection') + "\">Emulate Radar</a>",
        list=papaguy.log,
        refresh=3
    )


@app.route('/emulateradar')
def emulate_radar_detection():
    papaguy.send_message(GENERAL_MESSAGE.EMULATE_RADAR)
    return redirect(url_for('print_serial_log'))


@app.route('/precalc')
def force_batch_jobs():
    batch_jobs(True)
    return "Finished Forced Precalc."