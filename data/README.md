# Experiment Data

**한국어** | [English](README_EN.md)

이 디렉터리는 **Edge IoT Control System**의 실험 과정에서 생성한 Raw Data, Processed Data, Figure를 정리합니다.

최종 분석에 사용한 데이터뿐 아니라 Dry Run, 원인 확인을 위한 Diagnostic Data, 실험 조건 문제로 제외한 데이터, 프로젝트 초기의 Legacy Data도 구분하여 보존했습니다.

Raw CSV를 분석의 **Source of Truth**로 사용하며, Processed Data와 Figure는 분석 Script를 통해 다시 생성할 수 있도록 구성했습니다.

---

## 디렉터리 구조

```text
data/
├── raw/
│   ├── main/
│   │   ├── http/
│   │   ├── mqtt_qos0/
│   │   ├── mqtt_qos1/
│   │   ├── resource/
│   │   └── end_to_end/
│   │
│   ├── diagnostic/
│   │   ├── dryrun/
│   │   ├── wifi_sleep/
│   │   └── resource/
│   │
│   ├── excluded/
│   │   ├── keepalive/
│   │   └── uncertain_condition/
│   │
│   └── legacy/
│       └── http_latency/
│
├── processed/
│   ├── diagnostic/
│   └── *.csv
│
└── figures/
```

---

## Data 분류 기준

### `raw/main/`

최종 결과와 그래프에 사용한 **본실험 Raw Data**입니다.

### `raw/diagnostic/`

본실험 전후에 기능 확인, 원인 추적, 실험 조건 검증을 위해 수행한 데이터입니다.

최종 Protocol Benchmark 통계에는 포함하지 않습니다.

### `raw/excluded/`

측정 자체는 수행했지만 실험 조건이 유효하지 않거나 조건을 확실히 검증할 수 없어 **최종 분석에서 제외한 데이터**입니다.

제외한 데이터를 삭제하지 않고 이유와 함께 보존했습니다.

### `raw/legacy/`

프로젝트 초기 단계에서 수집한 Historical Data입니다.

Firmware, Endpoint, Network Condition, Benchmark 방식 등이 최종 실험과 다를 수 있으므로 직접적인 성능 비교에는 사용하지 않습니다.

### `processed/`

Raw Data에서 계산한 Summary 및 분석용 CSV입니다.

### `figures/`

Raw / Processed Data에서 생성한 최종 그래프입니다.

---

# 1. Main Protocol Benchmark

최종 Protocol Benchmark는 다음 세 조건을 비교했습니다.

```text
HTTP
MQTT QoS 0
MQTT QoS 1
```

최종 Raw Data 위치:

```text
raw/main/http/
raw/main/mqtt_qos0/
raw/main/mqtt_qos1/
```

대표 Raw File:

```text
http_main_1000_nosleep_20260904_102455.csv
mqtt_qos0_main_1000_nosleep_20260904_102455.csv
mqtt_qos1_main_1000_nosleep_20260904_102455.csv
```

---

## 실험 조건

```text
ESP32 Wi-Fi Sleep : OFF

Warm-up            : Protocol당 50회
Main Measurement   : 200회 × 5 Runs
Samples/Protocol   : 1000
Total Samples      : 3000

Request Interval   : 0.2 s
Execution          : Sequential
```

Protocol 순서가 항상 동일하지 않도록 Run별 순서를 교차했습니다.

```text
Run 1: HTTP       → MQTT QoS 0 → MQTT QoS 1
Run 2: MQTT QoS 0 → MQTT QoS 1 → HTTP
Run 3: MQTT QoS 1 → HTTP       → MQTT QoS 0
Run 4: HTTP       → MQTT QoS 1 → MQTT QoS 0
Run 5: MQTT QoS 1 → MQTT QoS 0 → HTTP
```

각 Run은 Protocol당 200 Samples이며, 총:

```text
HTTP       : 1000
MQTT QoS 0 : 1000
MQTT QoS 1 : 1000

Total      : 3000
```

입니다.

모든 최종 요청이 성공했습니다.

```text
3000 / 3000 successful
```

---

## Application RTT 결과

| Protocol | Mean | Median | Std Dev | P95 | P99 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| HTTP | 20.515 ms | 19.450 ms | 4.377 ms | 28.807 ms | 37.038 ms | 13.100 ms | 47.467 ms |
| MQTT QoS 0 | 15.319 ms | 13.988 ms | 4.820 ms | 22.980 ms | 31.076 ms | 8.297 ms | 62.187 ms |
| MQTT QoS 1 | 61.282 ms | 59.508 ms | 8.360 ms | 79.849 ms | 94.444 ms | 12.318 ms | 105.922 ms |

여기서 측정한 RTT는 **Application-level Round-Trip Time**입니다.

HTTP의 경우 Raspberry Pi에서 Request를 시작한 시점부터 HTTP Response Body를 읽은 시점까지를 측정했습니다.

MQTT의 경우 Raspberry Pi가 Benchmark Command를 Publish하기 직전부터 해당 Command ID에 대응하는 ESP32 Application ACK를 수신할 때까지를 측정했습니다.

따라서 이 값을 **순수 Network Propagation Latency로 해석하지 않습니다.**

---

## Run별 평균

각 Run의 평균 RTT도 따로 확인했습니다.

### HTTP

```text
Run 1 : 20.982 ms
Run 2 : 19.661 ms
Run 3 : 21.506 ms
Run 4 : 20.240 ms
Run 5 : 20.184 ms
```

### MQTT QoS 0

```text
Run 1 : 15.592 ms
Run 2 : 14.932 ms
Run 3 : 15.286 ms
Run 4 : 15.449 ms
Run 5 : 15.338 ms
```

### MQTT QoS 1

```text
Run 1 : 61.108 ms
Run 2 : 61.111 ms
Run 3 : 61.717 ms
Run 4 : 61.565 ms
Run 5 : 60.910 ms
```

Run 순서를 교차했음에도 각 Protocol의 Run 평균은 비슷한 수준으로 유지됐습니다.

---

# 2. ESP32 Handler Processing

Protocol Benchmark에서는 전체 Application RTT와 별도로 ESP32 Benchmark Handler 내부 처리시간을 측정했습니다.

측정에는 ESP32 내부 `micros()` Clock을 사용했습니다.

| Protocol | Mean | Median | P95 | Max |
|---|---:|---:|---:|---:|
| HTTP | 401.999 µs | 390 µs | 472.05 µs | 1027 µs |
| MQTT QoS 0 | 419.632 µs | 411 µs | 461 µs | 664 µs |
| MQTT QoS 1 | 420.765 µs | 411 µs | 465.05 µs | 652 µs |

세 Protocol 모두 평균 약 **0.4 ms** 수준이었습니다.

분석에서는 다음 값을 추가로 계산했습니다.

```text
Host / Network / Protocol Remainder
=
Application RTT
-
Measured ESP32 Handler Processing
```

평균:

| Protocol | Mean Remainder |
|---|---:|
| HTTP | 20.113 ms |
| MQTT QoS 0 | 14.900 ms |
| MQTT QoS 1 | 60.862 ms |

이 Remainder에는 다음 요소가 함께 포함될 수 있습니다.

- Raspberry Pi Host Processing
- Wi-Fi Communication
- TCP / MQTT Protocol Handling
- Mosquitto Broker Handling
- Response Generation / Reception
- Runtime Scheduling

따라서 **순수 Network Latency를 의미하지 않습니다.**

---

## Clock 해석 주의사항

Raspberry Pi와 ESP32는 동일한 Clock을 공유하지 않습니다.

따라서 서로 다른 장치에서 기록한 Absolute Timestamp를 직접 빼서 구간 Latency를 계산하지 않았습니다.

대신:

```text
Raspberry Pi 내부 시간 구간
→ Raspberry Pi Clock 사용

ESP32 내부 처리 구간
→ ESP32 Clock 사용
```

으로 각각 독립적으로 측정했습니다.

---

# 3. ESP32 Heap Data

Protocol Benchmark의 각 Request에서 다음 값을 기록했습니다.

```text
free_heap
min_free_heap
max_alloc_heap
rssi_dbm
```

Protocol별 CSV를 단순 연결한 순서가 아니라, 전체 3000 Samples를 Timestamp 기준으로 다시 정렬하여 실제 실험 순서에 따른 Free Heap 변화를 확인했습니다.

최종 Figure:

```text
figures/free_heap_chronological.png
```

실험 중 Free Heap은 여러 Runtime Level 사이에서 변동했지만, 전체 3000회 요청에서 지속적인 하락 추세는 관찰되지 않았습니다.

따라서 결과는 다음 범위로 제한하여 해석합니다.

> 본 Benchmark 범위에서는 반복 요청에 따른 누적적인 Free Heap 감소 현상이 관찰되지 않았습니다.

이는 모든 Runtime Condition에서 Memory Leak이 존재하지 않음을 증명하는 결과는 아닙니다.

또한:

```cpp
ESP.getMinFreeHeap()
```

은 Protocol별 순간 메모리 사용량이 아니라 **ESP32 Boot 이후 관찰된 최소 Free Heap**입니다.

따라서 이 값을 이용해 Protocol별 Memory Footprint를 직접 비교하지 않습니다.

---

# 4. Raspberry Pi Resource Benchmark

최종 Raw Data:

```text
raw/main/resource/pi_resource_samples_20260906_002151.csv
```

최종 Processed Summary:

```text
processed/pi_resource_summary_20260906_002151.csv
```

실험 조건:

```text
200 Requests × 3 Runs / Protocol

Request Interval         : 0.2 s
Resource Sampling        : 0.2 s
Execution                : Sequential
```

Run 순서:

```text
Run 1: HTTP       → MQTT QoS 0 → MQTT QoS 1
Run 2: MQTT QoS 0 → MQTT QoS 1 → HTTP
Run 3: MQTT QoS 1 → HTTP       → MQTT QoS 0
```

측정 항목:

- Python Worker CPU
- Python Worker RSS
- Mosquitto CPU
- Mosquitto RSS
- Raspberry Pi System CPU

최종 평균:

| Protocol | Worker CPU | Worker RSS | Mosquitto CPU | Mosquitto RSS |
|---|---:|---:|---:|---:|
| HTTP | 0.429% | 23.165 MiB | 0.008% | 8.406 MiB |
| MQTT QoS 0 | 0.397% | 23.371 MiB | 0.037% | 8.406 MiB |
| MQTT QoS 1 | 0.403% | 23.389 MiB | 0.043% | 8.406 MiB |

이 CPU 값은 0.2초 Request Interval을 포함한 전체 Workload에서 계산한 평균입니다.

따라서:

```text
요청 하나를 처리하는 데 사용한 CPU %
```

로 해석하지 않습니다.

---

# 5. Light Switch End-to-End Data

최종 Raw Data:

```text
raw/main/end_to_end/light_http_e2e_20_20260906_010354.csv
```

Processed Summary:

```text
processed/light_e2e_summary.csv
```

실제 Light ON/OFF Endpoint를 대상으로:

```text
ON   : 10
OFF  : 10
Total: 20
```

회 측정했습니다.

CSV의 `success`는 **HTTP API Response 성공 여부**입니다.

별도로 수행한 Physical Actuation Reliability Test의 `40 / 40` 성공 결과와는 다른 측정입니다.

---

## E2E 결과

| Metric | Value |
|---|---:|
| ON Mean | 1032.498 ms |
| OFF Mean | 1031.995 ms |
| Overall Mean | 1032.247 ms |
| Overall Median | 1031.450 ms |
| Min | 1028.087 ms |
| Max | 1040.075 ms |

Light Switch의 Programmed Servo Timing:

```text
Press Hold  : 400 ms
Return Wait : 600 ms

Total Programmed Delay
= 1000 ms
```

평균 E2E:

```text
Measured Mean
= 1032.247 ms

Programmed Actuator Delay
= 1000 ms
≈ 96.9%

Non-programmed Remainder
≈ 32.247 ms
≈ 3.1%
```

따라서 본 실험에서는 실제 사용자 체감 Light Control Latency의 대부분이 **의도적으로 설정한 Servo Timing**에서 발생했습니다.

Non-programmed Remainder에는:

- Raspberry Pi Request Handling
- Wi-Fi / TCP / HTTP
- ESP32 Handler
- Servo Command Execution
- Response Handling
- Runtime Scheduling

등이 함께 포함될 수 있으므로 순수 Network Latency로 해석하지 않습니다.

---

# 6. Wi-Fi Sleep Diagnostic

위치:

```text
raw/diagnostic/wifi_sleep/
```

초기 MQTT Benchmark에서 약 100 ms 이상의 RTT가 반복적으로 관찰되어 ESP32 Wi-Fi Power Saving 설정의 영향을 별도로 확인했습니다.

### Confirmed Sleep ON

```text
MQTT QoS 0

Success : 30 / 30
Mean    : 121.279 ms
Min     : 16.126 ms
Max     : 334.085 ms
```

### Confirmed Sleep OFF

```text
MQTT QoS 0

Success : 30 / 30
Mean    : 15.886 ms
Min     : 8.794 ms
Max     : 56.288 ms
```

최종 Firmware에서는:

```cpp
WiFi.setSleep(false);
```

를 사용했고, 모든 Main Protocol Benchmark도:

```text
Wi-Fi Sleep = OFF
```

조건에서 수행했습니다.

이 Diagnostic은 Wi-Fi Power Saving 설정이 본 시스템의 Latency에 큰 영향을 줄 수 있음을 확인하기 위한 A/B Test로 사용했습니다.

---

# 7. Resource Diagnostic

위치:

```text
raw/diagnostic/resource/
```

초기 Raspberry Pi Resource Benchmark에서 사용한 Worker Process는 HTTP와 MQTT 관련 Python Module을 모두 Import한 상태였습니다.

이 경우 Protocol별 Python Worker RSS를 비교할 때 각 Protocol의 Runtime 조건을 충분히 분리하기 어려웠습니다.

따라서 해당 측정은 Diagnostic Data로 이동했습니다.

이후 Worker를 수정하여:

```text
HTTP Condition
→ HTTP 관련 Module만 Import

MQTT Condition
→ MQTT 관련 Module만 Import
```

하도록 한 뒤 Resource Benchmark를 다시 수행했습니다.

최종 분석에는 수정 이후의 `raw/main/resource/` Data만 사용합니다.

---

# 8. Excluded Data

## HTTP Keep-Alive

위치:

```text
raw/excluded/keepalive/
```

HTTP Persistent Connection을 비교하기 위해 Keep-Alive 실험을 시도했습니다.

그러나 실제 Response에서:

```text
Connection: close
```

가 확인됐고, Client Log에서도 dropped connection을 다시 생성하는 동작이 관찰됐습니다.

따라서 측정된 조건은 실제 Persistent HTTP Connection이라고 보기 어렵다고 판단했습니다.

최종 Protocol Benchmark에서 제외한 이유는 **결과값이 좋거나 나빴기 때문이 아니라 실험 조건 자체가 성립하지 않았기 때문**입니다.

---

## Uncertain Wi-Fi Condition

위치:

```text
raw/excluded/uncertain_condition/
```

한 MQTT QoS 0 Run은:

```cpp
WiFi.setSleep(false);
```

가 포함된 Firmware가 실제 ESP32에 Upload된 상태인지 확실하게 확인할 수 없는 조건에서 실행됐습니다.

실험 조건을 검증할 수 없었으므로 최종 분석에서 제외했습니다.

---

# 9. Legacy Data

위치:

```text
raw/legacy/
```

프로젝트 초기 단계에서 측정한 데이터입니다.

예를 들어 초기 HTTP Latency Test는 이전 ESP32 Endpoint와 Network Condition에서 수행됐습니다.

초기 HTTP 측정 결과:

```text
Requests : 100
Success  : 100 / 100

Mean     : 114.017 ms
Median   : 114.560 ms
Min      : 82.420 ms
Max      : 126.070 ms
```

이 값은 개발 초기의 Historical Baseline으로만 보존합니다.

최종 HTTP Benchmark와는 Firmware, Endpoint, Wi-Fi 설정 및 측정 조건이 다르므로 직접적인 성능 비교에는 사용하지 않습니다.

---

# 10. Processed Data

주요 Processed File:

```text
protocol_summary.csv
protocol_per_run_summary.csv
protocol_samples_combined.csv

pi_resource_summary_20260906_002151.csv

light_e2e_summary.csv
```

Raw CSV에서 통계 및 그래프 생성에 필요한 형태로 가공한 결과입니다.

Raw Data가 분석의 Source of Truth이며 Processed Data는 Script를 이용해 다시 생성할 수 있습니다.

---

# 11. Figures

최종 Figure:

```text
latency_boxplot.png
latency_percentiles.png
latency_sequence.png
per_run_mean_latency.png

esp_processing_mean.png
latency_breakdown.png
free_heap_chronological.png

pi_resource_cpu.png
pi_resource_rss.png

light_e2e_on_off.png
light_e2e_breakdown.png
```

각 Figure의 목적:

```text
latency_boxplot.png
→ Protocol RTT Distribution 비교

latency_percentiles.png
→ Median / P95 / P99 비교

latency_sequence.png
→ Protocol별 Sample Sequence에 따른 RTT 변화

per_run_mean_latency.png
→ 5개 Run의 평균 RTT 재현성 확인

esp_processing_mean.png
→ ESP32 Handler 내부 Processing 비교

latency_breakdown.png
→ Application RTT와 ESP32 Processing / Remainder 비교

free_heap_chronological.png
→ 실제 Timestamp 순서의 ESP32 Free Heap 변화

pi_resource_cpu.png
→ Python Worker / Mosquitto CPU 비교

pi_resource_rss.png
→ Python Worker / Mosquitto RSS 비교

light_e2e_on_off.png
→ Light ON / OFF E2E 분포 비교

light_e2e_breakdown.png
→ Programmed Actuator Delay와 나머지 E2E 구간 비교
```

주의:

`latency_sequence.png`의 X축은 **Protocol별로 정리한 Sample Sequence**입니다.

전체 3000 Samples의 실제 Global Chronological Order를 나타내는 그래프는 아닙니다.

ESP32 Heap의 실제 시간 흐름은:

```text
free_heap_chronological.png
```

을 사용합니다.

---

# 12. 분석 Script

분석 및 Figure 생성 Script:

```text
analysis/analyze_protocol_benchmark.py
analysis/plot_protocol_benchmark.py
analysis/plot_bottleneck_heap.py
analysis/plot_pi_resources.py
analysis/plot_light_e2e.py
```

Protocol 분석:

```bash
python analysis/analyze_protocol_benchmark.py
```

Protocol Figure:

```bash
python analysis/plot_protocol_benchmark.py
```

Bottleneck / Heap:

```bash
python analysis/plot_bottleneck_heap.py
```

Raspberry Pi Resource:

```bash
python analysis/plot_pi_resources.py
```

Light E2E:

```bash
python analysis/plot_light_e2e.py
```

---

# 13. Data 해석 원칙

이 프로젝트에서는 측정 결과를 가능한 범위 안에서만 해석하는 것을 원칙으로 했습니다.

예를 들어:

- MQTT QoS 0가 본 실험에서 가장 낮은 RTT를 보였다고 해서 모든 환경에서 HTTP보다 빠르다고 일반화하지 않습니다.
- MQTT QoS 1의 RTT가 높았지만, 내부 세부 단계까지 측정하지 않았으므로 특정 한 단계가 원인이라고 단정하지 않습니다.
- `Application RTT - ESP32 Processing`을 순수 Network Latency라고 부르지 않습니다.
- Free Heap이 지속적으로 감소하지 않았다고 해서 Memory Leak이 절대 없다고 결론내리지 않습니다.
- 3000 / 3000 Request가 성공했다고 해서 Packet Loss 환경에서 QoS별 Reliability 차이를 검증했다고 보지 않습니다.
- Light E2E의 `success`와 별도의 Physical Actuation Reliability Test 결과를 구분합니다.

최종 결과뿐 아니라 **어떤 조건에서 측정했고, 어떤 데이터는 왜 제외했는지 함께 기록하는 것**을 이 디렉터리의 주요 목적 중 하나로 두었습니다.
