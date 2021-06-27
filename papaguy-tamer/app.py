from flask import Flask, render_template
from os import listdir
from time import time, ctime, sleep
from serial import Serial
from dataclasses import dataclass, field
from threading import Thread

from . import VERSION

app = Flask(__name__)

basedir = "./papaguy-tamer"

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

@app.route('/moves')
def list_moves():
    available_moves = listdir(f"{basedir}/moves")
    return render_template(
        'moves.html',
        title="Moves",
        message=f"{len(available_moves)} moves found.",
        list=available_moves
    )

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

