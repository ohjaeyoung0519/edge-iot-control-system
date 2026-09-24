> **Historical planning document**  
> 이 문서는 프로젝트 초기에 작성한 계획을 보존한 기록입니다. IR / Camera / Vision 관련 항목은 당시 검토한 확장 아이디어이며 **최종 구현 범위가 아닙니다.** 최종 구현 및 분석 범위는 Light Switch Node와 PC Power Node이며, 현재 상태는 루트 `README.md`와 `data/README.md`를 기준으로 합니다.

# Project Plan

## Project Title (current name)

Edge IoT Control System

## Objective

The objective of this project is to build an edge IoT control system using a Raspberry Pi 5 and ESP32 boards.

The system is designed to support remote control, local hardware control, servo-based physical switching, sensor-based state checking, and future IR/camera-based device state recognition.

This project is not only focused on implementing basic IoT control, but also on measuring and analyzing communication latency, ESP32 memory usage, servo motor stability, external power behavior, and hardware reliability in an embedded edge system.

## System Concept

The Raspberry Pi 5 acts as a central edge control server.

ESP32 boards operate as wireless hardware control nodes. Each ESP32 node can be assigned to a specific physical control target, such as a light switch, PC power button, or IR-based device control.

The system follows this general control flow:

```text
Phone / Web Browser / MacBook
        |
        v
Raspberry Pi 5 Edge Control Server
        |
   Wi-Fi / HTTP
        |
        v
ESP32 Hardware Control Node
        |
        |-- Servo Motor
        |-- LDR Sensor
        |-- Local Button
        |-- IR Transmitter / Receiver
```

## Development Phases

### Phase 1: Raspberry Pi and ESP32 Basic Setup

- Raspberry Pi OS setup
- Raspberry Pi Wi-Fi and SSH setup
- Raspberry Pi package update
- Raspberry Pi temperature and throttling check
- GitHub repository setup
- Flask test server implementation
- ESP32 development environment setup
- ESP32 board information test
- ESP32 Wi-Fi connection test
- ESP32 HTTP server test

### Phase 2: Raspberry Pi to ESP32 Communication

- Raspberry Pi Flask server implementation
- ESP32 HTTP server implementation
- Raspberry Pi to ESP32 HTTP request test
- ESP32 `/api/ping` endpoint test
- Raspberry Pi forwarding endpoint test
- Repeated latency measurement between Raspberry Pi and ESP32
- Raw and processed latency data organization

### Phase 3: Hardware Control and Sensor Test

- Servo motor control test using ESP32 GPIO
- SG90 servo motor test
- MG90S servo motor test
- External 5V power supply test
- Common GND wiring verification
- LDR analog sensor test using ESP32 ADC
- LDR raw value measurement
- Servo motor repeated actuation test
- Servo motor temperature measurement
- ESP32 free heap monitoring during repeated control

### Phase 4: Integrated Control Node

- Combine Wi-Fi communication, HTTP server, servo control, and LDR sensing into one ESP32 program
- Implement ESP32 control endpoints
  - `/api/ping`
  - `/api/servo/press`
  - `/api/ldr`
  - `/api/status`
- Implement Raspberry Pi API routes for ESP32 control
- Test remote servo control through Raspberry Pi
- Measure end-to-end command latency
- Verify stable operation under repeated requests

### Phase 5: PC Power State Verification

- Attach LDR sensor near PC power LED
- Measure PC OFF and ON raw light values
- Design threshold-based PC LED state detection
- Combine ping test and LDR value for PC power state judgment
- Implement conditional PC power control logic
- Prevent unnecessary power button actuation when the PC is already on

### Phase 6: Local Button Input

- Connect local tact switch to ESP32
- Implement local button input using GPIO pull-up
- Add software debounce logic
- Verify that local input and remote input can coexist
- Compare local control path and remote control path

### Phase 7: IR and Camera Extension

- Test IR receiver module
- Capture IR signal from existing remote controller
- Test IR LED transmission circuit using 2N2222A transistor
- Send stored IR command using ESP32
- Analyze limitation of one-way IR control
- Add Raspberry Pi camera as a future state verification method
- Explore camera-based device status recognition

## Success Criteria

### Basic System Criteria

- Raspberry Pi 5 operates as a local edge server.
- ESP32 connects to the same Wi-Fi network.
- ESP32 receives HTTP requests from Raspberry Pi.
- Raspberry Pi can forward control requests to ESP32.
- ESP32 returns status information such as free heap and RSSI.

### Measurement Criteria

- Raspberry Pi to ESP32 communication latency is measured and recorded.
- Repeated request success rate is recorded.
- ESP32 free heap is monitored during operation.
- Raw and processed data files are stored separately.
- Experiment photos and Serial Monitor screenshots are documented.

### Hardware Control Criteria

- ESP32 can control a servo motor using PWM.
- Servo motor is powered by an external 5V supply.
- ESP32 GND and external power GND are connected as common ground.
- Servo motor repeated operation is tested.
- Servo motor surface temperature is measured before and after repeated operation.
- No overheating or ESP32 reset occurs during the basic stability test.

### Sensor Criteria

- LDR analog values are measured using ESP32 ADC.
- LDR raw values change according to brightness.
- Threshold-based state detection can be designed from measured raw values.
- PC power LED state detection is tested in a later phase.

### Extension Criteria

- Local button input and remote command input can coexist.
- IR signal reception and transmission are tested.
- Camera-based state verification is explored as an extension.

## Completed Experiments

### Raspberry Pi Server Test

A Flask-based test server was implemented on the Raspberry Pi 5.

The server was accessed from a MacBook browser through the Raspberry Pi local IP address and port `5000`.

This confirmed the initial communication path:

```text
MacBook Browser -> Local Wi-Fi Network -> Raspberry Pi Flask Server
```

### ESP32 Wi-Fi and HTTP Server Test

ESP32 was connected to Wi-Fi and configured as a simple HTTP server.

The ESP32 successfully responded to browser and Raspberry Pi requests through its local IP address.

### Raspberry Pi to ESP32 Latency Test

Raspberry Pi sent 100 repeated HTTP requests to the ESP32 `/api/ping` endpoint.

Measured summary:

- Total requests: 100
- Successful requests: 100
- Failed requests: 0
- Success rate: 100%
- Minimum latency: 82.42 ms
- Maximum latency: 126.07 ms
- Average latency: 114.017 ms
- Median latency: 114.56 ms

Raw and processed data are stored in:

```text
data/raw/legacy/http_latency/esp32_latency_rpi_to_esp32_100.csv
data/processed/esp32_latency_rpi_to_esp32_summary.csv
```

### Servo and LDR Measurement Test

MG90S servo motor and LDR sensor were tested using ESP32.

The MG90S servo motor was powered by an external 5V power supply, and ESP32 GND was connected to the external power GND as common ground.

The LDR sensor was connected to ESP32 3.3V, GND, and GPIO34 ADC input.

A 10-minute repeated servo actuation test was performed.

Measured summary:

- Test duration: 10 minutes
- Total servo actuation trials: 172
- Servo pin: GPIO18
- LDR analog pin: GPIO34
- Initial free heap: 330252 bytes
- Final free heap: 329648 bytes
- Heap difference during each trial: 0 bytes
- Temperature before test: 26.5°C
- Temperature after 5 minutes: 27.6°C
- Temperature after 10 minutes: 27.8°C
- Temperature increase after 10 minutes: +1.3°C

No ESP32 reset, servo failure, or overheating was observed during the test.

Raw and processed data are stored in:

```text
data/raw/servo_ldr_measurement_10min_raw_log.txt
data/processed/servo_ldr_measurement_10min_clean.csv
data/processed/servo_ldr_measurement_summary.csv
data/processed/mg90s_temperature_summary.csv
```

## Current Limitations

- The current servo test was performed without a real physical switch load.
- LDR sensor was tested under general lighting conditions, but PC power LED threshold testing is not complete yet.
- Local button input has not yet been integrated with the final ESP32 node code.
- IR control and camera-based state recognition are planned as extensions.
- Current ESP32 test sketches are separated by function and need to be integrated into a single node program.

## Next Steps

1. Implement integrated ESP32 control node code.
2. Combine Wi-Fi, HTTP server, servo control, and LDR sensing.
3. Add ESP32 endpoints for servo and sensor control.
4. Connect Raspberry Pi Flask server to the integrated ESP32 node.
5. Test remote servo actuation through Raspberry Pi.
6. Measure end-to-end remote control latency.
7. Mount LDR sensor near the PC power LED.
8. Measure PC ON/OFF raw values and define threshold.
9. Add local tact switch input.
10. Prepare IR control and camera extension after the main control path is stable.