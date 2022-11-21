from flask import Flask, render_template, send_from_directory, request, url_for, redirect
from time import time, ctime, sleep
from traceback import print_exc
import threading
import os

from . import VERSION, GENERAL_MESSAGE, AUTO_CONNECT_AFTER_SECONDS
from .func_papaguy_itself import PapaGuyItself
from .logic import LegacyLogic, RocketLogic
from .batch import batch_jobs
from .utils import read_file_content, write_to_file


app = Flask(__name__)
server_start_time = time()

# logic = LegacyLogic(do_random_moves=RANDOM_MOVES_ON_DEFAULT,
#                     idle_seconds_min=SECONDS_TO_IDLE_AT_LEAST,
#                     idle_seconds_max=SECONDS_TO_IDLE_AT_MOST,
#                     chance_of_talking=CHANCE_OF_TALKING,)
logic = RocketLogic()

papaguy = PapaGuyItself(logic)

temp_rocket_filename = "./rockets/last.xml"
fallback_rocket_filename = "./rockets/default.xml"


@app.before_first_request
def startup():
    print(f"Hello. Active Threads: {threading.activeCount()}")

    def autoconnect_loop():
        print("Try to start Autoconnect loop...")
        papaguy.try_autoconnect()
        try:
            threading.Timer(AUTO_CONNECT_AFTER_SECONDS, autoconnect_loop).start()
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
        do_random_moves=papaguy.logic.is_doing_random_moves(),
    )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/moves')
def list_moves():
    known_moves = papaguy.logic.load_moves_from_file()
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
def initiate_move(move_id=None):
    known_moves = papaguy.logic.get_moves()
    try:
        existing_move = next((move for move in known_moves if move['id'] == move_id))
    except:
        return f"Move \"{move_id}\" not found. Maybe refresh the main 'moves' page."

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

    print("try to connect, does connection exist?", papaguy.connection is not None)
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


@app.route('/rocket-starter')
def rocket_page():
    return render_template(
        'rocket-start.html',
        title=f"Running on port {papaguy.port}",
        disconnected={papaguy.port is None},
        script=read_file_content(temp_rocket_filename, fallback_rocket_filename),
        steps=read_file_content(".last.rocket.steps")
    )


@app.route('/submit-rocket-script', methods=['POST'])
def submit_rocket_script():
    script = request.form['rocket-script']
    write_to_file(temp_rocket_filename, script)

    steps = request.form.get('number-steps', default=200, type=int)
    write_to_file(".last.rocket.steps", steps)

    papaguy.logic.process_script(temp_rocket_filename, steps=steps)
    try:
        return redirect(url_for('rocket_page'))
    except Exception as ex:
        return print_exc()


@app.route('/rocket-socket')
def rocket_socket_page(message=""):
    is_rocket_logic = papaguy.logic.name() == RocketLogic.__name__
    return render_template(
        'rocket-socket.html',
        is_rocket_logic=is_rocket_logic,
        host=read_file_content(".last.rocket.host"),
        timeout_sec=read_file_content(".last.rocket.timeout"),
        message=message
    )


@app.route('/submit-rocket-socket', methods=['POST'])
def submit_rocket_socket():
    if papaguy.logic.name() != RocketLogic.__name__:
        return "is not a rocket papaguy. you can not be here."

    host = request.form['socket-host']
    write_to_file(".last.rocket.host", host)

    port = 1338
    if ":" in host:
        parse = host.split(':')
        host = parse[0]
        port = int(parse[1])

    timeout_input = request.form['timeout-sec']
    write_to_file(".last.rocket.timeout", timeout_input)
    timeout_sec = int(timeout_input) if timeout_input.isnumeric() else 30

    message = "this seems to have failed."
    if RocketLogic.connect_socket(papaguy.logic, host, port, timeout_sec=timeout_sec):
        message = f"socket connected on {host}:{port}... timeout after {timeout_sec} seconds"
    return rocket_socket_page(message)


@app.route('/clear')
def clear_papaguy():
    papaguy.logic.clear()
    print(threading.enumerate())
    return f"papaguy cleared (i.e. all threads, hopefully). activeCount: {threading.activeCount()}"
