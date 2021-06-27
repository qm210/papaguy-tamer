from . import VERSION, PRODUCTION
from .app import app

if __name__ == '__main__':
    print("papaguy-tamer v", VERSION)

    if PRODUCTION:
        from waitress import serve
        serve(app, host='0.0.0.0', port=8080)
    else:
        app.run(debug=True, host='0.0.0.0', use_reloader=True) # threaded=True is default

