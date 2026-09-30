# Development & Experiment Documents

이 디렉터리는 프로젝트의 **개발 과정, 실험 기록, 초기 계획**을 보존합니다.

## Documents

- `experiment-log/Edge_IoT_Control_System_Development_and_Experiment_Log.pdf`: 프로젝트 전 과정의 구현·실험·측정·분석을 상세히 남긴 장문 기록입니다. 기존의 장문 기술 보고서를 **개발·실험 기록(Development & Experiment Log)** 으로 보존한 문서이며, 대표 보고서가 아니라 세부 과정과 근거를 확인하기 위한 자료입니다.
- `experiment_log.md`: 구현, 실험, 문제 해결 과정을 시간순으로 기록한 개발 로그
- `project_plan.md`: 프로젝트 초기에 작성한 계획 문서
- `hardware_list.md`: 준비한 하드웨어와 용도 정리

대표 프로젝트 보고서는 `report/` 디렉터리에서 관리합니다. 루트 `README.md`는 프로젝트 개요와 핵심 결과를, `data/README.md`는 최종 실험 데이터와 분석 기준을 정리합니다.

> `project_plan.md`과 초기 `experiment_log.md`에는 IR / Camera 등 당시 검토했던 확장 아이디어가 포함되어 있습니다.  
> 이 항목들은 **최종 구현 기능을 의미하지 않습니다.** 현재 구현 및 분석 범위는 **Light Switch Node와 PC Power Node**입니다.

## Final scope

```text
Raspberry Pi 5 Edge Control Server
├── ESP32 Light Switch Node
└── ESP32 PC Power Node
```

최종 성능 분석에는 HTTP, MQTT QoS 0 / QoS 1 Application RTT, ESP32 Handler Processing / Heap, Raspberry Pi Resource Usage, Light Control E2E Latency가 포함됩니다.
