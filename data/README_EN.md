# Experiment Data

[한국어](README.md) | **English**

This directory contains the Raw Data, Processed Data, and Figures generated during the experiments for the **Edge IoT Control System**.

In addition to the datasets used for the final analysis, Dry Runs, Diagnostic Data used for investigating causes, datasets excluded because of experimental-condition issues, and early Legacy Data are also preserved separately.

Raw CSV files are treated as the **Source of Truth**, and Processed Data and Figures are organized so that they can be regenerated using the analysis scripts.

---

## Directory Structure

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

## Data Classification

### `raw/main/`

Contains the **final raw datasets** used for the final results and figures.

### `raw/diagnostic/`

Contains measurements collected before or after the main experiments for functionality checks, cause investigation, and experimental-condition verification.

These datasets are not included in the final Protocol Benchmark statistics.

### `raw/excluded/`

Contains measurements that were collected but **excluded from the final analysis** because the experimental condition was invalid or could not be verified with sufficient confidence.

Excluded datasets are preserved together with the reason for exclusion instead of being deleted.

### `raw/legacy/`

Contains Historical Data collected during the early stages of the project.

Firmware, endpoints, network conditions, or benchmark methods may differ from the final experiments, so these datasets are not used for direct performance comparison.

### `processed/`

Contains summary and analysis CSV files generated from Raw Data.

### `figures/`

Contains the final figures generated from Raw or Processed Data.

---

# 1. Main Protocol Benchmark

The final Protocol Benchmark compared the following three conditions:

```text
HTTP
MQTT QoS 0
MQTT QoS 1
```

Final Raw Data locations:

```text
raw/main/http/
raw/main/mqtt_qos0/
raw/main/mqtt_qos1/
```

Representative Raw Files:

```text
http_main_1000_nosleep_20260904_102455.csv
mqtt_qos0_main_1000_nosleep_20260904_102455.csv
mqtt_qos1_main_1000_nosleep_20260904_102455.csv
```

---

## Experimental Conditions

```text
ESP32 Wi-Fi Sleep : OFF

Warm-up            : 50 requests per protocol
Main Measurement   : 200 requests × 5 runs
Samples/Protocol   : 1000
Total Samples      : 3000

Request Interval   : 0.2 s
Execution          : Sequential
```

The protocol order was rotated across runs so that the protocols were not always measured in the same order.

```text
Run 1: HTTP       → MQTT QoS 0 → MQTT QoS 1
Run 2: MQTT QoS 0 → MQTT QoS 1 → HTTP
Run 3: MQTT QoS 1 → HTTP       → MQTT QoS 0
Run 4: HTTP       → MQTT QoS 1 → MQTT QoS 0
Run 5: MQTT QoS 1 → MQTT QoS 0 → HTTP
```

Each run contained 200 samples per protocol, giving:

```text
HTTP       : 1000
MQTT QoS 0 : 1000
MQTT QoS 1 : 1000

Total      : 3000
```

All final requests completed successfully.

```text
3000 / 3000 successful
```

---

## Application RTT Results

| Protocol | Mean | Median | Std Dev | P95 | P99 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| HTTP | 20.515 ms | 19.450 ms | 4.377 ms | 28.807 ms | 37.038 ms | 13.100 ms | 47.467 ms |
| MQTT QoS 0 | 15.319 ms | 13.988 ms | 4.820 ms | 22.980 ms | 31.076 ms | 8.297 ms | 62.187 ms |
| MQTT QoS 1 | 61.282 ms | 59.508 ms | 8.360 ms | 79.849 ms | 94.444 ms | 12.318 ms | 105.922 ms |

The RTT measured here is **Application-level Round-Trip Time**.

For HTTP, timing starts when the Raspberry Pi begins the request and ends after the HTTP response body has been read.

For MQTT, timing starts immediately before the Raspberry Pi publishes the benchmark command and ends when the corresponding ESP32 application-level ACK with the matching command ID is received.

Therefore, these values are **not interpreted as pure network propagation latency**.

---

## Mean RTT per Run

The mean RTT of each individual run was also checked.

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

Even with the protocol order rotated across runs, the mean RTT for each protocol remained at a similar level across the five runs.

---

# 2. ESP32 Handler Processing

In addition to the complete Application RTT, the Protocol Benchmark separately measured the processing time inside the ESP32 benchmark handler.

The ESP32 internal `micros()` clock was used for this measurement.

| Protocol | Mean | Median | P95 | Max |
|---|---:|---:|---:|---:|
| HTTP | 401.999 µs | 390 µs | 472.05 µs | 1027 µs |
| MQTT QoS 0 | 419.632 µs | 411 µs | 461 µs | 664 µs |
| MQTT QoS 1 | 420.765 µs | 411 µs | 465.05 µs | 652 µs |

All three protocols showed an average processing time of approximately **0.4 ms**.

The following derived value was also calculated for analysis:

```text
Host / Network / Protocol Remainder
=
Application RTT
-
Measured ESP32 Handler Processing
```

Mean values:

| Protocol | Mean Remainder |
|---|---:|
| HTTP | 20.113 ms |
| MQTT QoS 0 | 14.900 ms |
| MQTT QoS 1 | 60.862 ms |

This remainder may include:

- Raspberry Pi Host Processing
- Wi-Fi Communication
- TCP / MQTT Protocol Handling
- Mosquitto Broker Handling
- Response Generation / Reception
- Runtime Scheduling

Therefore, it **does not represent pure Network Latency**.

---

## Clock Interpretation

The Raspberry Pi and ESP32 do not share the same clock.

Therefore, absolute timestamps recorded on different devices were not directly subtracted to calculate segment latency.

Instead:

```text
Raspberry Pi internal intervals
→ measured using the Raspberry Pi clock

ESP32 internal processing intervals
→ measured using the ESP32 clock
```

Each timing interval was measured independently using the clock of the device on which that interval occurred.

---

# 3. ESP32 Heap Data

The following values were recorded for each request during the Protocol Benchmark:

```text
free_heap
min_free_heap
max_alloc_heap
rssi_dbm
```

Rather than simply concatenating the protocol CSV files, all 3000 samples were sorted again by timestamp to examine Free Heap behavior in the actual experimental order.

Final Figure:

```text
figures/free_heap_chronological.png
```

Free Heap moved between several runtime levels during the experiment, but no continuous downward trend was observed across the full 3000-request benchmark.

Therefore, the result is interpreted only within the following scope:

> No cumulative decrease in Free Heap was observed during repeated requests within the scope of this benchmark.

This does not prove that memory leaks are impossible under every runtime condition.

Also:

```cpp
ESP.getMinFreeHeap()
```

represents the **minimum Free Heap observed since ESP32 boot**, not the instantaneous memory usage of each protocol.

Therefore, this value is not used to directly compare protocol-specific Memory Footprints.

---

# 4. Raspberry Pi Resource Benchmark

Final Raw Data:

```text
raw/main/resource/pi_resource_samples_20260906_002151.csv
```

Final Processed Summary:

```text
processed/pi_resource_summary_20260906_002151.csv
```

Experimental Conditions:

```text
200 Requests × 3 Runs / Protocol

Request Interval         : 0.2 s
Resource Sampling        : 0.2 s
Execution                : Sequential
```

Run order:

```text
Run 1: HTTP       → MQTT QoS 0 → MQTT QoS 1
Run 2: MQTT QoS 0 → MQTT QoS 1 → HTTP
Run 3: MQTT QoS 1 → HTTP       → MQTT QoS 0
```

Measured values:

- Python Worker CPU
- Python Worker RSS
- Mosquitto CPU
- Mosquitto RSS
- Raspberry Pi System CPU

Final averages:

| Protocol | Worker CPU | Worker RSS | Mosquitto CPU | Mosquitto RSS |
|---|---:|---:|---:|---:|
| HTTP | 0.429% | 23.165 MiB | 0.008% | 8.406 MiB |
| MQTT QoS 0 | 0.397% | 23.371 MiB | 0.037% | 8.406 MiB |
| MQTT QoS 1 | 0.403% | 23.389 MiB | 0.043% | 8.406 MiB |

These CPU values are averages calculated over the complete workload, including the 0.2-second Request Interval.

Therefore, they should not be interpreted as:

```text
CPU % required to process one individual request
```

---

# 5. Light Switch End-to-End Data

Final Raw Data:

```text
raw/main/end_to_end/light_http_e2e_20_20260906_010354.csv
```

Processed Summary:

```text
processed/light_e2e_summary.csv
```

The actual Light ON/OFF endpoint was measured:

```text
ON   : 10
OFF  : 10
Total: 20
```

times.

The `success` field in the CSV represents **successful HTTP API responses**.

This is different from the separate Physical Actuation Reliability Test result of `40 / 40`.

---

## E2E Results

| Metric | Value |
|---|---:|
| ON Mean | 1032.498 ms |
| OFF Mean | 1031.995 ms |
| Overall Mean | 1032.247 ms |
| Overall Median | 1031.450 ms |
| Min | 1028.087 ms |
| Max | 1040.075 ms |

Programmed Servo Timing for the Light Switch:

```text
Press Hold  : 400 ms
Return Wait : 600 ms

Total Programmed Delay
= 1000 ms
```

Mean E2E:

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

Therefore, in this experiment, most of the user-visible Light Control Latency came from the **intentionally programmed Servo Timing**.

The Non-programmed Remainder may include:

- Raspberry Pi Request Handling
- Wi-Fi / TCP / HTTP
- ESP32 Handler
- Servo Command Execution
- Response Handling
- Runtime Scheduling

so it is not interpreted as pure Network Latency.

---

# 6. Wi-Fi Sleep Diagnostic

Location:

```text
raw/diagnostic/wifi_sleep/
```

During early MQTT Benchmark measurements, RTT values around or above 100 ms were repeatedly observed.

A separate experiment was performed to investigate the effect of ESP32 Wi-Fi Power Saving.

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

The final firmware uses:

```cpp
WiFi.setSleep(false);
```

and all Main Protocol Benchmark measurements were performed under:

```text
Wi-Fi Sleep = OFF
```

This diagnostic was used as an A/B test to verify that the Wi-Fi Power Saving configuration could have a large effect on latency in this system.

---

# 7. Resource Diagnostic

Location:

```text
raw/diagnostic/resource/
```

The Worker Process used in the initial Raspberry Pi Resource Benchmark imported both HTTP-related and MQTT-related Python modules.

Under this condition, the runtime environment was not sufficiently separated for a clean comparison of protocol-specific Python Worker RSS.

Therefore, this measurement was moved to Diagnostic Data.

The Worker was later modified so that:

```text
HTTP Condition
→ import only HTTP-related modules

MQTT Condition
→ import only MQTT-related modules
```

and the Resource Benchmark was repeated.

Only the corrected data under `raw/main/resource/` is used for the final analysis.

---

# 8. Excluded Data

## HTTP Keep-Alive

Location:

```text
raw/excluded/keepalive/
```

A Keep-Alive experiment was attempted to compare an HTTP Persistent Connection condition.

However, the actual response included:

```text
Connection: close
```

and the client log also showed dropped connections being recreated.

Therefore, the measured condition could not be considered a true Persistent HTTP Connection.

The experiment was excluded from the final Protocol Benchmark **not because the result was good or bad, but because the intended experimental condition itself was not satisfied**.

---

## Uncertain Wi-Fi Condition

Location:

```text
raw/excluded/uncertain_condition/
```

One MQTT QoS 0 run was executed under a condition where it was not possible to confirm with certainty that firmware containing:

```cpp
WiFi.setSleep(false);
```

had actually been uploaded to the ESP32.

Because the experimental condition could not be verified, the dataset was excluded from the final analysis.

---

# 9. Legacy Data

Location:

```text
raw/legacy/
```

This directory contains data collected during the early stages of the project.

For example, the initial HTTP Latency Test was performed using an older ESP32 endpoint and different network conditions.

Initial HTTP measurement:

```text
Requests : 100
Success  : 100 / 100

Mean     : 114.017 ms
Median   : 114.560 ms
Min      : 82.420 ms
Max      : 126.070 ms
```

This dataset is preserved only as a Historical Baseline from the early development stage.

It is not used for direct performance comparison with the final HTTP Benchmark because the Firmware, Endpoint, Wi-Fi configuration, and measurement conditions are different.

---

# 10. Processed Data

Main Processed Files:

```text
protocol_summary.csv
protocol_per_run_summary.csv
protocol_samples_combined.csv

pi_resource_summary_20260906_002151.csv

light_e2e_summary.csv
```

These files contain statistics or analysis-ready data derived from Raw Data.

Raw Data remains the Source of Truth, and Processed Data can be regenerated using the analysis scripts.

---

# 11. Figures

Final Figures:

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

Purpose of each Figure:

```text
latency_boxplot.png
→ Compare Protocol RTT distributions

latency_percentiles.png
→ Compare Median / P95 / P99

latency_sequence.png
→ Show RTT changes across the sample sequence of each protocol

per_run_mean_latency.png
→ Check mean RTT consistency across the five runs

esp_processing_mean.png
→ Compare ESP32 Handler internal processing

latency_breakdown.png
→ Compare Application RTT with ESP32 Processing / Remainder

free_heap_chronological.png
→ Show ESP32 Free Heap behavior in actual timestamp order

pi_resource_cpu.png
→ Compare Python Worker / Mosquitto CPU

pi_resource_rss.png
→ Compare Python Worker / Mosquitto RSS

light_e2e_on_off.png
→ Compare Light ON / OFF E2E distributions

light_e2e_breakdown.png
→ Compare Programmed Actuator Delay with the remaining E2E interval
```

Note:

The X-axis of `latency_sequence.png` represents a **sample sequence organized separately for each protocol**.

It does not represent the actual global chronological order of all 3000 samples.

For the actual chronological behavior of ESP32 Heap, use:

```text
free_heap_chronological.png
```

---

# 12. Analysis Scripts

Analysis and Figure-generation scripts:

```text
analysis/analyze_protocol_benchmark.py
analysis/plot_protocol_benchmark.py
analysis/plot_bottleneck_heap.py
analysis/plot_pi_resources.py
analysis/plot_light_e2e.py
```

Protocol analysis:

```bash
python analysis/analyze_protocol_benchmark.py
```

Protocol Figures:

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

# 13. Data Interpretation Principles

This project follows the principle of interpreting measurement results only within the range directly supported by the experiment.

For example:

- MQTT QoS 0 showed the lowest RTT in this experiment, but this is not generalized to mean that MQTT QoS 0 is always faster than HTTP in every environment.
- MQTT QoS 1 showed higher RTT, but because the internal protocol stages were not measured separately, no single internal stage is claimed as the exact cause.
- `Application RTT - ESP32 Processing` is not described as pure Network Latency.
- The absence of a continuous Free Heap decrease does not prove that Memory Leaks are impossible.
- A `3000 / 3000` request success result does not demonstrate QoS reliability differences under Packet Loss conditions.
- The `success` field in the Light E2E dataset is kept separate from the results of the Physical Actuation Reliability Test.

One of the main purposes of this directory is not only to preserve the final results, but also to record **under which conditions the measurements were performed and why certain datasets were excluded from the final analysis**.
