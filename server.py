from flask import Flask, jsonify, send_file
from flask_cors import CORS
from configs.home_config import HOME_CONFIG

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes.


@app.route('/api/home_config')
def get_home_page_config():
    return jsonify(HOME_CONFIG)


@app.route("/api/rules/<language>")
def get_rules(language: str):
    rules_paths = HOME_CONFIG["rules_button"]["paths"]
    return send_file(rules_paths[language], mimetype="text/plain")


if __name__ == "__main__":
    from configs.app_config import HOST, PORT
    app.run(host=HOST, port=PORT, debug=True)
