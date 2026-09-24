from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Edge IoT Control System</h1>
    <p>Raspberry Pi server is running.</p>
    <p>Next step: connect ESP32 control node.</p>
    """

@app.route("/api/ping")
def ping():
    return jsonify({
        "status": "ok",
        "device": "raspberry-pi",
        "role": "central-server",
        "time": datetime.now().isoformat()
    })

@app.route("/api/light/toggle")
def light_toggle():
    return jsonify({
        "status": "received",
        "command": "light_toggle",
        "note": "ESP32 is not connected yet. This is a server-side test."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)