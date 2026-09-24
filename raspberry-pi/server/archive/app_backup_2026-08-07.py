from flask import Flask, jsonify
from datetime import datetime
import json
import time
import urllib.request

app = Flask(__name__)

ESP32_BASE_URL = "http://192.168.0.36"


@app.route("/")
def home():
    return """
    <h1>Edge IoT Control System</h1>
    <p>Raspberry Pi server is running.</p>
    <p>ESP32 connection test endpoint: /api/esp32/ping</p>
    """


@app.route("/api/ping")
def ping():
    return jsonify({
        "status": "ok",
        "device": "raspberry-pi",
        "role": "central-server",
        "time": datetime.now().isoformat()
    })


@app.route("/api/esp32/ping")
def esp32_ping():
    start_time = time.perf_counter()

    try:
        with urllib.request.urlopen(f"{ESP32_BASE_URL}/api/ping", timeout=3) as response:
            raw_data = response.read().decode("utf-8")

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        esp32_data = json.loads(raw_data)

        return jsonify({
            "status": "ok",
            "source": "raspberry-pi",
            "target": "esp32",
            "latency_ms": round(elapsed_ms, 2),
            "esp32_response": esp32_data
        })

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "source": "raspberry-pi",
            "target": "esp32",
            "latency_ms": round(elapsed_ms, 2),
            "message": str(error)
        }), 502


@app.route("/api/light/toggle")
def light_toggle():
    return jsonify({
        "status": "received",
        "command": "light_toggle",
        "note": "ESP32 servo control is not connected yet. This is a server-side placeholder."
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
