from flask import Flask, render_template, send_from_directory, request, url_for, redirect
from time import time, ctime, sleep
from threading import Timer
import os

from . import VERSION, GENERAL_MESSAGE, AUTO_CONNECT_AFTER_SECONDS, \
    RANDOM_MOVES_ON_DEFAULT, SECONDS_TO_IDLE_AT_LEAST, SECONDS_TO_IDLE_AT_MOST, CHANCE_OF_TALKING

from .func_papaguy_itself import PapaGuyItself
from .logic import LegacyLogic, RocketLogic
from .batch import batch_jobs


app = Flask(__name__)
server_start_time = time()

logic = LegacyLogic(do_random_moves=RANDOM_MOVES_ON_DEFAULT,
                    idle_seconds_min=SECONDS_TO_IDLE_AT_LEAST,
                    idle_seconds_max=SECONDS_TO_IDLE_AT_MOST,
                    chance_of_talking=CHANCE_OF_TALKING,)
papaguy = PapaGuyItself(logic)


@app.before_first_request
def startup():
    print("Hello.")
    def autoconnect_loop():
        print("Start Autoconnect loop.")
        papaguy.try_autoconnect()
        try:
            Timer(AUTO_CONNECT_AFTER_SECONDS, autoconnect_loop).start()
        except:
            print("could not start threading.Timer, use blocking delay (few seconds)")
            sleep(5)
            autoconnect_loop()
    autoconnect_loop()
    return redirect(url_for('index'))


@app.errorhandler(Exception)
def handle_exception(err):
    print("!!! ERROR", err)
    try_autoconnect()
    return redirect(url_for('list_serial_ports'))


@app.route('/')
def index():
    return render_template(
        'home.html',
        title=f"papaguy-tamer v{VERSION} is running since {ctime(server_start_time)}",
        message=f"qm says thanks for checking by.",
        connected=papaguy.connection is not None,
        do_random_moves = papaguy.do_random_moves,
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/moves')
def list_moves():
    known_moves = papaguy.load_moves()
    return render_template(
        'moves.html',
        title="Moves",
        message=f"Found {len(known_moves)} thingies.",
        list=known_moves
    )

@app.route('/toggle_random_moves')
def toggle_random_moves():
    papaguy.toggle_random_moves()
    return redirect(url_for('index'))


@app.route('/movesdebug')
def list_moves_to_console():
    papaguy.print_all_moves()
    return index()


@app.route('/moves/<id>')
def initiate_move(id=None):
    known_moves = papaguy.load_moves()  # wir gönnen uns, statt einfach liste vom cache zu nehmen
    try:
        existing_move = next((move for move in known_moves if move['id'] == id))
    except:
        return f"Move \"{id}\" not found. Maybe refresh the main 'moves' page."

    if papaguy.execute_move(existing_move):
        papaguy.reset_log(f"Executing {existing_move['id']} [{existing_move['type']}]")
    else:
        papaguy.reset_log("Didn't work. Maybe there is still a move ongoing?")

    return redirect(url_for('list_moves'))


@app.route('/panic')
def cancel_all_moves():
    papaguy.clear_connection()
    # TODO: might send some reset information to the microcontroller
    return f"Cleared PapaGuy movement. Hope that saved the world."


@app.route('/connect/<port>')
def connect_serial(port):
    def kthxbye():
        return redirect(url_for('print_serial_log'))

    print("try to connect, does connection exist?", papaguy.connection is not None, "... should route to", route)
    if papaguy.connection is not None:
        return kthxbye()

    if papaguy.connect(port):
        return kthxbye()
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
    return connect_serial(port=f"/dev/{port}")


@app.route('/disconnect')
def disconnect():
    papaguy.disconnect()
    return redirect(url_for('index'))


@app.route('/portlist')
def list_serial_ports():
    ports = papaguy.get_port_list()
    links = ['./connect/' + port for port in ports]
    return render_template(
        'list.html',
        title="COM ports",
        message=f"Currently connected to port: {papaguy.port}",
        list=ports,
        href=links
    )


@app.route('/autoconn')
def try_autoconnect():
    papaguy.try_autoconnect()
    return redirect(url_for('list_moves'))


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