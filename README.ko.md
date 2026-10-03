# BEMS 이상 탐지 운영 콘솔

**🌐 Language:** [English](README.md) · **한국어**

> ICT Module 4 — Intermediate Project
> **스마트 빌딩 에너지 이상 탐지 및 대응 시스템**
> 김성현 · 개인 프로젝트

다중 zone의 건물 에너지 관리 시스템(BEMS) 텔레메트리를 시뮬레이션하고,
무선 네트워크의 지연·손실·노이즈를 시뮬레이션한 뒤, 선형 보간으로
결측값을 추정하고 머신러닝으로 이상을 탐지하며, 결정론적 룰 엔진으로 심각도 분류와 근본 원인을
진단한 다음, 7-탭 Streamlit 운영 콘솔로 모든 것을 한눈에 보여주는
**6단계 에이전트 파이프라인**입니다.

---

## 🎥  발표 영상

**[발표 영상 보기](https://youtu.be/Qljy0q05-nU)**

---

## 저장소 구조

```
.
├── src/                       모든 소스 코드
│   ├── config.py              센서 사양·존·네트워크 제약·파이프라인 파라미터
│   └── agents/                5개 백엔드 에이전트
│       ├── generator.py       Stage 1  ▸ 멀티존 BEMS 샘플 생성
│       ├── transmitter.py     Stage 2  ▸ 네트워크 열화 (지연 / 드롭 / 노이즈)
│       ├── collector.py       Stage 3  ▸ FastAPI + SQLite + 백그라운드 워커
│       ├── ml_processor.py    Stage 4  ▸ 보간 + 3-detector 앙상블
│       ├── decision.py        Stage 5  ▸ 결정론적 룰 엔진
│       ├── evaluator.py       MAE + Precision/Recall/F1 (ground truth 대비)
│       ├── scenarios.py       시나리오 프리셋 (화재 / HVAC / 피크 / …)
│       └── store.py           SQLite (WAL) 영속 계층
│
├── dashboard/                 웹 GUI 코드
│   └── app.py                 Stage 6  ▸ 7-탭 Streamlit + Plotly 콘솔
│
├── data/                      샘플 합성 데이터
│   ├── generate_samples.py    재생성 스크립트
│   ├── sample_truth.csv       600행 ground truth (3존 × 200샘플)
│   ├── sample_readings.csv    10% 드롭 적용 후 540행
│   ├── sample_decisions.csv   599개 Decision 출력 (Critical 50 / Warning 17 / Normal 532)
│   └── README.md              스키마 레퍼런스
│
├── tests/                     pytest 24개 (RLock 데드락 회귀 테스트 포함)
├── .streamlit/config.toml     대시보드 테마
├── requirements.txt
├── run_all.sh                 전체 단계 원클릭 기동 스크립트
├── README.md                  English version
├── README.ko.md               (이 문서)
└── TROUBLESHOOTING.md         개발 중 마주친 주요 버그와 해결법
```

---

## 시스템 개요

```
[1] Generator  →  [2] Transmitter  →  [3] Collector  →  [4] ML Processor  →  [5] Decision  →  [6] Dashboard
 3존,             지연 / 드롭 /          FastAPI +          보간 +                 룰 엔진           운영
 ground-truth     EM 노이즈              SQLite + 워커      Z-score + IForest      근본 원인 추정    콘솔
```

6개의 논리 단계는 **3개의 프로세스**로 실행됩니다. Transmitter가 Generator를
호출하고, Collector의 백그라운드 워커가 ML Processor와 Decision을 실행하며,
Dashboard는 별도 프로세스에서 REST API를 조회합니다. 결정 생성은 화면 갱신과
독립적으로 수행되며, 대시보드는 선택한 주기로 REST API를 다시 조회합니다.

기본 센서 전송은 REST입니다. `src/config.py`의 `PipelineConfig.transport`를
`"udp"`로 설정하면 JSON UDP 전송을 사용할 수 있습니다. 이것은 BACnet
프로토콜 구현이 아니며, 관리 API와 평가용 원본 전송은 계속 REST를 사용합니다.

### 6개 에이전트

| # | 단계 | 모듈 | 역할 |
|---|------|------|------|
| ① | Generator      | `src/agents/generator.py`     | 3존 × 4센서, 일일 점유 사이클 + Gaussian 노이즈, ground-truth 라벨 (`is_anomaly`, `scenario`) 부착 |
| ② | Transmitter    | `src/agents/transmitter.py`   | `/truth`로 원본 전송; 손실되지 않은 열화 사본을 REST 또는 UDP로 전송 |
| ③ | Collector      | `src/agents/collector.py`     | FastAPI · SQLite (WAL) 영속화 · 백그라운드 결정 워커 · 12개 REST 엔드포인트 |
| ④ | ML Processor   | `src/agents/ml_processor.py`  | 존별 reindex · 선형 보간 · 3개 탐지 신호 결합 |
| ⑤ | Decision       | `src/agents/decision.py`      | 심각도 분류 + 9-룰 설명 가능한 근본 원인 엔진 |
| ⑥ | Dashboard      | `dashboard/app.py`            | 7-탭 콘솔 — Building / Operations / Telemetry / Pipeline / Alerts / Scenario Lab / Quality Metrics |

### 센서 사양

| 센서 | 정상 범위 | 이상 임계 |
|------|-----------|-----------|
| 전력 소비        | 0 – 5 kW       | > 8 kW |
| 온도             | 20 – 26 °C     | > 30 °C 또는 < 15 °C |
| 습도             | 40 – 60 %      | > 75 % 또는 < 25 % |
| CO₂              | 400 – 800 ppm  | > 1200 ppm |

판정 조건 — (a) 하드 물리 임계 위반, (b) **robust Z-score** (MAD 기반,
\|z\| > 3.2) 초과, (c) **IsolationForest**가 다변량 이상치로 표시
— 셋 중 하나라도 만족하면 이상치로 분류됩니다. Decision Agent는
하드 임계 위반 또는 \|z\| > 4면 *Critical*, 그 외 발화는 *Warning*으로
승급시킵니다.

### Decision Agent — 근본 원인 룰 엔진

9개의 순서가 있는 룰을 위에서부터 매칭하며, **첫 매치가 승**합니다.
모든 진단은 감사 가능합니다.

| 룰 | 필요 신호 | 금지 신호 | 진단 |
|------|----------|-----------|------|
| `fire_risk`       | temp ↑, CO₂ ↑                    | humidity ↑       | 화재 / 열폭주 의심 |
| `hvac_failure`    | temp ↑, humidity ↑, CO₂ ↑        | —                | HVAC 냉방 실패 |
| `peak_load`       | power ↑                          | temp ↑, CO₂ ↑    | 피크 전력 부하 |
| `cold_snap`       | temp ↓                           | —                | 난방 손실 / 환기 노출 |
| `occupancy_spike` | CO₂ ↑, humidity ↑                | power ↑, temp ↑  | 점유율 급증 / 환기 부족 |
| `humidity_anomaly`| humidity ↑                       | —                | 습도 이상 |
| `low_humidity`    | humidity ↓                       | —                | 저습도 / 건조 |
| `co2_only`        | CO₂ ↑                            | —                | CO₂ 상승 — 환기 점검 |
| `temperature_only`| temp ↑                           | —                | 온도 드리프트 |

각 룰은 구체적인 **권고 조치** 문구와 함께 묶여 있습니다.

---

## 빠른 시작

```bash
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt 'streamlit>=1.37.0'
./run_all.sh
```

* 대시보드: <http://localhost:8501>
* Collector API 문서: <http://127.0.0.1:8000/docs>

`st.fragment` 사용을 위해 Streamlit 1.37 이상이 필요합니다.

로그는 `./logs/`에 쌓입니다. Ctrl-C로 모든 단계가 정지됩니다.

## 단계별 개별 실행

각 명령은 가상환경을 활성화한 별도 터미널에서 실행합니다.

```bash
export PYTHONPATH="$PWD"
python -m src.agents.collector      # Stage 3 + 백그라운드 Stage 4 + 5
python -m src.agents.transmitter    # Stage 1 + 2
streamlit run dashboard/app.py      # Stage 6
```

## Collector REST API

| 메서드 | 경로            | 용도 |
|--------|-----------------|------|
| POST   | `/truth`        | Generator의 clean 샘플 (평가 전용) |
| POST   | `/ingest`       | Transmitter의 열화된 패킷 |
| POST   | `/inject`       | 사용자 시나리오 또는 커스텀 샘플 |
| POST   | `/reset`        | 운영 저장소 초기화 |
| GET    | `/zones`        | 설정된 존 + 데이터가 있는 존 |
| GET    | `/scenarios`    | 프리셋 라이브러리 |
| GET    | `/raw`          | 버퍼링된 readings + 결측 seq 리스트 |
| GET    | `/processed`    | ML 복구 + 이상 플래그 프레임 |
| GET    | `/decisions`    | severity + diagnosis + action 히스토리 |
| GET    | `/stats`        | 존별 패킷 통계 + 워커 상태 |
| GET    | `/evaluation`   | 보간 MAE + 탐지 P/R/F1 |
| GET    | `/health`       | 라이브니스 프로브 |

## Scenario Lab — 제어된 결함 주입

```bash
# 프리셋 시나리오
curl -X POST http://127.0.0.1:8000/inject \
     -H "Content-Type: application/json" \
     -d '{"zone":"Zone-A","scenario":"fire_risk"}'

# 커스텀 reading
curl -X POST http://127.0.0.1:8000/inject \
     -H "Content-Type: application/json" \
     -d '{"zone":"Zone-B","readings":{"power":15,"temperature":35,"humidity":85,"co2":1500}}'
```

프리셋: `hvac_failure`, `peak_load`, `fire_risk`, `cold_snap`, `occupancy_spike`.

## 테스트

```bash
source .venv/bin/activate && python -m pytest tests/ -v
```

24개 케이스 — SQLite 저장소 + RLock 데드락 회귀 테스트, 존별 보간,
Z-score / hard-threshold / IsolationForest detector, severity 분류,
주요 root-cause 룰, 시나리오 라이브러리, 종단 evaluator.

---

## 기술 스택

Python 3.11+ · FastAPI · SQLite (WAL) · pandas / NumPy / scikit-learn ·
Streamlit + Plotly. 결정 로직은 **순수 룰 엔진** — 외부 LLM 의존성
없음. 테스트는 pytest.

## 문서

- `TROUBLESHOOTING.md` — 개발 중 마주친 실제 버그 (RLock 데드락,
  `0 or -1` 정수 함정, Z-score masking effect 등) 와 해결 방법

## 한계

합성 데이터로 구성한 로컬 시뮬레이션입니다. 실제 건물 센서 연동이나 운영 환경 성능을
검증하지 않았으며, 규칙 기반 진단은 확정된 원인이 아닙니다. API에는 인증 계층이 없고,
센서 임계값과 권고 조치는 시연용입니다. 현재 실행 구조와 설정은 [English README](README.md)를 참고하세요.
