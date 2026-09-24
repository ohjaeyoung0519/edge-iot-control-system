from flask import Flask, jsonify
from datetime import datetime
import json
import time
import urllib.request
import subprocess
import requests

app = Flask(__name__)

# =========================
# Device Config
# =========================

# 기존 ESP32 테스트 노드 또는 Node1 주소
# 기존 /api/esp32/ping 테스트용으로 남겨둠
ESP32_BASE_URL = "http://192.168.0.36"

# PC 전원 제어 대상 컴퓨터 IP
# 윈도우에서 ipconfig 했을 때 IPv4 주소로 바꾸기
PC_IP = "192.168.0.17"

# ESP32 Node2 주소
# Node2 업로드 후 Serial Monitor에 뜨는 IP로 바꾸기
NODE2_BASE_URL = "http://192.168.0.22"

# 전원 버튼 누른 뒤 재확인까지 기다리는 시간
PC_BOOT_WAIT_SEC = 8


# =========================
# Helper Functions
# =========================

def ping_pc():
    """
    Raspberry Pi에서 PC로 ping을 보내 네트워크 응답 여부를 확인함.
    ping 성공: True
    ping 실패: False
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", PC_IP],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_node2_ldr_status():
    """
    ESP32 Node2에서 LDR 조도센서 기반 PC LED 상태를 가져옴.
    Node2에는 /api/ldr endpoint가 있어야 함.
    """
    response = requests.get(
        f"{NODE2_BASE_URL}/api/ldr",
        timeout=2,
    )
    response.raise_for_status()
    return response.json()


def press_pc_power_button():
    """
    ESP32 Node2에 PC 전원 버튼을 짧게 누르라고 요청함.
    """
    response = requests.get(
        f"{NODE2_BASE_URL}/api/pc/power/press",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def decide_pc_power_state(ping_ok, led_on):
    """
    최종 PC 상태 판단 규칙.

    ping 성공 or LED ON  -> PC ON
    ping 실패 and LED OFF -> PC OFF 후보
    """
    if ping_ok or led_on:
        return "ON"

    return "OFF_CANDIDATE"


# =========================
# Basic APIs
# =========================

@app.route("/")
def home():
    return """
    <h1>Edge IoT Control System</h1>
    <p>Raspberry Pi server is running.</p>

    <h2>Basic</h2>
    <ul>
      <li><a href="/api/ping">/api/ping</a></li>
      <li><a href="/api/esp32/ping">/api/esp32/ping</a></li>
    </ul>

    <h2>PC Power Control</h2>
    <ul>
      <li><a href="/api/pc/status">/api/pc/status</a></li>
      <li><a href="/api/pc/power/on">/api/pc/power/on</a></li>
    </ul>
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
        with urllib.request.urlopen(
            f"{ESP32_BASE_URL}/api/ping",
            timeout=3
        ) as response:
            raw_data = response.read().decode("utf-8")

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        esp32_data = json.loads(raw_data)

        return jsonify({
            "status": "ok",
            "source": "raspberry-pi",
            "target": "esp32",
            "target_url": ESP32_BASE_URL,
            "latency_ms": round(elapsed_ms, 2),
            "esp32_response": esp32_data
        })

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "source": "raspberry-pi",
            "target": "esp32",
            "target_url": ESP32_BASE_URL,
            "latency_ms": round(elapsed_ms, 2),
            "message": str(error)
        }), 502


@app.route("/api/light/toggle")
def light_toggle():
    return jsonify({
        "status": "received",
        "command": "light_toggle",
        "note": "This is a server-side placeholder."
    })


# =========================
# PC Power Control APIs
# =========================

@app.route("/api/pc/status")
def pc_status():
    """
    PC 상태 확인 API.

    Raspberry Pi가 직접 PC에 ping을 보내고,
    ESP32 Node2에서 LDR 기반 LED 상태를 가져온 뒤,
    두 결과를 합쳐 최종 PC 상태를 판단함.
    """
    start_time = time.perf_counter()

    try:
        ping_ok = ping_pc()
        node2_data = get_node2_ldr_status()

        led_on = bool(node2_data.get("pc_led_on", False))
        ldr_raw = node2_data.get("ldr_raw")
        ldr_avg = node2_data.get("ldr_avg")
        ldr_threshold = node2_data.get("ldr_threshold")

        pc_state = decide_pc_power_state(ping_ok, led_on)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "pc_ip": PC_IP,
            "node2_base_url": NODE2_BASE_URL,
            "ping_ok": ping_ok,
            "ldr_led_on": led_on,
            "ldr_raw": ldr_raw,
            "ldr_avg": ldr_avg,
            "ldr_threshold": ldr_threshold,
            "pc_power_state": pc_state,
            "decision_rule": "ping_ok OR ldr_led_on => PC ON, otherwise OFF_CANDIDATE",
            "node2_response": node2_data,
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except requests.exceptions.RequestException as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "error_type": "node2_request_failed",
            "message": str(error),
            "pc_ip": PC_IP,
            "node2_base_url": NODE2_BASE_URL,
            "elapsed_ms": round(elapsed_ms, 2)
        }), 502

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(error),
            "elapsed_ms": round(elapsed_ms, 2)
        }), 500


@app.route("/api/pc/power/on")
def pc_power_on():
    """
    PC 전원 ON 요청 API.

    이미 켜져 있으면 전원 버튼을 누르지 않음.
    ping 실패 + LED OFF일 때만 ESP32 Node2에 전원 버튼 press 요청을 보냄.
    """
    start_time = time.perf_counter()

    try:
        # 1. 제어 전 상태 확인
        ping_before = ping_pc()
        node2_before = get_node2_ldr_status()

        led_before = bool(node2_before.get("pc_led_on", False))
        ldr_before = node2_before.get("ldr_avg")

        pc_state_before = decide_pc_power_state(ping_before, led_before)

        # 2. 이미 켜져 있으면 전원 버튼 누르지 않음
        if pc_state_before == "ON":
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return jsonify({
                "status": "ok",
                "action": "no_press",
                "reason": "PC is already ON",
                "before": {
                    "ping_ok": ping_before,
                    "ldr_led_on": led_before,
                    "ldr_avg": ldr_before,
                    "pc_power_state": pc_state_before
                },
                "elapsed_ms": round(elapsed_ms, 2)
            })

        # 3. ping 실패 + LED OFF일 때만 전원 버튼 누름
        press_result = press_pc_power_button()

        # 4. PC 부팅 대기
        time.sleep(PC_BOOT_WAIT_SEC)

        # 5. 제어 후 상태 재확인
        ping_after = ping_pc()
        node2_after = get_node2_ldr_status()

        led_after = bool(node2_after.get("pc_led_on", False))
        ldr_after = node2_after.get("ldr_avg")

        pc_state_after = decide_pc_power_state(ping_after, led_after)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "action": "press_power_button",
            "before": {
                "ping_ok": ping_before,
                "ldr_led_on": led_before,
                "ldr_avg": ldr_before,
                "pc_power_state": pc_state_before
            },
            "press_result": press_result,
            "wait_sec": PC_BOOT_WAIT_SEC,
            "after": {
                "ping_ok": ping_after,
                "ldr_led_on": led_after,
                "ldr_avg": ldr_after,
                "pc_power_state": pc_state_after
            },
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except requests.exceptions.RequestException as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "error_type": "node2_request_failed",
            "message": str(error),
            "pc_ip": PC_IP,
            "node2_base_url": NODE2_BASE_URL,
            "elapsed_ms": round(elapsed_ms, 2)
        }), 502

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(error),
            "elapsed_ms": round(elapsed_ms, 2)
        }), 500


# =========================
# Run Server
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
