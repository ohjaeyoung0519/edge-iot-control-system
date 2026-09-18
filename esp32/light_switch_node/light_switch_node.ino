#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>
#include <MQTT.h>

#include "wifi_config.h"

// ==================================================
// Light Switch Node Config
// ==================================================

const char* NODE_NAME = "light-switch-node";
const char* NODE_ROLE = "room-light-control";

// --------------------
// Servo
// --------------------

const int SERVO_PIN = 18;

// Local Buttons
const int BUTTON_ON_PIN = 21;
const int BUTTON_OFF_PIN = 22;

// Servo Angles
const int REST_ANGLE = 90;
const int PRESS_ON_ANGLE = 50;
const int PRESS_OFF_ANGLE = 140;

// Servo Timing
const int PRESS_HOLD_MS = 400;
const int RETURN_WAIT_MS = 600;

const unsigned long DEBOUNCE_MS = 300;

// Servo PWM Range
const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2400;

// true = 동작 완료 후 Servo PWM을 detach하여 holding torque를 해제
const bool DETACH_AFTER_MOVE = true;


// ==================================================
// MQTT Config
// ==================================================

// Raspberry Pi Mosquitto Broker
const char* MQTT_BROKER = "192.168.0.35";
const int MQTT_PORT = 1883;

// Benchmark 전용 Topic
const char* MQTT_BENCHMARK_CMD_TOPIC =
  "edge/light/benchmark/cmd";

const char* MQTT_BENCHMARK_ACK_TOPIC =
  "edge/light/benchmark/ack";

// Broker 재연결 시도 간격
const unsigned long MQTT_RECONNECT_INTERVAL_MS = 2000;


// ==================================================
// Global Objects
// ==================================================

WebServer server(80);

Servo servo;

// MQTT가 사용할 TCP Connection
WiFiClient mqttNetwork;

// MQTT Read Buffer
MQTTClient mqttClient(512);


// ==================================================
// Servo State
// ==================================================

bool servoBusy = false;
bool servoAttached = false;

unsigned long lastButtonOnMs = 0;
unsigned long lastButtonOffMs = 0;

int lastActionAngle = REST_ANGLE;
String lastAction = "rest";


// ==================================================
// MQTT State
// ==================================================

unsigned long lastMqttReconnectAttemptMs = 0;

// MQTT callback 안에서는 ACK를 바로 publish하지 않고,
// 측정값만 저장한 뒤 loop()에서 publish함.

bool mqttAckPending = false;

String mqttPendingCommandId = "";

int mqttPendingQos = 0;

unsigned long mqttPendingProcessingUs = 0;

uint32_t mqttPendingFreeHeap = 0;
uint32_t mqttPendingMinFreeHeap = 0;
uint32_t mqttPendingMaxAllocHeap = 0;

int32_t mqttPendingRssi = 0;


// ==================================================
// Servo Helper Functions
// ==================================================

void attachServoIfNeeded() {

  if (!servoAttached) {

    servo.setPeriodHertz(50);

    servo.attach(
      SERVO_PIN,
      SERVO_MIN_US,
      SERVO_MAX_US
    );

    servoAttached = true;

    delay(100);
  }
}


void detachServoIfNeeded() {

  if (
    DETACH_AFTER_MOVE &&
    servoAttached
  ) {

    servo.detach();

    servoAttached = false;
  }
}


bool pressServo(
  int targetAngle,
  const String& actionName
) {

  if (servoBusy) {
    return false;
  }

  servoBusy = true;

  uint32_t heapBefore =
    ESP.getFreeHeap();

  unsigned long startUs =
    micros();

  attachServoIfNeeded();

  // 실제 Switch Press
  servo.write(targetAngle);

  delay(PRESS_HOLD_MS);

  // Rest Position
  servo.write(REST_ANGLE);

  delay(RETURN_WAIT_MS);

  detachServoIfNeeded();

  unsigned long endUs =
    micros();

  uint32_t heapAfter =
    ESP.getFreeHeap();

  lastActionAngle =
    targetAngle;

  lastAction =
    actionName;

  Serial.println();

  Serial.print(
    "[SERVO] action="
  );

  Serial.println(
    actionName
  );

  Serial.print(
    "[SERVO] target_angle="
  );

  Serial.println(
    targetAngle
  );

  Serial.print(
    "[SERVO] duration_ms="
  );

  Serial.println(
    (endUs - startUs) / 1000.0
  );

  Serial.print(
    "[SERVO] heap_before="
  );

  Serial.println(
    heapBefore
  );

  Serial.print(
    "[SERVO] heap_after="
  );

  Serial.println(
    heapAfter
  );

  Serial.print(
    "[SERVO] heap_diff="
  );

  Serial.println(
    (int)heapAfter -
    (int)heapBefore
  );

  servoBusy = false;

  return true;
}


// ==================================================
// JSON Status
// ==================================================

String jsonStatus() {

  String json = "{";

  json +=
    "\"status\":\"ok\",";

  json +=
    "\"node\":\"" +
    String(NODE_NAME) +
    "\",";

  json +=
    "\"role\":\"" +
    String(NODE_ROLE) +
    "\",";

  json +=
    "\"ip\":\"" +
    WiFi.localIP().toString() +
    "\",";

  json +=
    "\"uptime_ms\":" +
    String(millis()) +
    ",";

  json +=
    "\"free_heap\":" +
    String(ESP.getFreeHeap()) +
    ",";

  json +=
    "\"rssi\":" +
    String(WiFi.RSSI()) +
    ",";

  json +=
    "\"mqtt_connected\":" +
    String(
      mqttClient.connected()
      ? "true"
      : "false"
    ) +
    ",";

  json +=
    "\"servo_busy\":" +
    String(
      servoBusy
      ? "true"
      : "false"
    ) +
    ",";

  json +=
    "\"servo_attached\":" +
    String(
      servoAttached
      ? "true"
      : "false"
    ) +
    ",";

  json +=
    "\"rest_angle\":" +
    String(REST_ANGLE) +
    ",";

  json +=
    "\"press_on_angle\":" +
    String(PRESS_ON_ANGLE) +
    ",";

  json +=
    "\"press_off_angle\":" +
    String(PRESS_OFF_ANGLE) +
    ",";

  json +=
    "\"last_action\":\"" +
    lastAction +
    "\",";

  json +=
    "\"last_action_angle\":" +
    String(lastActionAngle);

  json += "}";

  return json;
}


// ==================================================
// HTTP Handlers
// ==================================================

void handleRoot() {

  String html = "";

  html +=
    "<!DOCTYPE html>"
    "<html>"
    "<head>";

  html +=
    "<meta name='viewport' "
    "content='width=device-width, initial-scale=1'>";

  html +=
    "<title>Light Switch Node</title>";

  html +=
    "<style>";

  html +=
    "body{"
    "font-family:Arial,sans-serif;"
    "background:#111;"
    "color:#eee;"
    "padding:24px;"
    "}";

  html +=
    ".card{"
    "background:#1e1e1e;"
    "border-radius:16px;"
    "padding:20px;"
    "max-width:420px;"
    "margin:auto;"
    "}";

  html +=
    "h1{font-size:24px;margin-top:0;}";

  html +=
    "button{"
    "width:100%;"
    "padding:18px;"
    "margin:8px 0;"
    "border:0;"
    "border-radius:12px;"
    "font-size:18px;"
    "font-weight:bold;"
    "}";

  html +=
    ".on{background:#f5c542;color:#111;}";

  html +=
    ".off{background:#444;color:white;}";

  html +=
    ".status{background:#2f80ed;color:white;}";

  html +=
    "pre{"
    "background:#000;"
    "padding:12px;"
    "border-radius:8px;"
    "overflow:auto;"
    "}";

  html +=
    "</style>";

  html +=
    "</head>"
    "<body>";

  html +=
    "<div class='card'>";

  html +=
    "<h1>Light Switch Node</h1>";

  html +=
    "<p>ESP32 room light control node</p>";

  html +=
    "<button class='on' "
    "onclick=\"fetch('/api/light/on')"
    ".then(r=>r.text())"
    ".then(t=>out.textContent=t)\">"
    "Light ON"
    "</button>";

  html +=
    "<button class='off' "
    "onclick=\"fetch('/api/light/off')"
    ".then(r=>r.text())"
    ".then(t=>out.textContent=t)\">"
    "Light OFF"
    "</button>";

  html +=
    "<button class='status' "
    "onclick=\"fetch('/api/status')"
    ".then(r=>r.text())"
    ".then(t=>out.textContent=t)\">"
    "Status"
    "</button>";

  html +=
    "<pre id='out'>Ready</pre>";

  html +=
    "</div>"
    "</body>"
    "</html>";

  server.send(
    200,
    "text/html",
    html
  );
}


void handlePing() {

  String json = "{";

  json +=
    "\"status\":\"ok\",";

  json +=
    "\"node\":\"" +
    String(NODE_NAME) +
    "\",";

  json +=
    "\"role\":\"" +
    String(NODE_ROLE) +
    "\",";

  json +=
    "\"uptime_ms\":" +
    String(millis()) +
    ",";

  json +=
    "\"free_heap\":" +
    String(ESP.getFreeHeap()) +
    ",";

  json +=
    "\"rssi\":" +
    String(WiFi.RSSI());

  json += "}";

  server.send(
    200,
    "application/json",
    json
  );
}


// ==================================================
// HTTP Benchmark Handler
// ==================================================
//
// 실제 Servo 동작 없음.
// 의도적인 delay 없음.
//
// HTTP Benchmark:
//
// Pi
//   ↓
// /api/benchmark?id=157
//   ↓
// ESP32 측정
//   ↓
// JSON Response
//

void handleBenchmark() {

  unsigned long startUs =
    micros();

  String commandId = "";

  if (server.hasArg("id")) {

    commandId =
      server.arg("id");
  }

  uint32_t freeHeap =
    ESP.getFreeHeap();

  uint32_t minFreeHeap =
    ESP.getMinFreeHeap();

  uint32_t maxAllocHeap =
    ESP.getMaxAllocHeap();

  int32_t rssi =
    WiFi.RSSI();

  unsigned long processingUs =
    micros() - startUs;

  String json = "{";

  json +=
    "\"command_id\":\"" +
    commandId +
    "\",";

  json +=
    "\"status\":\"ok\",";

  json +=
    "\"esp_processing_us\":" +
    String(processingUs) +
    ",";

  json +=
    "\"free_heap\":" +
    String(freeHeap) +
    ",";

  json +=
    "\"min_free_heap\":" +
    String(minFreeHeap) +
    ",";

  json +=
    "\"max_alloc_heap\":" +
    String(maxAllocHeap) +
    ",";

  json +=
    "\"rssi_dbm\":" +
    String(rssi);

  json += "}";

  server.send(
    200,
    "application/json",
    json
  );
}


void handleStatus() {

  server.send(
    200,
    "application/json",
    jsonStatus()
  );
}


void handleLightOn() {

  bool result =
    pressServo(
      PRESS_ON_ANGLE,
      "light_on"
    );

  String json = "{";

  json +=
    "\"status\":\"";

  json +=
    result
    ? "ok"
    : "busy";

  json += "\",";

  json +=
    "\"action\":\"light_on\",";

  json +=
    "\"target_angle\":" +
    String(PRESS_ON_ANGLE) +
    ",";

  json +=
    "\"node\":\"" +
    String(NODE_NAME) +
    "\",";

  json +=
    "\"free_heap\":" +
    String(ESP.getFreeHeap());

  json += "}";

  server.send(
    result ? 200 : 409,
    "application/json",
    json
  );
}


void handleLightOff() {

  bool result =
    pressServo(
      PRESS_OFF_ANGLE,
      "light_off"
    );

  String json = "{";

  json +=
    "\"status\":\"";

  json +=
    result
    ? "ok"
    : "busy";

  json += "\",";

  json +=
    "\"action\":\"light_off\",";

  json +=
    "\"target_angle\":" +
    String(PRESS_OFF_ANGLE) +
    ",";

  json +=
    "\"node\":\"" +
    String(NODE_NAME) +
    "\",";

  json +=
    "\"free_heap\":" +
    String(ESP.getFreeHeap());

  json += "}";

  server.send(
    result ? 200 : 409,
    "application/json",
    json
  );
}


void handleServoReset() {

  attachServoIfNeeded();

  servo.write(
    REST_ANGLE
  );

  delay(300);

  lastAction =
    "rest";

  lastActionAngle =
    REST_ANGLE;

  detachServoIfNeeded();

  String json = "{";

  json +=
    "\"status\":\"ok\",";

  json +=
    "\"action\":\"servo_rest\",";

  json +=
    "\"rest_angle\":" +
    String(REST_ANGLE);

  json += "}";

  server.send(
    200,
    "application/json",
    json
  );
}


// ==================================================
// Wi-Fi
// ==================================================

void connectWiFi() {

  Serial.println();

  Serial.println(
    "[WiFi] Connecting..."
  );

  WiFi.mode(
    WIFI_STA
  );

  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );

  int retry = 0;

  while (
    WiFi.status() !=
    WL_CONNECTED
  ) {

    delay(500);

    Serial.print(".");

    retry++;

    if (retry > 60) {

      Serial.println();

      Serial.println(
        "[WiFi] Failed. Restarting..."
      );

      ESP.restart();
    }
  }

  Serial.println();

  Serial.println(
    "[WiFi] Connected"
  );

  WiFi.setSleep(false);
  Serial.println("[WiFi] Sleep mode: OFF");

  Serial.print(
    "[WiFi] IP address: "
  );

  Serial.println(
    WiFi.localIP()
  );

  Serial.print(
    "[WiFi] RSSI: "
  );

  Serial.println(
    WiFi.RSSI()
  );
}

// ==================================================
// MQTT Benchmark Receive
// ==================================================
//
// Command Payload:
//
// command_id|qos
//
// 예:
//
// mqtt-qos0-1-157|0
//
// mqtt-qos1-1-157|1
//
// callback에서는 ACK Publish를 하지 않음.
// 측정 결과만 저장한 뒤 loop()에서 ACK를 Publish함.
//

void mqttMessageReceived(
  String& topic,
  String& payload
) {

  if (
    topic !=
    MQTT_BENCHMARK_CMD_TOPIC
  ) {

    return;
  }

  unsigned long startUs =
    micros();

  // 이전 ACK가 아직 처리되지 않았다면
  // 새 요청은 받지 않음.
  //
  // 본 실험에서는 sequential request/ACK 방식이므로
  // 정상 조건에서는 발생하지 않아야 함.

  if (mqttAckPending) {

    Serial.println(
      "[MQTT] Benchmark command ignored: ACK pending"
    );

    return;
  }

  int separator =
    payload.lastIndexOf('|');

  String commandId =
    payload;

  int qos = 0;

  if (separator >= 0) {

    commandId =
      payload.substring(
        0,
        separator
      );

    qos =
      payload.substring(
        separator + 1
      ).toInt();
  }

  // 이번 실험은 QoS 0 / 1만 사용
  if (
    qos != 0 &&
    qos != 1
  ) {

    qos = 0;
  }

  uint32_t freeHeap =
    ESP.getFreeHeap();

  uint32_t minFreeHeap =
    ESP.getMinFreeHeap();

  uint32_t maxAllocHeap =
    ESP.getMaxAllocHeap();

  int32_t rssi =
    WiFi.RSSI();

  unsigned long processingUs =
    micros() - startUs;

  // loop()에서 ACK Publish하기 위해 저장

  mqttPendingCommandId =
    commandId;

  mqttPendingQos =
    qos;

  mqttPendingProcessingUs =
    processingUs;

  mqttPendingFreeHeap =
    freeHeap;

  mqttPendingMinFreeHeap =
    minFreeHeap;

  mqttPendingMaxAllocHeap =
    maxAllocHeap;

  mqttPendingRssi =
    rssi;

  mqttAckPending =
    true;
}


// ==================================================
// MQTT Application ACK
// ==================================================

void publishPendingMqttAck() {

  if (!mqttAckPending) {
    return;
  }

  // Broker 연결이 끊긴 경우
  // 늦게 ACK를 보내지 않고 해당 요청은 실패로 처리.
  if (!mqttClient.connected()) {

    Serial.println(
      "[MQTT] ACK dropped: broker disconnected"
    );

    mqttAckPending =
      false;

    return;
  }

  String json = "{";

  json +=
    "\"command_id\":\"" +
    mqttPendingCommandId +
    "\",";

  json +=
    "\"status\":\"ok\",";

  json +=
    "\"qos\":" +
    String(mqttPendingQos) +
    ",";

  json +=
    "\"esp_processing_us\":" +
    String(
      mqttPendingProcessingUs
    ) +
    ",";

  json +=
    "\"free_heap\":" +
    String(
      mqttPendingFreeHeap
    ) +
    ",";

  json +=
    "\"min_free_heap\":" +
    String(
      mqttPendingMinFreeHeap
    ) +
    ",";

  json +=
    "\"max_alloc_heap\":" +
    String(
      mqttPendingMaxAllocHeap
    ) +
    ",";

  json +=
    "\"rssi_dbm\":" +
    String(
      mqttPendingRssi
    );

  json += "}";

  bool publishResult =
    mqttClient.publish(
      MQTT_BENCHMARK_ACK_TOPIC,
      json,
      false,
      mqttPendingQos
    );

  if (!publishResult) {

    Serial.println(
      "[MQTT] Benchmark ACK publish FAILED"
    );
  }

  mqttAckPending =
    false;
}


// ==================================================
// MQTT Connection
// ==================================================

void tryConnectMQTT() {

  if (
    mqttClient.connected()
  ) {

    return;
  }

  Serial.println();

  Serial.println(
    "[MQTT] Connecting to broker..."
  );

  String clientId =
    "light-node-" +
    String(
      (uint32_t)ESP.getEfuseMac(),
      HEX
    );

  Serial.print(
    "[MQTT] Client ID: "
  );

  Serial.println(
    clientId
  );

  bool connected =
    mqttClient.connect(
      clientId.c_str()
    );

  if (!connected) {

    Serial.println(
      "[MQTT] Connection failed"
    );

    return;
  }

  Serial.println(
    "[MQTT] Connected!"
  );

  // QoS 1로 Subscribe.
  //
  // QoS0 Command는 QoS0으로,
  // QoS1 Command는 QoS1으로 전달 가능하도록 함.

  bool subscribed =
    mqttClient.subscribe(
      MQTT_BENCHMARK_CMD_TOPIC,
      1
    );

  Serial.print(
    "[MQTT] Subscribe result: "
  );

  Serial.println(
    subscribed
    ? "OK"
    : "FAILED"
  );

  Serial.print(
    "[MQTT] Benchmark CMD topic: "
  );

  Serial.println(
    MQTT_BENCHMARK_CMD_TOPIC
  );

  Serial.print(
    "[MQTT] Benchmark ACK topic: "
  );

  Serial.println(
    MQTT_BENCHMARK_ACK_TOPIC
  );
}


// ==================================================
// Local Button Check
// ==================================================

void checkButtons() {

  unsigned long now =
    millis();

  int onState =
    digitalRead(
      BUTTON_ON_PIN
    );

  int offState =
    digitalRead(
      BUTTON_OFF_PIN
    );

  if (
    onState == LOW &&
    now - lastButtonOnMs >
    DEBOUNCE_MS
  ) {

    lastButtonOnMs =
      now;

    Serial.println(
      "[BUTTON] ON button pressed"
    );

    pressServo(
      PRESS_ON_ANGLE,
      "local_button_on"
    );
  }

  if (
    offState == LOW &&
    now - lastButtonOffMs >
    DEBOUNCE_MS
  ) {

    lastButtonOffMs =
      now;

    Serial.println(
      "[BUTTON] OFF button pressed"
    );

    pressServo(
      PRESS_OFF_ANGLE,
      "local_button_off"
    );
  }
}


// ==================================================
// Setup
// ==================================================

void setup() {

  Serial.begin(
    115200
  );

  delay(1000);

  Serial.println();

  Serial.println(
    "================================"
  );

  Serial.println(
    "ESP32 Light Switch Node Start"
  );

  Serial.println(
    "HTTP + MQTT Benchmark"
  );

  Serial.println(
    "================================"
  );

  pinMode(
    BUTTON_ON_PIN,
    INPUT_PULLUP
  );

  pinMode(
    BUTTON_OFF_PIN,
    INPUT_PULLUP
  );

  attachServoIfNeeded();

  servo.write(
    REST_ANGLE
  );

  delay(1000);

  connectWiFi();


  // --------------------
  // HTTP
  // --------------------

  server.on(
    "/",
    HTTP_GET,
    handleRoot
  );

  server.on(
    "/api/ping",
    HTTP_GET,
    handlePing
  );

  server.on(
    "/api/benchmark",
    HTTP_GET,
    handleBenchmark
  );

  server.on(
    "/api/status",
    HTTP_GET,
    handleStatus
  );

  server.on(
    "/api/light/on",
    HTTP_GET,
    handleLightOn
  );

  server.on(
    "/api/light/off",
    HTTP_GET,
    handleLightOff
  );

  server.on(
    "/api/servo/rest",
    HTTP_GET,
    handleServoReset
  );

  server.begin();

  Serial.println();

  Serial.println(
    "[HTTP] Server started"
  );

  Serial.println(
    "[HTTP] Available endpoints:"
  );

  Serial.println(
    "  GET /"
  );

  Serial.println(
    "  GET /api/ping"
  );

  Serial.println(
    "  GET /api/benchmark?id=1"
  );

  Serial.println(
    "  GET /api/status"
  );

  Serial.println(
    "  GET /api/light/on"
  );

  Serial.println(
    "  GET /api/light/off"
  );

  Serial.println(
    "  GET /api/servo/rest"
  );


  // --------------------
  // MQTT
  // --------------------

  mqttClient.begin(
    MQTT_BROKER,
    MQTT_PORT,
    mqttNetwork
  );

  mqttClient.onMessage(
    mqttMessageReceived
  );

  // 실패해도 HTTP 기능은 계속 동작함.
  tryConnectMQTT();


  // --------------------
  // System Info
  // --------------------

  Serial.println();

  Serial.println(
    "[PIN] Servo: GPIO18"
  );

  Serial.println(
    "[PIN] ON button: GPIO21 -> GND"
  );

  Serial.println(
    "[PIN] OFF button: GPIO22 -> GND"
  );

  Serial.println();

  Serial.println(
    "[ANGLE] REST: 90"
  );

  Serial.println(
    "[ANGLE] ON: 50"
  );

  Serial.println(
    "[ANGLE] OFF: 140"
  );

  Serial.println();
}


// ==================================================
// Loop
// ==================================================

void loop() {

  // 기존 HTTP Server
  server.handleClient();

  // Local Button
  checkButtons();

  // MQTT Network Processing
  mqttClient.loop();

  // MQTT Callback에서 준비한
  // Application ACK를 여기서 Publish
  publishPendingMqttAck();

  // Broker가 끊어진 경우
  // 일정 간격으로 재접속
  if (
    !mqttClient.connected()
  ) {

    unsigned long now =
      millis();

    if (
      now -
      lastMqttReconnectAttemptMs >=
      MQTT_RECONNECT_INTERVAL_MS
    ) {

      lastMqttReconnectAttemptMs =
        now;

      tryConnectMQTT();
    }
  }

  delay(2);
}