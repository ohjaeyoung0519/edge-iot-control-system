# Development Documents

이 디렉터리는 프로젝트의 **개발 과정과 당시의 계획**을 보존합니다.

- `experiment_log.md`: 구현, 실험, 문제 해결 과정을 시간순으로 기록한 개발 로그
- `project_plan.md`: 프로젝트 초기에 작성한 계획 문서
- `hardware_list.md`: 준비한 하드웨어와 용도 정리

> `project_plan.md`과 초기 `experiment_log.md`에는 IR / Camera 등 당시 검토했던 확장 아이디어가 포함되어 있습니다.  
> 이 항목들은 **최종 구현 기능을 의미하지 않습니다.** 현재 구현 및 분석 범위는 **Light Switch Node와 PC Power Node**이며, 최종 상태와 측정 결과는 루트 `README.md`와 `data/README.md`를 기준으로 합니다.

## Final scope

```text
Raspberry Pi 5 Edge Control Server
├── ESP32 Light Switch Node
└── ESP32 PC Power Node
```

최종 성능 분석에는 HTTP, MQTT QoS 0 / QoS 1 application RTT, ESP32 handler processing / heap, Raspberry Pi resource usage, Light Control E2E latency가 포함됩니다.
