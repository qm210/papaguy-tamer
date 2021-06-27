from flask import Flask

from . import VERSION

app = Flask(__name__)

@app.route('/')
def index():
    return f"papaguy-tamer v{VERSION} is running, thanks for checking by."

