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

# ESP32 Node1: 방 불 스위치 제어 노드
LIGHT_NODE_BASE_URL = "http://192.168.0.21"

# ESP32 Node2: PC 전원 LED 조도센서 + PC 전원 버튼 서보 노드
PC_NODE_BASE_URL = "http://192.168.0.22"

# 제어 대상 PC IP
PC_IP = "192.168.0.17"

# 기존 ESP32 ping 테스트용
ESP32_BASE_URL = LIGHT_NODE_BASE_URL

# PC 전원 버튼 누른 뒤 재확인까지 기다리는 시간
PC_BOOT_WAIT_SEC = 8


# =========================
# Common Helper Functions
# =========================

def request_json(url, timeout=3):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


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


# =========================
# Light Node Helper Functions
# =========================

def get_light_status():
    return request_json(f"{LIGHT_NODE_BASE_URL}/api/status", timeout=2)


def light_on():
    return request_json(f"{LIGHT_NODE_BASE_URL}/api/light/on", timeout=5)


def light_off():
    return request_json(f"{LIGHT_NODE_BASE_URL}/api/light/off", timeout=5)


def light_servo_rest():
    return request_json(f"{LIGHT_NODE_BASE_URL}/api/servo/rest", timeout=5)


# =========================
# PC Node Helper Functions
# =========================

def get_pc_node_ldr_status():
    return request_json(f"{PC_NODE_BASE_URL}/api/ldr", timeout=2)


def press_pc_power_button():
    return request_json(f"{PC_NODE_BASE_URL}/api/pc/power/press", timeout=5)


def decide_pc_power_state(ping_ok, led_on):
    """
    최종 PC 상태 판단 규칙.

    ping 성공 or LED ON  -> PC ON
    ping 실패 and LED OFF -> PC OFF 후보
    """
    if ping_ok or led_on:
        return "ON"

    return "OFF_CANDIDATE"


def get_combined_pc_status():
    """
    Raspberry Pi에서 PC ping을 확인하고,
    ESP32 Node2에서 조도센서 값을 가져와 최종 PC 전원 상태를 판단함.
    """
    start_time = time.perf_counter()

    ping_ok = ping_pc()
    pc_node_data = get_pc_node_ldr_status()

    led_on = bool(pc_node_data.get("pc_led_on", False))
    ldr_raw = pc_node_data.get("ldr_raw")
    ldr_avg = pc_node_data.get("ldr_avg")
    ldr_threshold = pc_node_data.get("ldr_threshold")

    pc_state = decide_pc_power_state(ping_ok, led_on)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return {
        "status": "ok",
        "pc_ip": PC_IP,
        "pc_node_base_url": PC_NODE_BASE_URL,
        "ping_ok": ping_ok,
        "ldr_led_on": led_on,
        "ldr_raw": ldr_raw,
        "ldr_avg": ldr_avg,
        "ldr_threshold": ldr_threshold,
        "pc_power_state": pc_state,
        "pc_message": "컴퓨터가 켜져있습니다" if pc_state == "ON" else "컴퓨터가 꺼져있는 후보 상태입니다",
        "servo_locked": pc_state == "ON",
        "servo_available": pc_state != "ON",
        "decision_rule": "ping_ok OR ldr_led_on => PC ON, otherwise OFF_CANDIDATE",
        "pc_node_response": pc_node_data,
        "elapsed_ms": round(elapsed_ms, 2)
    }


# =========================
# Web Pages
# =========================

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Edge IoT Control System</title>
</head>
<body>
  <h1>Edge IoT Control System</h1>
  <p>Raspberry Pi server is running.</p>

  <h2>Dashboard</h2>
  <p><a href="/dashboard">통합 대시보드 열기</a></p>

  <h2>Basic APIs</h2>
  <ul>
    <li><a href="/api/ping">/api/ping</a></li>
    <li><a href="/api/esp32/ping">/api/esp32/ping</a></li>
  </ul>

  <h2>Light APIs</h2>
  <ul>
    <li><a href="/api/light/status">/api/light/status</a></li>
    <li><a href="/api/light/on">/api/light/on</a></li>
    <li><a href="/api/light/off">/api/light/off</a></li>
    <li><a href="/api/light/servo/rest">/api/light/servo/rest</a></li>
  </ul>

  <h2>PC APIs</h2>
  <ul>
    <li><a href="/api/pc/status">/api/pc/status</a></li>
    <li><a href="/api/pc/power/on">/api/pc/power/on</a></li>
  </ul>
</body>
</html>
    """


@app.route("/pc")
def pc_page_redirect():
    return dashboard()


@app.route("/dashboard")
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Edge IoT Dashboard</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #111;
      color: #eee;
      margin: 0;
      padding: 24px;
    }
    .container {
      max-width: 720px;
      margin: 0 auto;
    }
    h1 {
      font-size: 26px;
      margin: 0 0 8px;
    }
    .sub {
      color: #aaa;
      margin-bottom: 22px;
    }
    .card {
      background: #1b1b1b;
      border-radius: 18px;
      padding: 22px;
      margin-bottom: 18px;
      box-shadow: 0 0 20px rgba(0,0,0,.35);
    }
    .card h2 {
      margin-top: 0;
      font-size: 22px;
    }
    .box {
      background: #262626;
      border-radius: 14px;
      padding: 14px;
      margin: 10px 0;
    }
    .label {
      color: #aaa;
      font-size: 13px;
    }
    .value {
      font-size: 21px;
      font-weight: bold;
      margin-top: 4px;
    }
    .on {
      color: #66ff99;
    }
    .off {
      color: #ffcc00;
    }
    .error {
      color: #ff6b6b;
    }
    button {
      width: 100%;
      padding: 15px;
      margin: 8px 0;
      border: 0;
      border-radius: 14px;
      font-size: 17px;
      font-weight: bold;
      cursor: pointer;
    }
    .statusBtn {
      background: #4da3ff;
      color: white;
    }
    .onBtn {
      background: #66ff99;
      color: #111;
    }
    .offBtn {
      background: #ff7b7b;
      color: #111;
    }
    .powerBtn {
      background: #ffcc00;
      color: #111;
    }
    .restBtn {
      background: #555;
      color: white;
    }
    button:disabled {
      background: #555;
      color: #aaa;
      cursor: not-allowed;
    }
    pre {
      white-space: pre-wrap;
      background: #0b0b0b;
      padding: 12px;
      border-radius: 12px;
      color: #ddd;
      overflow: auto;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Edge IoT Dashboard</h1>
    <div class="sub">Raspberry Pi + ESP32 Node1 Light + ESP32 Node2 PC Power</div>

    <div class="card">
      <h2>방 불 스위치 제어</h2>

      <div class="box">
        <div class="label">Light Node 상태</div>
        <div class="value" id="lightState">아직 확인 안 함</div>
      </div>

      <div class="box">
        <div class="label">Light Node 응답</div>
        <div class="value" id="lightMessage">-</div>
      </div>

      <button class="statusBtn" onclick="checkLightStatus()">방 불 노드 상태 확인</button>
      <button class="onBtn" onclick="lightOn()">방 불 켜기</button>
      <button class="offBtn" onclick="lightOff()">방 불 끄기</button>
      <button class="restBtn" onclick="lightRest()">방 불 서보 REST</button>

      <pre id="lightJsonBox">ready</pre>
    </div>

    <div class="card">
      <h2>PC 전원 제어</h2>

      <div class="box">
        <div class="label">현재 컴퓨터 상태</div>
        <div class="value" id="pcState">아직 확인 안 함</div>
      </div>

      <div class="box">
        <div class="label">상태 메시지</div>
        <div class="value" id="pcMessage">현재 상태 확인 버튼을 눌러 확인하세요</div>
      </div>

      <div class="box">
        <div class="label">Ping 결과</div>
        <div class="value" id="pingResult">-</div>
      </div>

      <div class="box">
        <div class="label">LDR 조도값 평균</div>
        <div class="value" id="ldrAvg">-</div>
      </div>

      <div class="box">
        <div class="label">LDR Threshold</div>
        <div class="value" id="ldrThreshold">-</div>
      </div>

      <button class="statusBtn" onclick="checkPcStatus()">PC 현재 상태 확인</button>
      <button class="powerBtn" id="pcPowerButton" onclick="pcPowerOn()" disabled>
        PC 전원 버튼 누르기
      </button>

      <pre id="pcJsonBox">ready</pre>
    </div>
  </div>

<script>
async function checkLightStatus() {
  const lightState = document.getElementById("lightState");
  const lightMessage = document.getElementById("lightMessage");
  const lightJsonBox = document.getElementById("lightJsonBox");

  lightState.innerText = "확인 중...";
  lightState.className = "value";
  lightMessage.innerText = "Light Node 확인 중...";

  try {
    const res = await fetch("/api/light/status");
    const data = await res.json();

    lightJsonBox.innerText = JSON.stringify(data, null, 2);

    if (data.status === "ok") {
      lightState.innerText = "ONLINE";
      lightState.className = "value on";
      lightMessage.innerText = "방 불 노드가 응답합니다.";
    } else {
      lightState.innerText = "ERROR";
      lightState.className = "value error";
      lightMessage.innerText = "방 불 노드 응답 오류";
    }
  } catch (err) {
    lightState.innerText = "ERROR";
    lightState.className = "value error";
    lightMessage.innerText = "방 불 노드 연결 실패";
    lightJsonBox.innerText = String(err);
  }
}

async function lightOn() {
  const lightMessage = document.getElementById("lightMessage");
  const lightJsonBox = document.getElementById("lightJsonBox");

  lightMessage.innerText = "방 불 켜기 명령 전송 중...";

  try {
    const res = await fetch("/api/light/on");
    const data = await res.json();

    lightJsonBox.innerText = JSON.stringify(data, null, 2);
    lightMessage.innerText = data.status === "ok" ? "방 불 켜기 명령 완료" : "방 불 켜기 명령 오류";
  } catch (err) {
    lightMessage.innerText = "방 불 켜기 요청 실패";
    lightJsonBox.innerText = String(err);
  }
}

async function lightOff() {
  const lightMessage = document.getElementById("lightMessage");
  const lightJsonBox = document.getElementById("lightJsonBox");

  lightMessage.innerText = "방 불 끄기 명령 전송 중...";

  try {
    const res = await fetch("/api/light/off");
    const data = await res.json();

    lightJsonBox.innerText = JSON.stringify(data, null, 2);
    lightMessage.innerText = data.status === "ok" ? "방 불 끄기 명령 완료" : "방 불 끄기 명령 오류";
  } catch (err) {
    lightMessage.innerText = "방 불 끄기 요청 실패";
    lightJsonBox.innerText = String(err);
  }
}

async function lightRest() {
  const lightMessage = document.getElementById("lightMessage");
  const lightJsonBox = document.getElementById("lightJsonBox");

  lightMessage.innerText = "방 불 서보 REST 요청 중...";

  try {
    const res = await fetch("/api/light/servo/rest");
    const data = await res.json();

    lightJsonBox.innerText = JSON.stringify(data, null, 2);
    lightMessage.innerText = "방 불 서보 REST 완료";
  } catch (err) {
    lightMessage.innerText = "방 불 서보 REST 요청 실패";
    lightJsonBox.innerText = String(err);
  }
}

async function checkPcStatus() {
  const pcState = document.getElementById("pcState");
  const pcMessage = document.getElementById("pcMessage");
  const pingResult = document.getElementById("pingResult");
  const ldrAvg = document.getElementById("ldrAvg");
  const ldrThreshold = document.getElementById("ldrThreshold");
  const powerButton = document.getElementById("pcPowerButton");
  const pcJsonBox = document.getElementById("pcJsonBox");

  pcState.innerText = "확인 중...";
  pcState.className = "value";
  pcMessage.innerText = "조도값과 ping을 확인하는 중입니다...";
  powerButton.disabled = true;

  try {
    const res = await fetch("/api/pc/status");
    const data = await res.json();

    pcJsonBox.innerText = JSON.stringify(data, null, 2);

    if (data.status !== "ok") {
      pcState.innerText = "ERROR";
      pcState.className = "value error";
      pcMessage.innerText = "PC 상태 확인 실패";
      return;
    }

    pcState.innerText = data.pc_power_state;
    pingResult.innerText = data.ping_ok ? "PING 성공" : "PING 실패";
    ldrAvg.innerText = data.ldr_avg;
    ldrThreshold.innerText = data.ldr_threshold;

    if (data.pc_power_state === "ON") {
      pcState.className = "value on";
      pcMessage.innerText = "컴퓨터가 켜져있습니다. 전원 버튼은 잠금 처리됩니다.";
      powerButton.disabled = true;
    } else {
      pcState.className = "value off";
      pcMessage.innerText = "컴퓨터가 꺼져있는 후보 상태입니다. 전원 버튼을 누를 수 있습니다.";
      powerButton.disabled = false;
    }

  } catch (err) {
    pcState.innerText = "ERROR";
    pcState.className = "value error";
    pcMessage.innerText = "Raspberry Pi 또는 PC Node2 연결 오류";
    pcJsonBox.innerText = String(err);
    powerButton.disabled = true;
  }
}

async function pcPowerOn() {
  const powerButton = document.getElementById("pcPowerButton");
  const pcJsonBox = document.getElementById("pcJsonBox");
  const pcMessage = document.getElementById("pcMessage");

  const ok = confirm("현재 상태가 OFF 후보일 때만 전원 버튼을 누릅니다. 진행할까요?");
  if (!ok) return;

  powerButton.disabled = true;
  pcMessage.innerText = "PC 전원 버튼 요청 중입니다...";

  try {
    const res = await fetch("/api/pc/power/on");
    const data = await res.json();

    pcJsonBox.innerText = JSON.stringify(data, null, 2);

    if (data.action === "no_press") {
      pcMessage.innerText = "컴퓨터가 이미 켜져 있어서 전원 버튼을 누르지 않았습니다.";
    } else if (data.action === "press_power_button") {
      pcMessage.innerText = "전원 버튼을 눌렀고, 상태를 재확인했습니다.";
    } else {
      pcMessage.innerText = "응답 내용을 확인하세요.";
    }

    await checkPcStatus();

  } catch (err) {
    pcJsonBox.innerText = String(err);
    pcMessage.innerText = "PC 전원 버튼 요청 실패";
    powerButton.disabled = false;
  }
}

// 페이지 열면 자동으로 한 번 확인
checkLightStatus();
checkPcStatus();
</script>
</body>
</html>
    """


# =========================
# Basic APIs
# =========================

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


# =========================
# Light Control APIs
# =========================

@app.route("/api/light/status")
def api_light_status():
    start_time = time.perf_counter()

    try:
        data = get_light_status()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "target": "light-node",
            "light_node_base_url": LIGHT_NODE_BASE_URL,
            "light_response": data,
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "target": "light-node",
            "light_node_base_url": LIGHT_NODE_BASE_URL,
            "message": str(error),
            "elapsed_ms": round(elapsed_ms, 2)
        }), 502


@app.route("/api/light/on")
def api_light_on():
    start_time = time.perf_counter()

    try:
        data = light_on()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "action": "light_on",
            "light_response": data,
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "action": "light_on",
            "message": str(error),
            "elapsed_ms": round(elapsed_ms, 2)
        }), 502


@app.route("/api/light/off")
def api_light_off():
    start_time = time.perf_counter()

    try:
        data = light_off()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "action": "light_off",
            "light_response": data,
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "action": "light_off",
            "message": str(error),
            "elapsed_ms": round(elapsed_ms, 2)
        }), 502


@app.route("/api/light/servo/rest")
def api_light_servo_rest():
    start_time = time.perf_counter()

    try:
        data = light_servo_rest()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "action": "light_servo_rest",
            "light_response": data,
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except Exception as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "action": "light_servo_rest",
            "message": str(error),
            "elapsed_ms": round(elapsed_ms, 2)
        }), 502


# 기존 호환용
@app.route("/api/light/toggle")
def light_toggle():
    return jsonify({
        "status": "received",
        "command": "light_toggle",
        "note": "Use /api/light/on or /api/light/off instead."
    })


# =========================
# PC Power Control APIs
# =========================

@app.route("/api/pc/status")
def pc_status():
    try:
        data = get_combined_pc_status()
        return jsonify(data)

    except requests.exceptions.RequestException as error:
        return jsonify({
            "status": "error",
            "error_type": "pc_node_request_failed",
            "message": str(error),
            "pc_ip": PC_IP,
            "pc_node_base_url": PC_NODE_BASE_URL
        }), 502

    except Exception as error:
        return jsonify({
            "status": "error",
            "error_type": "unexpected_error",
            "message": str(error)
        }), 500


@app.route("/api/pc/power/on")
def pc_power_on():
    start_time = time.perf_counter()

    try:
        # 1. 누르기 전 상태 확인
        before = get_combined_pc_status()

        # 2. 이미 켜져 있으면 절대 전원 버튼 누르지 않음
        if before["pc_power_state"] == "ON":
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return jsonify({
                "status": "ok",
                "action": "no_press",
                "reason": "PC is already ON",
                "message": "컴퓨터가 이미 켜져 있어서 전원 버튼을 누르지 않았습니다.",
                "before": before,
                "elapsed_ms": round(elapsed_ms, 2)
            })

        # 3. 꺼짐 후보일 때만 전원 버튼 누름
        press_result = press_pc_power_button()

        # 4. 부팅 대기
        time.sleep(PC_BOOT_WAIT_SEC)

        # 5. 누른 뒤 상태 재확인
        after = get_combined_pc_status()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "ok",
            "action": "press_power_button",
            "message": "PC OFF 후보 상태였기 때문에 전원 버튼을 눌렀습니다.",
            "before": before,
            "press_result": press_result,
            "wait_sec": PC_BOOT_WAIT_SEC,
            "after": after,
            "elapsed_ms": round(elapsed_ms, 2)
        })

    except requests.exceptions.RequestException as error:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return jsonify({
            "status": "error",
            "error_type": "pc_node_request_failed",
            "message": str(error),
            "pc_ip": PC_IP,
            "pc_node_base_url": PC_NODE_BASE_URL,
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
