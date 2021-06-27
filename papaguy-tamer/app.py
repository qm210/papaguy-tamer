from flask import Flask, render_template
from os import listdir
from time import time, ctime

from . import VERSION

app = Flask(__name__)

basedir = "./papaguy-tamer"

start_time = time()

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
        'list.html',
        title="Moves",
        message=f"{len(available_moves)} moves found.",
        list=available_moves
    )
