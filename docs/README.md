# Development & Experiment Documents

이 디렉터리는 프로젝트의 **개발 과정, 실험 기록, 초기 계획**을 보존합니다.

대표 결과만 빠르게 확인하려면 [대표 프로젝트 보고서](../report/Raspberry_Pi_5_ESP32_Edge_Control_System_Report.pdf)를 보는 것을 권장합니다.

## Documents

- [`experiment-log/Edge_IoT_Control_System_Development_and_Experiment_Log.pdf`](experiment-log/Edge_IoT_Control_System_Development_and_Experiment_Log.pdf): 프로젝트 전 과정의 구현·실험·측정·분석을 상세히 남긴 장문 기록입니다. 기존 장문 기술 보고서를 **개발·실험 기록(Development & Experiment Log)** 으로 보존한 문서입니다.
- `experiment_log.md`: 구현, 실험, 문제 해결 과정을 시간순으로 기록한 개발 로그
- `project_plan.md`: 프로젝트 초기에 작성한 계획 문서
- `hardware_list.md`: 준비한 하드웨어와 용도 정리

문서 역할은 다음과 같이 구분합니다.

- **대표 보고서:** `report/Raspberry_Pi_5_ESP32_Edge_Control_System_Report.pdf`
- **프로젝트 개요 및 핵심 결과:** 루트 `README.md`, `README_EN.md`
- **상세 실험 데이터 및 분석 기준:** `data/README.md`, `data/README_EN.md`
- **개발·실험 세부 기록:** 이 디렉터리와 `experiment-log/`

> `project_plan.md`과 초기 `experiment_log.md`에는 IR / Camera 등 당시 검토했던 확장 아이디어가 포함되어 있습니다.  
> 이 항목들은 **최종 구현 기능을 의미하지 않습니다.** 현재 구현 및 분석 범위는 **Light Switch Node와 PC Power Node**입니다.

## Final scope

```text
Raspberry Pi 5 Edge Control Server
├── ESP32 Light Switch Node
└── ESP32 PC Power Node
```

최종 성능 분석에는 HTTP, MQTT QoS 0 / QoS 1 Application RTT, ESP32 Handler Processing / Heap, Raspberry Pi Resource Usage, Light Control E2E Latency가 포함됩니다.

---

For English readers: the **main project report** is available at [`report/Raspberry_Pi_5_ESP32_Edge_Control_System_Report.pdf`](../report/Raspberry_Pi_5_ESP32_Edge_Control_System_Report.pdf). The previous long-form technical report is preserved here as the **Development & Experiment Log**, while the root English README and `data/README_EN.md` provide the project overview and final dataset documentation.
