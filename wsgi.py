from main import get_app
import logging
app = get_app().app

if __name__ == '__main__':
    # Mute werkzeug logging - we do this ourselves
    logging.getLogger('werkzeug').setLevel("WARNING")
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=True)