from . import VERSION, PRODUCTION
from .app import app
from .batch import batch_jobs
from threading import Timer
from requests import get


def startup():
    try:
        response = get('http://localhost:8080', verify=False)
        print("auto request response", response.content)
    except:
        print("no response from auto request, visit manually plis")


if __name__ == '__main__':
    print("papaguy-tamer v", VERSION)

    batch_jobs()

    Timer(2, startup).start()

    if PRODUCTION:
        from waitress import serve
        serve(app, host='0.0.0.0', port=8080)
    else:
        app.run(debug=True, host='0.0.0.0', use_reloader=True)  # threaded=True is default

