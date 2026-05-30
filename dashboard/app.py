"""Stage 6 — Dashboard Agent (Enterprise Control Center).

A dense, scannable operations console for the BEMS pipeline with six tabs:
Operations · Telemetry · Pipeline · Alerts · Scenario Lab · Quality Metrics.

Bilingual UI — switch English / 한국어 from the sidebar.
"""
from __future__ import annotations

import io
import time
from datetime import datetime

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import PIPELINE, SENSORS, SENSOR_NAMES, ZONES, ZONE_NAMES


# ────────────────────────────────────────────────────────────── page setup
st.set_page_config(
    page_title="BEMS — Anomaly Operations Center",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- enterprise palette (Atlassian/Linear-inspired) ----------------------
C_BG       = "#f5f7fa"
C_SURFACE  = "#ffffff"
C_SURFACE2 = "#fafbfc"
C_BORDER   = "#e1e4e8"
C_BORDER2  = "#d0d7de"
C_TEXT     = "#172b4d"
C_TEXT2    = "#42526e"
C_MUTED    = "#6b778c"
C_PRIMARY  = "#1f5dde"
C_PRIMARY_BG = "#e8f0ff"
C_OK       = "#1f7a4d"
C_OK_BG    = "#e3f5ec"
C_WARN     = "#9a5b00"
C_WARN_BG  = "#fff4e0"
C_CRIT     = "#a1271d"
C_CRIT_BG  = "#fde4e1"
C_ACCENT   = "#6a4cff"

SEVERITY_COLOR = {"Normal": C_OK, "Warning": C_WARN, "Critical": C_CRIT}
SEVERITY_BG    = {"Normal": C_OK_BG, "Warning": C_WARN_BG, "Critical": C_CRIT_BG}

PLOT = {
    "interp":      C_PRIMARY,
    "raw":         "#8993a4",
    "z_anom":      C_CRIT,
    "iforest":     C_ACCENT,
    "normal_band": "#1f7a4d",
    "grid":        "#eaedf2",
    "axis":        "#a5adba",
}


# ════════════════════════════════════════════════════════ i18n / language
# Each entry maps a key to (English, Korean). Brand names, severity words,
# detector names and sensor names stay in English on purpose (standard terms).
I18N: dict[str, tuple[str, str]] = {
    # app bar
    "appbar_sub": ("Smart Building Energy Management · 6-stage agent pipeline · {n} monitored zones",
                   "스마트 빌딩 에너지 관리 · 6단계 에이전트 파이프라인 · {n}개 모니터링 존"),
    "all_ok": ("All Systems OK", "전체 정상"),
    "worker_error": ("Worker Error", "워커 오류"),
    "decider_online": ("Decider Online", "결정 엔진 가동"),
    "decider_idle": ("Decider Idle", "결정 엔진 대기"),
    # sidebar
    "console_sub": ("v2.0 · operations", "v2.0 · 운영"),
    "lang_label": ("Language / 언어", "Language / 언어"),
    "sec_refresh": ("Refresh", "새로고침"),
    "auto_refresh": ("Auto-refresh", "자동 새로고침"),
    "interval": ("Interval (s)", "주기 (초)"),
    "refresh_on": ("Auto-refresh ON · every {s}s", "자동 새로고침 ON · {s}초마다"),
    "refresh_off": ("Auto-refresh OFF · every {s}s", "자동 새로고침 OFF · {s}초마다"),
    "sec_admin": ("Administration", "관리"),
    "reset_btn": ("Reset operational store", "운영 데이터 초기화"),
    "reset_done": ("Store wiped.", "데이터가 초기화되었습니다."),
    "sec_thresholds": ("Sensor thresholds", "센서 임계값"),
    # tabs
    "tab_operations": ("Operations", "운영 현황"),
    "tab_telemetry": ("Telemetry", "센서 데이터"),
    "tab_pipeline": ("Pipeline", "파이프라인"),
    "tab_alerts": ("Alerts", "알림"),
    "tab_scenario": ("Scenario Lab", "시나리오 랩"),
    "tab_metrics": ("Quality Metrics", "품질 지표"),
    "tab_building": ("Building", "건물 뷰"),
    # building view
    "bld_title": ("Live Building View", "실시간 건물 뷰"),
    "bld_sub": ("Real-time status of every zone — floors glow by severity, and a sensor dot "
                "turns red the moment it breaches a limit.",
                "존별 실시간 상태 — 층은 심각도에 따라 색이 바뀌고, 임계 위반 시 센서 점이 즉시 빨개집니다."),
    "bld_rooftop": ("ROOFTOP · HVAC PLANT", "옥상 · HVAC 설비"),
    "bld_floor": ("Floor", "층"),
    "bld_legend": ("● sensor normal    ● sensor breached    ·    floor tint = zone severity",
                   "● 센서 정상    ● 센서 위반    ·    층 색 = 존 심각도"),
    "bld_demo": ("Live demo — inject a fault and watch the floor react",
                 "라이브 데모 — 결함을 주입하면 해당 층이 반응합니다"),
    "bld_scenario": ("Scenario", "시나리오"),
    "bld_inject": ("Inject", "주입"),
    "bld_no_data": ("No live data yet — start the transmitter or inject a sample.",
                    "아직 실시간 데이터가 없습니다 — 송신기를 켜거나 샘플을 주입하세요."),
    "bld_status_ok": ("All zones nominal", "모든 존 정상"),
    "bld_status_warn": ("Attention — warnings active", "주의 — Warning 발생 중"),
    "bld_status_crit": ("Critical — immediate attention required", "Critical — 즉시 조치 필요"),
    "bld_trend": ("recent trend", "최근 추세"),
    "bld_view": ("View", "보기"),
    "bld_cross": ("Cross-section", "단면도"),
    "bld_plan": ("Floor plan", "평면도"),
    "bld_north": ("NORTH", "북"),
    "bld_drill": ("Drill-down — open a zone's live sensor charts",
                  "드릴다운 — 존의 실시간 센서 차트 열기"),
    "bld_inspecting": ("Inspecting", "상세 보기"),
    "bld_close": ("Close", "닫기"),
    # operations KPIs
    "kpi_zones": ("Active Zones", "활성 존"),
    "kpi_received": ("Packets Received", "수신 패킷"),
    "kpi_loss": ("Packet Loss", "패킷 손실"),
    "kpi_decisions": ("Decisions Made", "생성된 결정"),
    "kpi_critical": ("Critical Alerts", "Critical 알림"),
    "kpi_warning": ("Warning Alerts", "Warning 알림"),
    # operations — services
    "sys_services": ("System Services", "시스템 서비스"),
    "sys_services_sub": ("Health of the 6 pipeline stages", "6개 파이프라인 단계의 상태"),
    "col_service": ("Service", "서비스"),
    "col_description": ("Description", "설명"),
    "col_status": ("Status", "상태"),
    "st_operational": ("Operational", "정상"),
    "st_idle": ("Idle", "대기"),
    "st_error": ("Error", "오류"),
    "worker_error_label": ("Worker error:", "워커 오류:"),
    "svc_generator": ("synthetic BEMS sample stream", "BEMS 센서 샘플 생성 스트림"),
    "svc_transmitter": ("network degradation + forwarding", "네트워크 열화 + 전달"),
    "svc_ml": ("interpolate + Z-score + IForest", "보간 + Z-score + IForest"),
    "svc_decision_rule": ("rule-based · last tick {t}", "룰 기반 · 마지막 실행 {t}"),
    "svc_dashboard": ("this console", "이 콘솔"),
    # decision timeline
    "dt_title": ("Decision Timeline", "결정 타임라인"),
    "dt_sub": ("Recent decisions across all zones — Critical/Warning highlighted",
               "전체 존의 최근 결정 — Critical/Warning 강조 표시"),
    "show_normal": ("Show Normal", "Normal 표시"),
    "show_normal_help": ("Hide nominal events to make anomalies easier to spot.",
                         "정상 이벤트를 숨겨 이상치를 더 잘 보이게 합니다."),
    "awaiting_decision": ("Awaiting first decision from worker.", "워커의 첫 결정을 기다리는 중입니다."),
    "window_last": ("window: last {n} decisions", "범위: 최근 {n}개 결정"),
    "dt_caption": ("Critical = star, Warning = diamond, Normal = small dot. Click a legend item to isolate that severity.",
                   "Critical은 별, Warning은 다이아몬드, Normal은 작은 점. 범례를 클릭하면 해당 심각도만 표시됩니다."),
    # zone status
    "zone_status": ("Zone Status", "존 현황"),
    "zone_status_sub": ("Per-zone packet flow over the rolling window", "롤링 윈도우 기준 존별 패킷 흐름"),
    "z_received": ("Received", "수신"),
    "z_expected": ("Expected", "기대치"),
    "z_missing": ("Missing", "손실"),
    "z_seq_range": ("Seq range", "Seq 범위"),
    "loss_suffix": ("{p}% loss", "{p}% 손실"),
    "no_telemetry": ("No telemetry yet. Awaiting transmitter.", "아직 데이터가 없습니다. 송신기를 기다리는 중입니다."),
    # telemetry
    "sel_zone": ("Zone", "존"),
    "tel_show_raw": ("Show raw points", "원시 데이터 표시"),
    "tel_show_raw_help": ("Gray dots are the degraded readings before ML recovery.",
                          "회색 점은 ML 복구 이전의 열화된 측정값입니다."),
    "tel_raw_points": ("Raw points", "원시 포인트"),
    "tel_recovered_rows": ("Recovered rows", "복구된 행"),
    "tel_dropped": ("Packets dropped", "손실 패킷"),
    "tel_flagged": ("Flagged anomalies", "탐지된 이상치"),
    "no_telemetry_arrived": ("No telemetry has arrived yet.", "아직 도착한 데이터가 없습니다."),
    "packet_loss_banner": ("<b>Packet loss detected</b> — {n} sequence(s) dropped; the ML Processor "
                           "reconstructed them (shown as hollow diamonds). Recent gaps: ",
                           "<b>패킷 손실 감지</b> — {n}개 시퀀스 손실; ML 프로세서가 복구했습니다 "
                           "(속 빈 다이아몬드로 표시). 최근 손실 구간: "),
    "charts_per_row": ("Charts per row", "행당 차트 수"),
    "charts_per_row_help": ("Switch to 1 per row for full-width, easier-to-read charts.",
                            "1로 바꾸면 차트가 전체 너비로 표시되어 보기 편합니다."),
    "lk_signal": ("Recovered signal", "복구 신호"),
    "lk_recovered": ("Reconstructed point", "복구된 포인트"),
    "lk_zscore": ("Z-score / hard breach", "Z-score / 하드 임계 위반"),
    "lk_iforest": ("IsolationForest", "IsolationForest"),
    "lk_normal": ("Normal band", "정상 범위"),
    "lk_danger": ("Danger zone", "위험 구역"),
    # pipeline
    "agent_topology": ("Agent Topology", "에이전트 구성도"),
    "agent_topology_sub": ("Six independent agents communicating via REST. Each card lists the agent's "
                           "responsibility, source file, and live KPIs.",
                           "REST로 통신하는 6개의 독립 에이전트. 각 카드는 역할, 소스 파일, 실시간 지표를 보여줍니다."),
    "source_label": ("Source", "소스"),
    "kp_truth_rows": ("Truth rows", "Truth 행"),
    "kp_cadence": ("Cadence", "주기"),
    "kp_received": ("Received", "수신"),
    "kp_dropped": ("Dropped", "손실"),
    "kp_zones": ("Zones", "존"),
    "kp_database": ("Database", "데이터베이스"),
    "kp_window": ("Window", "윈도우"),
    "kp_zthr": ("Z-threshold", "Z-임계값"),
    "kp_decisions": ("Decisions", "결정"),
    "kp_last_tick": ("Last tick", "마지막 실행"),
    "kp_refresh": ("Refresh", "갱신"),
    "kp_render": ("Render", "렌더"),
    "win_rows": ("{n} rows", "{n}행"),
    "render_live": ("live", "실시간"),
    "role_generator": ("Multi-zone BEMS sample stream. Each tick emits one sample per zone with a "
                       "daily-cycle baseline, Gaussian noise, and a ground-truth anomaly label.",
                       "멀티존 BEMS 샘플 생성. 매 틱마다 존별로 일일 사이클 기준선 + 가우시안 노이즈 + "
                       "ground-truth 이상 라벨이 붙은 샘플을 하나씩 생성합니다."),
    "role_transmitter": ("Forwards every sample twice — clean copy to /truth (for evaluation), degraded "
                         "copy (variable delay, 10% packet drop, EM noise) to /ingest.",
                         "각 샘플을 두 번 전달 — 깨끗한 사본은 /truth(평가용), 열화된 사본(가변 지연, "
                         "10% 패킷 손실, EM 노이즈)은 /ingest로 전송합니다."),
    "role_collector": ("FastAPI service. Persists truth, readings, and decisions to SQLite (WAL). Hosts "
                       "the background decision worker. Exposes raw, processed, decisions, stats, etc.",
                       "FastAPI 서비스. truth·readings·decisions를 SQLite(WAL)에 영속화하고 백그라운드 "
                       "결정 워커를 실행합니다. raw·processed·decisions·stats 등을 제공합니다."),
    "role_ml": ("Per-zone reindex and linear interpolation of dropped sequences. Three detectors run in "
                "parallel: robust Z-score (MAD), IsolationForest, and hard physical thresholds.",
                "존별 reindex와 손실 시퀀스 선형 보간. 세 detector를 병렬 실행: robust Z-score(MAD), "
                "IsolationForest, 하드 물리 임계값."),
    "role_decision": ("Severity classification (Normal / Warning / Critical). A nine-rule engine matches "
                      "the fired-sensor pattern to a known event and outputs an explainable diagnosis + action.",
                      "심각도 분류(Normal / Warning / Critical). 9개 룰 엔진이 발화한 센서 패턴을 알려진 "
                      "사고에 매칭하여 설명 가능한 진단과 조치를 출력합니다."),
    "role_dashboard": ("This console. Polls the Collector and renders operations, telemetry, alerts, "
                       "scenario lab, and quality-metrics surfaces.",
                       "이 콘솔. 콜렉터를 폴링하여 운영·센서·알림·시나리오 랩·품질 지표 화면을 렌더링합니다."),
    # alerts
    "al_total": ("Total decisions", "전체 결정"),
    "al_critical": ("Critical", "Critical"),
    "al_warning": ("Warning", "Warning"),
    "al_normal": ("Normal", "Normal"),
    "f_severity": ("Severity", "심각도"),
    "f_zone": ("Zone", "존"),
    "f_max_rows": ("Max rows", "최대 행 수"),
    "no_alerts": ("No alerts have been generated yet.", "아직 생성된 알림이 없습니다."),
    "no_match": ("No alerts match the current filters.", "현재 필터에 해당하는 알림이 없습니다."),
    "export_csv": ("Export filtered alerts (CSV)", "필터된 알림 내보내기 (CSV)"),
    "rec_action": ("Recommended action:", "권고 조치:"),
    "detector": ("Detector", "탐지기"),
    # scenario lab
    "ci_title": ("Controlled Fault Injection", "제어된 결함 주입"),
    "ci_sub": ("Push synthetic samples into the pipeline to validate runbooks and detector response. "
               "Injected samples are labelled as ground-truth anomalies so Quality Metrics can score them.",
               "합성 샘플을 파이프라인에 주입하여 대응 절차와 탐지 성능을 검증합니다. 주입된 샘플은 "
               "ground-truth 이상치로 표기되어 품질 지표에서 평가됩니다."),
    "preset_scenarios": ("Preset scenarios", "프리셋 시나리오"),
    "target_zone": ("Target zone", "대상 존"),
    "inject_into": ("Inject into {zone}", "{zone}에 주입"),
    "inject_success": ("Injected {tag} into {zone} at seq {seq}. The decision appears in the Alerts tab "
                       "within {s}s.",
                       "{tag}을(를) {zone}에 주입했습니다 (seq {seq}). 결정은 {s}초 내 Alerts 탭에 나타납니다."),
    "custom_sample": ("Custom sample — set each sensor and watch the result",
                      "커스텀 샘플 — 각 센서값을 설정하고 결과를 확인"),
    "label_anomaly": ("Label as ground-truth anomaly", "ground-truth 이상치로 표기"),
    "inject_custom": ("Inject custom sample", "커스텀 샘플 주입"),
    "inject_custom_ok": ("Injected into {zone} at seq {seq}.", "{zone}에 주입했습니다 (seq {seq})."),
    "recent_injections": ("Recent injections", "최근 주입 내역"),
    "no_injections": ("No manual injections have been recorded yet.", "아직 수동 주입 기록이 없습니다."),
    # injection preview / result
    "preview": ("Live preview — how each value compares to its limits",
                "실시간 미리보기 — 각 값이 임계와 어떻게 비교되는지"),
    "preview_normal": ("within normal range", "정상 범위 이내"),
    "preview_breach": ("BREACH — past the limit", "위반 — 임계 초과"),
    "expected_sev": ("Predicted severity", "예상 심각도"),
    "result_title": ("Injection result", "주입 결과"),
    "result_wait": ("Waiting for the decision worker…", "결정 워커를 기다리는 중…"),
    "result_decided": ("Decided in {ms} — the pipeline classified your sample:",
                       "{ms} 만에 처리됨 — 파이프라인이 샘플을 분류했습니다:"),
    "result_open_alerts": ("See it in the Alerts tab", "Alerts 탭에서 확인"),
    "norm_label": ("normal {lo}–{hi}{u}", "정상 {lo}–{hi}{u}"),
    "thr_label": ("limit {op}{v}{u}", "임계 {op}{v}{u}"),
    "col_time": ("Time", "시각"),
    "col_zone": ("Zone", "존"),
    "col_seq": ("Seq", "Seq"),
    # quality metrics
    "interp_quality": ("Interpolation Quality", "보간 품질"),
    "interp_sub": ("Mean absolute error between recovered values and ground-truth. <b>Recovered-only</b> "
                   "isolates the dropped sequences the ML Processor actually had to reconstruct.",
                   "복구값과 ground-truth 간 평균 절대 오차(MAE). <b>복구 전용</b>은 ML 프로세서가 실제로 "
                   "복원해야 했던 손실 시퀀스만 따로 측정합니다."),
    "m_truth_rows": ("Truth rows", "Truth 행"),
    "m_recovered_gaps": ("Recovered gaps", "복구된 구간"),
    "m_avg_mae": ("Avg recovery MAE", "평균 복구 MAE"),
    "col_sensor": ("Sensor", "센서"),
    "col_mae_rec": ("MAE (recovered)", "MAE (복구분)"),
    "col_mae_all": ("MAE (all rows)", "MAE (전체)"),
    "col_rec_samples": ("Recovered samples", "복구 샘플 수"),
    "not_enough_overlap": ("Not enough overlap between truth and readings yet.",
                           "truth와 readings 간 겹치는 구간이 아직 부족합니다."),
    "detection_perf": ("Anomaly Detection Performance", "이상 탐지 성능"),
    "detection_sub": ("Precision / Recall / F1 of each detector against the ground-truth labels. "
                      "<b>Union</b> combines all three.",
                      "ground-truth 라벨 대비 각 detector의 정밀도/재현율/F1. <b>Union</b>은 셋을 결합합니다."),
    "m_labelled": ("Labelled samples", "라벨된 샘플"),
    "m_prevalence": ("Anomaly prevalence", "이상치 비율"),
    "m_detectors": ("Detectors evaluated", "평가된 탐지기"),
    "prf_label": ("Precision · Recall · F1 by detector", "탐지기별 정밀도 · 재현율 · F1"),
    "confusion_counts": ("Confusion counts", "혼동 행렬 카운트"),
    "best_f1": ("Best F1: <b>{d}</b> at <b>{f}</b> — <code>union</code> combines all three detectors' strengths.",
                "최고 F1: <b>{d}</b> ({f}) — <code>union</code>은 세 탐지기의 장점을 결합합니다."),
    "need_labelled": ("Need a few labelled samples before metrics are meaningful.",
                      "지표가 유의미하려면 라벨된 샘플이 조금 더 필요합니다."),
    "no_data_eval": ("No data to evaluate yet.", "아직 평가할 데이터가 없습니다."),
    # footer
    "footer_refresh": ("Last refresh {ts}", "마지막 갱신 {ts}"),
}


def _lang() -> str:
    return st.session_state.get("lang", "en")


def t(key: str, **kwargs) -> str:
    pair = I18N.get(key)
    if not pair:
        return key
    s = pair[1] if _lang() == "ko" else pair[0]
    return s.format(**kwargs) if kwargs else s


CSS = f"""
<style>
:root {{
  --bg: {C_BG}; --surface: {C_SURFACE}; --surface2: {C_SURFACE2};
  --border: {C_BORDER}; --border2: {C_BORDER2};
  --text: {C_TEXT}; --text2: {C_TEXT2}; --muted: {C_MUTED};
  --primary: {C_PRIMARY}; --primary-bg: {C_PRIMARY_BG};
  --ok: {C_OK}; --ok-bg: {C_OK_BG};
  --warn: {C_WARN}; --warn-bg: {C_WARN_BG};
  --crit: {C_CRIT}; --crit-bg: {C_CRIT_BG};
}}

/* --- layout --------------------------------------------------------- */
.stApp {{ background: var(--bg); }}
.main .block-container {{ padding-top: 1.5rem !important; max-width: 1480px; }}
section[data-testid="stSidebar"] {{
  background: var(--surface) !important;
  border-right: 1px solid var(--border);
  padding-top: 0.4rem !important;
}}

/* --- typography ----------------------------------------------------- */
html, body, [class*="css"] {{
  font-family: -apple-system, "Segoe UI", "Helvetica Neue", "Inter", sans-serif !important;
  color: var(--text);
}}
h1, h2, h3, h4, h5 {{ color: var(--text); letter-spacing: -0.01em; }}
.section-title {{
  font-size: 1.1rem; font-weight: 700; color: var(--text);
  margin: 4px 0 2px 0;
}}
.section-sub {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 14px; }}

/* --- top app bar ---------------------------------------------------- */
.appbar {{
  display: flex; align-items: center; justify-content: space-between;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 14px 20px; margin-bottom: 18px;
  box-shadow: 0 1px 1px rgba(9,30,66,0.04);
}}
.appbar-brand {{ display: flex; align-items: center; gap: 14px; }}
.appbar-logo {{
  width: 32px; height: 32px; border-radius: 8px;
  background: linear-gradient(135deg, #1f5dde, #6a4cff);
  display: inline-flex; align-items: center; justify-content: center;
  color: white; font-weight: 800; font-size: 1.1rem;
}}
.appbar-title {{ font-size: 1.05rem; font-weight: 700; color: var(--text); line-height: 1.1; }}
.appbar-sub {{ font-size: 0.78rem; color: var(--muted); margin-top: 2px; }}
.appbar-status {{ display: flex; align-items: center; gap: 10px; }}

/* --- pills & status ------------------------------------------------- */
.pill {{
  display: inline-flex; align-items: center; gap: 6px;
  padding: 3px 10px; border-radius: 6px;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.03em;
  text-transform: uppercase; border: 1px solid transparent;
}}
.pill-ok   {{ background: var(--ok-bg);   color: var(--ok);   border-color: #c2e5d3; }}
.pill-warn {{ background: var(--warn-bg); color: var(--warn); border-color: #f3d9a8; }}
.pill-crit {{ background: var(--crit-bg); color: var(--crit); border-color: #f3c4be; }}
.pill-info {{ background: var(--primary-bg); color: var(--primary); border-color: #c9dafa; }}
.pill-muted {{ background: #eef0f3; color: var(--text2); border-color: #dde1e6; }}
.pill-dot {{
  width: 6px; height: 6px; border-radius: 50%;
  display: inline-block; background: currentColor;
}}

/* --- KPI cards ------------------------------------------------------ */
[data-testid="stMetric"] {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px 14px 18px;
  box-shadow: 0 1px 2px rgba(9,30,66,0.05);
  position: relative; overflow: hidden;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}}
[data-testid="stMetric"]::before {{
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  opacity: 0.9;
}}
[data-testid="stMetric"]:hover {{
  box-shadow: 0 6px 18px rgba(9,30,66,0.10); transform: translateY(-1px);
}}
[data-testid="stMetricValue"] {{
  font-size: 1.75rem !important; color: var(--text);
  font-weight: 800; letter-spacing: -0.025em;
  font-variant-numeric: tabular-nums;
}}
[data-testid="stMetricLabel"] {{
  color: var(--muted) !important; font-weight: 600 !important;
  font-size: 0.68rem !important; text-transform: uppercase; letter-spacing: 0.07em;
}}
[data-testid="stMetricDelta"] {{ font-size: 0.78rem !important; }}

/* --- tabs (the navigation row) ------------------------------------- */
.stTabs [data-baseweb="tab-list"] {{
  gap: 2px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 4px; margin-bottom: 18px;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent; border-radius: 6px;
  padding: 8px 16px; color: var(--text2); font-weight: 600; font-size: 0.88rem;
  border: 0;
}}
.stTabs [aria-selected="true"] {{
  background: var(--primary-bg) !important; color: var(--primary) !important;
}}

/* --- buttons -------------------------------------------------------- */
.stButton > button {{
  border-radius: 6px; border: 1px solid var(--border2);
  background: var(--surface); color: var(--text);
  font-weight: 600; font-size: 0.85rem;
  padding: 6px 14px; box-shadow: 0 1px 0 rgba(9,30,66,0.04);
  transition: background 0.12s ease, border-color 0.12s ease;
}}
.stButton > button:hover {{
  background: var(--surface2); border-color: var(--text2); color: var(--text);
}}
.stButton > button[kind="primary"] {{
  background: var(--primary); color: white; border-color: var(--primary);
}}
.stButton > button[kind="primary"]:hover {{
  background: #1849b8; border-color: #1849b8; color: white;
}}

/* --- cards (zones, agents, services) ------------------------------- */
.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px 16px;
  box-shadow: 0 1px 0 rgba(9,30,66,0.04);
}}
.card-head {{
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}}
.card-title {{ font-weight: 700; color: var(--text); font-size: 0.95rem; }}
.card-sub   {{ font-size: 0.78rem; color: var(--muted); }}
.card-row   {{
  display: flex; justify-content: space-between; padding: 6px 0;
  border-top: 1px solid var(--border); font-size: 0.85rem;
}}
.card-row:first-of-type {{ border-top: 0; }}
.card-row .k {{ color: var(--muted); }}
.card-row .v {{ color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }}

/* --- services table (operations) ---------------------------------- */
.svc-table {{
  width: 100%; border-collapse: collapse;
  border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
  background: var(--surface);
}}
.svc-table th {{
  background: var(--surface2); padding: 10px 14px;
  text-align: left; font-size: 0.7rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600;
  border-bottom: 1px solid var(--border);
}}
.svc-table td {{
  padding: 12px 14px; font-size: 0.88rem; color: var(--text);
  border-bottom: 1px solid var(--border);
}}
.svc-table tr:last-child td {{ border-bottom: 0; }}
.svc-table code {{
  background: var(--surface2); padding: 2px 6px; border-radius: 4px;
  font-size: 0.78rem; color: var(--text2);
}}

/* --- alert rows ----------------------------------------------------- */
.alert-row {{
  display: grid;
  grid-template-columns: 86px 100px 120px 1fr;
  gap: 14px; padding: 12px 16px;
  background: var(--surface); border: 1px solid var(--border);
  border-left-width: 4px; border-radius: 6px;
  margin-bottom: 8px; align-items: start;
}}
.alert-meta-col {{
  display: flex; flex-direction: column; gap: 4px;
  font-size: 0.78rem; color: var(--muted);
}}
.alert-meta-col .time {{ color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }}
.alert-meta-col code {{
  background: var(--surface2); padding: 1px 6px; border-radius: 4px;
  color: var(--text2); font-size: 0.72rem;
}}
.alert-diag {{ color: var(--text); font-weight: 600; font-size: 0.92rem; margin-bottom: 4px; }}
.alert-action {{ color: var(--text2); font-size: 0.85rem; line-height: 1.45; }}
.alert-evidence {{
  margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px;
}}

/* --- scenario preset cards ----------------------------------------- */
.preset {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px;
}}
.preset-id   {{ font-size: 0.68rem; color: var(--muted); text-transform: uppercase;
                letter-spacing: 0.06em; font-weight: 600; }}
.preset-name {{ font-size: 1rem; font-weight: 700; color: var(--text); margin-top: 2px; }}
.preset-desc {{ font-size: 0.82rem; color: var(--text2); line-height: 1.45;
                margin: 8px 0 12px 0; min-height: 50px; }}

/* --- inputs --------------------------------------------------------- */
[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
  background: var(--surface) !important;
  border-color: var(--border2) !important;
  color: var(--text) !important;
  font-size: 0.88rem !important;
}}
.stTextInput label, .stNumberInput label, .stSelectbox label {{
  font-size: 0.78rem !important; color: var(--text2) !important; font-weight: 600 !important;
}}

/* --- dataframe ------------------------------------------------------ */
[data-testid="stDataFrame"] {{
  border: 1px solid var(--border); border-radius: 8px;
}}

/* --- chart card: wrap plotly charts in a clean panel --------------- */
[data-testid="stPlotlyChart"] {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 16px 10px 16px;
  box-shadow: 0 1px 2px rgba(9,30,66,0.04);
  margin-bottom: 20px;
}}

/* --- section divider rhythm ---------------------------------------- */
hr {{ margin: 0.6rem 0 !important; border-color: var(--border) !important; }}

/* --- chart panel label --------------------------------------------- */
.chart-label {{
  font-size: 0.82rem; font-weight: 700; color: var(--text2);
  margin: 2px 0 6px 2px; display: flex; align-items: center; gap: 8px;
}}

/* --- building view ------------------------------------------------- */
.bld-wrap {{ max-width: 940px; margin: 4px auto 0 auto; }}
.bld-roof {{
  height: 30px; border-radius: 12px 12px 0 0;
  background: linear-gradient(180deg, #2b3a67, #1a2a5e);
  border: 1px solid #1a2a5e; border-bottom: 0;
  color: #cdd8f5; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em;
  display: flex; align-items: center; justify-content: center;
}}
.bld-ground {{
  height: 16px; border-radius: 0 0 12px 12px;
  border: 1px solid var(--border); border-top: 0;
  background: repeating-linear-gradient(45deg,#cbd5e1,#cbd5e1 9px,#e2e8f0 9px,#e2e8f0 18px);
}}
.floor {{
  display: flex; align-items: center; gap: 18px;
  border: 1px solid var(--border); border-top: 0;
  padding: 16px 20px; position: relative; overflow: hidden;
}}
.floor-left {{ width: 230px; flex: 0 0 230px; }}
.floor-name {{ font-size: 1.25rem; font-weight: 800; color: var(--text); line-height: 1.1; }}
.floor-fn {{ font-size: 0.78rem; color: var(--muted); margin: 3px 0 9px 0; }}
.floor-sensors {{ display: flex; gap: 10px; flex: 1; flex-wrap: wrap; }}
.bld-summary {{
  max-width: 940px; margin: 0 auto 14px auto;
  display: flex; align-items: center; gap: 16px;
  padding: 13px 20px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px;
  box-shadow: 0 1px 2px rgba(9,30,66,0.05);
}}
.bld-summary .bs-status {{ font-size: 1.05rem; font-weight: 800; color: var(--text); }}
.bld-summary .bs-counts {{ margin-left: auto; display: flex; gap: 8px; }}
.floor-num {{
  display: inline-flex; width: 30px; height: 30px; border-radius: 8px;
  background: var(--surface2); color: var(--text2); font-weight: 800;
  align-items: center; justify-content: center; font-size: 0.9rem;
  margin-bottom: 8px; border: 1px solid var(--border);
}}
.schip {{
  flex: 1; min-width: 152px; border: 1px solid var(--border); border-radius: 10px;
  padding: 8px 11px 7px 11px; background: var(--surface);
}}
.schip-top {{ display: flex; align-items: center; gap: 8px; }}
.schip .dot {{ width: 9px; height: 9px; border-radius: 50%; flex: 0 0 auto; }}
.schip.ok .dot  {{ background: #16a34a; }}
.schip.bad .dot {{ background: #ef4444; box-shadow: 0 0 0 4px rgba(239,68,68,0.16); }}
.schip .sname {{ font-size: 0.66rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
.schip .sval  {{ margin-left: auto; font-size: 1.02rem; font-weight: 800; color: var(--text); font-variant-numeric: tabular-nums; }}
.schip .sunit {{ font-size: 0.7rem; color: var(--muted); font-weight: 600; margin-left: 2px; }}
.schip .spark {{ margin-top: 5px; height: 28px; }}
.schip.bad {{ border-color: #f3c4be; background: #fdeeec; }}
.floor-diag {{ font-size: 0.78rem; color: #b91c1c; font-weight: 600; margin-top: 8px; }}
@keyframes floorpulse {{
  0%   {{ box-shadow: inset 0 0 0 0 rgba(239,68,68,0); }}
  50%  {{ box-shadow: inset 0 0 60px 0 rgba(239,68,68,0.14); }}
  100% {{ box-shadow: inset 0 0 0 0 rgba(239,68,68,0); }}
}}
.floor.crit {{ animation: floorpulse 1.7s ease-in-out infinite; }}
.livedot {{
  width: 9px; height: 9px; border-radius: 50%; background: #16a34a;
  display: inline-block; margin-right: 7px; animation: livepulse 1.4s infinite;
}}
@keyframes livepulse {{
  0%   {{ box-shadow: 0 0 0 0 rgba(22,163,74,0.5); }}
  70%  {{ box-shadow: 0 0 0 9px rgba(22,163,74,0); }}
  100% {{ box-shadow: 0 0 0 0 rgba(22,163,74,0); }}
}}

/* --- building: exterior windows (cross-section facade) ------------- */
.facade {{
  width: 42px; flex: 0 0 42px; display: grid;
  grid-template-columns: 1fr 1fr; gap: 5px; align-content: center;
  padding-left: 8px; border-left: 1px dashed var(--border);
}}
.facade .win {{ aspect-ratio: 1 / 1; border-radius: 2px; background: #c3d4f5; }}
.facade .win.lit  {{ background: #fde68a; box-shadow: inset 0 0 3px rgba(180,130,0,0.25); }}
.facade .win.crit {{ background: #fca5a5; }}

/* --- building: top-down floor plan -------------------------------- */
.plan {{
  max-width: 940px; margin: 0 auto; padding: 18px;
  border: 2px solid #c7ced9; border-radius: 16px; position: relative;
  background: linear-gradient(180deg, #fbfcfe, #eef2f9);
}}
.plan-compass {{
  position: absolute; top: 12px; right: 18px; font-size: 0.7rem;
  font-weight: 800; color: var(--muted); letter-spacing: 0.1em;
}}
.plan-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(255px, 1fr)); gap: 14px; }}
.plan-room {{
  border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px;
  background: var(--surface); position: relative; overflow: hidden;
}}
.room-windows {{ display: flex; gap: 6px; justify-content: center; margin-bottom: 12px; }}
.rwin {{ width: 18px; height: 8px; border-radius: 2px; background: #c3d4f5; }}
.rwin.lit  {{ background: #fde68a; }}
.rwin.crit {{ background: #fca5a5; }}
.room-name {{ font-size: 1.2rem; font-weight: 800; color: var(--text); }}
.room-fn {{ font-size: 0.78rem; color: var(--muted); margin: 2px 0 9px 0; }}
.room-metrics {{ margin-top: 11px; display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }}
.pm {{ font-size: 0.82rem; color: var(--text2); display: flex; align-items: center; gap: 6px; }}
.pm .pmdot {{ width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }}
.pm.ok .pmdot  {{ background: #16a34a; }}
.pm.bad .pmdot {{ background: #ef4444; box-shadow: 0 0 0 3px rgba(239,68,68,0.15); }}
.pm.bad {{ color: #b91c1c; font-weight: 700; }}
.plan-room.crit {{ animation: floorpulse 1.7s ease-in-out infinite; }}

/* --- hide chrome (minimal — never touch the header or sidebar controls,
       so Streamlit's native collapse/expand arrow keeps working) ------- */
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────── HTTP helpers
def _get(path: str, **params) -> dict:
    try:
        r = httpx.get(f"{PIPELINE.collector_url}{path}", params=params, timeout=15.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as exc:
        st.error(f"GET {path} failed: {exc}")
        return {}


def _post(path: str, json: dict | None = None, **params) -> dict:
    try:
        r = httpx.post(f"{PIPELINE.collector_url}{path}", json=json, params=params, timeout=15.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as exc:
        st.error(f"POST {path} failed: {exc}")
        return {}


def _pill(kind: str, label: str) -> str:
    return (f"<span class='pill pill-{kind}'>"
            f"<span class='pill-dot'></span>{label}</span>")


# ──────────────────────────────────────────────────────────── app bar
def _app_bar(stats: dict) -> None:
    worker = stats.get("worker") or {}
    running = worker.get("running")
    n_zones = len(stats.get("zones", {})) or len(ZONE_NAMES)
    decider_pill = _pill("ok" if running else "muted",
                         t("decider_online") if running else t("decider_idle"))
    err = worker.get("last_error")
    error_pill = _pill("crit", t("worker_error")) if err else _pill("ok", t("all_ok"))
    st.markdown(
        f"""
        <div class='appbar'>
          <div class='appbar-brand'>
            <div class='appbar-logo'>◆</div>
            <div>
              <div class='appbar-title'>BEMS · Anomaly Operations Center</div>
              <div class='appbar-sub'>{t('appbar_sub', n=n_zones)}</div>
            </div>
          </div>
          <div class='appbar-status'>
            {error_pill}{decider_pill}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ───────────────────────────────────────────────────────────── sidebar
def _sidebar() -> dict:
    st.sidebar.markdown(
        f"<div style='padding:8px 4px 14px 4px; border-bottom:1px solid {C_BORDER};'>"
        f"<div style='font-size:1.05rem; font-weight:800; color:{C_TEXT}; letter-spacing:-0.01em;'>BEMS Console</div>"
        f"<div style='font-size:0.76rem; color:{C_MUTED}; margin-top:2px;'>{t('console_sub')}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # language selector — sets st.session_state['lang'] for the whole run
    lang_choice = st.sidebar.radio(
        t("lang_label"), ["English", "한국어"],
        index=0 if _lang() == "en" else 1,
        horizontal=True, key="lang_radio",
    )
    st.session_state["lang"] = "ko" if lang_choice == "한국어" else "en"

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:600; margin:14px 0 6px 0;'>{t('sec_refresh')}</div>",
        unsafe_allow_html=True,
    )
    auto = st.sidebar.toggle(t("auto_refresh"), value=True, label_visibility="collapsed")
    refresh = st.sidebar.slider(t("interval"), 2.0, 15.0, 4.0, 0.5,
                                label_visibility="collapsed")
    st.sidebar.caption(t("refresh_on", s=f"{refresh:.1f}") if auto
                       else t("refresh_off", s=f"{refresh:.1f}"))

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:600; margin:18px 0 6px 0;'>{t('sec_admin')}</div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button(t("reset_btn"), use_container_width=True):
        _post("/reset")
        st.sidebar.success(t("reset_done"))
        time.sleep(0.4)

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:600; margin:18px 0 6px 0;'>{t('sec_thresholds')}</div>",
        unsafe_allow_html=True,
    )
    for spec in SENSORS.values():
        lo = "—" if spec.anomaly_low is None else f"{spec.anomaly_low}"
        hi = "—" if spec.anomaly_high is None else f"{spec.anomaly_high}"
        st.sidebar.markdown(
            f"<div style='font-size:0.8rem; padding:6px 0; border-bottom:1px solid {C_BORDER};'>"
            f"<div style='font-weight:600; color:{C_TEXT};'>{spec.name}</div>"
            f"<div style='display:flex; gap:8px; margin-top:2px; font-size:0.76rem;'>"
            f"<span style='color:{C_OK};'>● {spec.normal_min}–{spec.normal_max}{spec.unit}</span>"
            f"<span style='color:{C_CRIT};'>● &lt;{lo} / &gt;{hi}</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.sidebar.markdown(
        f"<div style='margin-top:18px; font-size:0.72rem; color:{C_MUTED}; "
        f"padding:8px 4px; border-top:1px solid {C_BORDER};'>"
        f"Collector · <code style='font-size:0.72rem;'>{PIPELINE.collector_url}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )
    return {"auto": auto, "refresh": refresh}


# ────────────────────────────────────────────────── shared chart styler
def _style_axes(fig: go.Figure, height: int = 300) -> go.Figure:
    fig.update_layout(
        height=height,
        margin={"l": 54, "r": 18, "t": 34, "b": 34},
        paper_bgcolor="white", plot_bgcolor="white",
        font={"color": C_TEXT, "family": "-apple-system, sans-serif", "size": 12},
        xaxis={"gridcolor": PLOT["grid"], "linecolor": PLOT["axis"],
               "zeroline": False, "showspikes": True, "spikecolor": "#cbd5e1",
               "spikedash": "dot", "spikethickness": 1, "ticks": "outside",
               "tickcolor": PLOT["axis"], "ticklen": 4},
        yaxis={"gridcolor": PLOT["grid"], "linecolor": PLOT["axis"], "zeroline": False,
               "ticks": "outside", "tickcolor": PLOT["axis"], "ticklen": 4},
        legend={"orientation": "h", "y": -0.22, "x": 0, "bgcolor": "rgba(0,0,0,0)",
                "font": {"size": 11}},
    )
    return fig


def _yrange(values, spec, pad_frac: float = 0.14):
    """Padded y-range that always includes the sensor's thresholds."""
    import numpy as np
    vals = [float(v) for v in values
            if v is not None and not (isinstance(v, float) and np.isnan(v))]
    his = [*vals, spec.normal_max]
    los = [*vals, spec.normal_min]
    if spec.anomaly_high is not None:
        his.append(spec.anomaly_high)
    if spec.anomaly_low is not None:
        los.append(spec.anomaly_low)
    hi, lo = max(his), min(los)
    span = (hi - lo) or 1.0
    return lo - span * pad_frac, hi + span * pad_frac


# ─────────────────────────────────────────────────── tab: Operations
def tab_operations(stats: dict, decisions: list[dict]) -> None:
    zones = stats.get("zones", {}) or {}
    worker = stats.get("worker") or {}

    crit = sum(1 for d in decisions if d.get("severity") == "Critical")
    warn = sum(1 for d in decisions if d.get("severity") == "Warning")
    total_received = sum(z.get("received", 0) for z in zones.values())
    total_missing = sum(z.get("missing", 0) for z in zones.values())
    avg_loss = (total_missing / max(sum(z.get("expected", 0) for z in zones.values()), 1)) * 100

    k = st.columns(6)
    k[0].metric(t("kpi_zones"), len(zones))
    k[1].metric(t("kpi_received"), f"{total_received:,}")
    k[2].metric(t("kpi_loss"), f"{avg_loss:.1f}%")
    k[3].metric(t("kpi_decisions"), worker.get("decisions_made", 0))
    k[4].metric(t("kpi_critical"), crit)
    k[5].metric(t("kpi_warning"), warn)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1, 1.2], gap="large")

    with left:
        st.markdown(f"<div class='section-title'>{t('sys_services')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-sub'>{t('sys_services_sub')}</div>", unsafe_allow_html=True)
        last_tick = worker.get("last_tick")
        last_tick_str = (datetime.fromtimestamp(last_tick).strftime("%H:%M:%S")
                         if last_tick else "—")
        services = [
            ("Generator",    t("svc_generator"),   "ok" if stats.get("total_truth", 0) > 0 else "muted"),
            ("Transmitter",  t("svc_transmitter"), "ok" if total_received > 0 else "muted"),
            ("Collector",    f"FastAPI · {PIPELINE.collector_url}", "ok"),
            ("ML Processor", t("svc_ml"),          "ok" if worker.get("decisions_made", 0) > 0 else "muted"),
            ("Decision",     t("svc_decision_rule", t=last_tick_str),
                             "crit" if worker.get("last_error") else
                             ("ok" if worker.get("running") else "muted")),
            ("Dashboard",    t("svc_dashboard"),   "ok"),
        ]
        status_label = {"ok": t("st_operational"), "muted": t("st_idle"), "crit": t("st_error")}
        rows_html = "".join(
            f"<tr><td><b>{n}</b></td><td><code>{d}</code></td>"
            f"<td style='text-align:right;'>{_pill(s, status_label[s])}</td></tr>"
            for n, d, s in services
        )
        st.markdown(
            f"<table class='svc-table'>"
            f"<thead><tr><th>{t('col_service')}</th><th>{t('col_description')}</th>"
            f"<th style='text-align:right;'>{t('col_status')}</th></tr></thead>"
            f"<tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )
        if worker.get("last_error"):
            st.markdown(
                f"<div style='margin-top:10px; padding:10px 14px; background:{C_CRIT_BG}; "
                f"border:1px solid #f3c4be; border-radius:6px; color:{C_CRIT}; font-size:0.85rem;'>"
                f"<b>{t('worker_error_label')}</b> {worker['last_error']}</div>",
                unsafe_allow_html=True,
            )

    with right:
        hdr_l, hdr_r = st.columns([3, 1])
        with hdr_l:
            st.markdown(f"<div class='section-title'>{t('dt_title')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-sub'>{t('dt_sub')}</div>", unsafe_allow_html=True)
        with hdr_r:
            show_normal = st.toggle(t("show_normal"), value=False, key="ops_show_normal",
                                    help=t("show_normal_help"))

        if not decisions:
            st.info(t("awaiting_decision"))
        else:
            df = pd.DataFrame(decisions)
            df["time"] = pd.to_datetime(df["decided_at"], unit="s")
            df = df.head(200)

            n_crit = int((df["severity"] == "Critical").sum())
            n_warn = int((df["severity"] == "Warning").sum())
            n_norm = int((df["severity"] == "Normal").sum())
            st.markdown(
                f"<div style='margin: 4px 0 8px 0; display:flex; gap:8px; flex-wrap:wrap; align-items:center;'>"
                f"{_pill('crit', f'{n_crit} CRITICAL')}"
                f"{_pill('warn', f'{n_warn} WARNING')}"
                f"{_pill('ok',   f'{n_norm} NORMAL')}"
                f"<span style='color:{C_MUTED}; font-size:0.8rem;'>{t('window_last', n=len(df))}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            fig = go.Figure()
            zones_order = sorted(df["zone"].unique())
            layers = [
                ("Normal",   {"size": 6,  "opacity": 0.30, "symbol": "circle", "line": {"width": 0}}),
                ("Warning",  {"size": 14, "opacity": 0.95, "symbol": "diamond", "line": {"width": 1.5, "color": "white"}}),
                ("Critical", {"size": 18, "opacity": 1.00, "symbol": "star", "line": {"width": 1.8, "color": "#5a1610"}}),
            ]
            for sev, marker in layers:
                if sev == "Normal" and not show_normal:
                    continue
                sub = df[df["severity"] == sev]
                if sub.empty:
                    continue
                fig.add_trace(go.Scatter(
                    x=sub["time"], y=sub["zone"], mode="markers",
                    name=f"{sev} · {len(sub)}",
                    marker={**marker, "color": SEVERITY_COLOR[sev]},
                    customdata=sub[["severity", "seq", "detector", "diagnosis"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b>  ·  %{y}<br>"
                        "seq <b>%{customdata[1]}</b>  ·  %{x|%H:%M:%S}<br>"
                        "detector: %{customdata[2]}<br>"
                        "<i>%{customdata[3]}</i><extra></extra>"
                    ),
                ))

            _style_axes(fig, height=320)
            fig.update_layout(
                yaxis={"title": "", "categoryorder": "array",
                       "categoryarray": zones_order[::-1],
                       "tickfont": {"size": 12, "color": C_TEXT}, "showgrid": False},
                xaxis={"title": "", "tickformat": "%H:%M:%S",
                       "showgrid": True, "gridcolor": "#f1f3f5"},
                legend={"orientation": "h", "y": 1.10, "x": 0, "bgcolor": "rgba(0,0,0,0)",
                        "font": {"size": 11, "color": C_TEXT}, "itemclick": "toggleothers"},
                margin={"l": 70, "r": 20, "t": 50, "b": 30},
                hoverlabel={"bgcolor": "white", "bordercolor": C_BORDER,
                            "font": {"color": C_TEXT, "size": 12}},
            )
            for i in range(len(zones_order) - 1):
                fig.add_hline(y=i + 0.5, line={"color": "#f1f3f5", "width": 1}, layer="below")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption(t("dt_caption"))

    st.markdown(f"<br><div class='section-title'>{t('zone_status')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-sub'>{t('zone_status_sub')}</div>", unsafe_allow_html=True)
    if not zones:
        st.info(t("no_telemetry"))
        return
    cols = st.columns(len(zones), gap="large")
    for col, (zone, zs) in zip(cols, zones.items()):
        loss_pct = zs.get("packet_loss_rate", 0.0) * 100
        loss_kind = "ok" if loss_pct < 8 else ("warn" if loss_pct < 18 else "crit")
        with col:
            label = ZONES.get(zone, {}).get("label", "")
            st.markdown(
                f"""
                <div class='card'>
                  <div class='card-head'>
                    <div>
                      <div class='card-title'>{zone}</div>
                      <div class='card-sub'>{label}</div>
                    </div>
                    {_pill(loss_kind, t('loss_suffix', p=f'{loss_pct:.1f}'))}
                  </div>
                  <div class='card-row'><span class='k'>{t('z_received')}</span> <span class='v'>{zs.get('received',0):,}</span></div>
                  <div class='card-row'><span class='k'>{t('z_expected')}</span> <span class='v'>{zs.get('expected',0):,}</span></div>
                  <div class='card-row'><span class='k'>{t('z_missing')}</span>  <span class='v'>{zs.get('missing',0):,}</span></div>
                  <div class='card-row'><span class='k'>{t('z_seq_range')}</span><span class='v'>{zs.get('first_seq')} → {zs.get('last_seq')}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────── tab: Telemetry
def _sensor_chart(name: str, raw_df: pd.DataFrame, proc_df: pd.DataFrame,
                  show_raw: bool = True) -> go.Figure:
    spec = SENSORS[name]
    fig = go.Figure()

    all_vals = []
    if not proc_df.empty:
        all_vals += proc_df[name].tolist()
    if show_raw and not raw_df.empty and name in raw_df.columns:
        all_vals += raw_df[name].tolist()
    ymin, ymax = _yrange(all_vals, spec)

    if spec.anomaly_high is not None:
        fig.add_hrect(y0=spec.anomaly_high, y1=ymax, fillcolor=C_CRIT,
                      opacity=0.05, line_width=0, layer="below")
    if spec.anomaly_low is not None:
        fig.add_hrect(y0=ymin, y1=spec.anomaly_low, fillcolor=C_CRIT,
                      opacity=0.05, line_width=0, layer="below")
    fig.add_hrect(y0=spec.normal_min, y1=spec.normal_max, fillcolor=PLOT["normal_band"],
                  opacity=0.08, line_width=0, layer="below",
                  annotation_text=t("lk_normal"), annotation_position="top left",
                  annotation_font={"size": 9, "color": C_OK})

    if spec.anomaly_high is not None:
        fig.add_hline(y=spec.anomaly_high, line_dash="dot", line_color=C_CRIT, line_width=1, opacity=0.6)
    if spec.anomaly_low is not None:
        fig.add_hline(y=spec.anomaly_low, line_dash="dot", line_color=C_CRIT, line_width=1, opacity=0.6)

    if show_raw and not raw_df.empty and name in raw_df.columns:
        fig.add_trace(go.Scatter(
            x=raw_df["seq"], y=raw_df[name], mode="markers", name="Raw",
            marker={"color": PLOT["raw"], "size": 4.5, "opacity": 0.5},
            hovertemplate="seq %{x} · raw %{y:.2f}" + spec.unit + "<extra></extra>",
        ))

    if not proc_df.empty:
        fig.add_trace(go.Scatter(
            x=proc_df["seq"], y=proc_df[name], mode="lines", name=t("lk_signal"),
            line={"color": PLOT["interp"], "width": 2.4, "shape": "spline"},
            fill="tozeroy", fillcolor="rgba(31,93,222,0.06)",
            hovertemplate="seq %{x} · %{y:.2f}" + spec.unit + "<extra></extra>",
        ))
        if "was_missing" in proc_df.columns:
            rec = proc_df[proc_df["was_missing"] == True]   # noqa: E712
            if not rec.empty:
                fig.add_trace(go.Scatter(
                    x=rec["seq"], y=rec[name], mode="markers", name=t("lk_recovered"),
                    marker={"color": "white", "size": 8, "symbol": "diamond",
                            "line": {"width": 1.6, "color": PLOT["interp"]}},
                    hovertemplate="seq %{x} · interp %{y:.2f}" + spec.unit + "<extra></extra>",
                ))
        z_an = proc_df[proc_df[f"{name}_anom"] == True]   # noqa: E712
        if not z_an.empty:
            fig.add_trace(go.Scatter(
                x=z_an["seq"], y=z_an[name], mode="markers", name=t("lk_zscore"),
                marker={"color": C_CRIT, "size": 11, "symbol": "x",
                        "line": {"width": 2.2, "color": C_CRIT}},
                hovertemplate="seq %{x} · ANOMALY %{y:.2f}" + spec.unit + "<extra></extra>",
            ))
        if_an = proc_df[proc_df["iforest_anom"] == True]  # noqa: E712
        if not if_an.empty:
            fig.add_trace(go.Scatter(
                x=if_an["seq"], y=if_an[name], mode="markers", name=t("lk_iforest"),
                marker={"color": C_ACCENT, "size": 12, "symbol": "circle-open",
                        "line": {"width": 2.2}},
                hovertemplate="seq %{x} · IForest %{y:.2f}" + spec.unit + "<extra></extra>",
            ))
        last = proc_df.iloc[-1]
        last_anom = bool(last.get(f"{name}_anom") or last.get("iforest_anom"))
        dot_color = C_CRIT if last_anom else C_OK
        fig.add_trace(go.Scatter(
            x=[last["seq"]], y=[last[name]], mode="markers",
            marker={"color": dot_color, "size": 11, "line": {"width": 2, "color": "white"}},
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_annotation(
            x=last["seq"], y=last[name], text=f"<b>{last[name]:.1f}</b>",
            showarrow=False, xanchor="left", xshift=10,
            font={"size": 11, "color": dot_color}, bgcolor="white",
            bordercolor=dot_color, borderwidth=1, borderpad=2,
        )

    fig.update_layout(
        title={"text": f"<b>{name.title()}</b> <span style='color:{C_MUTED};font-weight:400;'>· {spec.unit}</span>",
               "font": {"size": 14, "color": C_TEXT}, "x": 0.01, "y": 0.96},
        hovermode="x unified",
        hoverlabel={"bgcolor": "white", "bordercolor": C_BORDER, "font": {"size": 11}},
    )
    fig.update_yaxes(title_text="", range=[ymin, ymax])
    fig.update_xaxes(title_text="sequence")
    _style_axes(fig, height=320)
    fig.update_layout(margin={"l": 54, "r": 46, "t": 46, "b": 38})
    return fig


def tab_telemetry(zones_seen: list[str]) -> None:
    if not zones_seen:
        st.info(t("no_telemetry_arrived"))
        return
    bar = st.columns([1.4, 1.2, 2.4])
    with bar[0]:
        zone = st.selectbox(t("sel_zone"), zones_seen, key="tel_zone")
    with bar[1]:
        show_raw = st.toggle(t("tel_show_raw"), value=True, key="tel_show_raw",
                             help=t("tel_show_raw_help"))
    raw = _get("/raw", zone=zone, last_n=200)
    proc = _get("/processed", zone=zone, last_n=200)

    raw_df = pd.DataFrame(raw.get("records", []))
    proc_df = pd.DataFrame(proc.get("records", []))

    k = st.columns(4)
    k[0].metric(t("tel_raw_points"), len(raw_df))
    k[1].metric(t("tel_recovered_rows"), len(proc_df))
    k[2].metric(t("tel_dropped"), len(raw.get("missing_seqs", [])))
    n_anom = int(proc_df.get("anomaly_any", pd.Series(dtype=bool)).sum()) if not proc_df.empty else 0
    k[3].metric(t("tel_flagged"), n_anom)

    missing = raw.get("missing_seqs", [])
    if missing:
        st.markdown(
            f"<div style='margin-top:14px; padding:10px 14px; background:{C_WARN_BG}; "
            f"border:1px solid #f3d9a8; border-radius:6px; color:{C_WARN}; font-size:0.85rem;'>"
            f"{t('packet_loss_banner', n=len(missing))}"
            f"<code style='background:white; color:{C_WARN};'>{missing[-20:]}</code></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='margin:14px 0 6px 0; display:flex; gap:18px; flex-wrap:wrap; "
        f"font-size:0.78rem; color:{C_TEXT2};'>"
        f"<span><span style='display:inline-block;width:18px;height:3px;background:{C_PRIMARY};"
        f"vertical-align:middle;margin-right:5px;'></span>{t('lk_signal')}</span>"
        f"<span><span style='color:{C_PRIMARY};'>◇</span> {t('lk_recovered')}</span>"
        f"<span><span style='color:{C_CRIT};'>✕</span> {t('lk_zscore')}</span>"
        f"<span><span style='color:{C_ACCENT};'>○</span> {t('lk_iforest')}</span>"
        f"<span><span style='display:inline-block;width:12px;height:10px;"
        f"background:{PLOT['normal_band']};opacity:0.25;vertical-align:middle;margin-right:4px;'></span>"
        f"{t('lk_normal')}</span>"
        f"<span><span style='display:inline-block;width:12px;height:10px;"
        f"background:{C_CRIT};opacity:0.18;vertical-align:middle;margin-right:4px;'></span>"
        f"{t('lk_danger')}</span></div>",
        unsafe_allow_html=True,
    )

    per_row = st.radio(t("charts_per_row"), [1, 2], index=1, horizontal=True,
                       key="tel_per_row", help=t("charts_per_row_help"))
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    height = 360 if per_row == 1 else 320
    if per_row == 1:
        for name in SENSOR_NAMES:
            fig = _sensor_chart(name, raw_df, proc_df, show_raw=show_raw)
            fig.update_layout(showlegend=False, height=height)
            st.plotly_chart(fig, use_container_width=True, key=f"tel_{zone}_{name}",
                            config={"displayModeBar": False})
    else:
        for i in range(0, len(SENSOR_NAMES), 2):
            cols = st.columns(2, gap="large")
            for j, col in enumerate(cols):
                if i + j >= len(SENSOR_NAMES):
                    continue
                name = SENSOR_NAMES[i + j]
                with col:
                    fig = _sensor_chart(name, raw_df, proc_df, show_raw=show_raw)
                    fig.update_layout(showlegend=False, height=height)
                    st.plotly_chart(fig, use_container_width=True,
                                    key=f"tel_{zone}_{name}",
                                    config={"displayModeBar": False})


# ─────────────────────────────────────────────────── tab: Pipeline
AGENT_CARDS = [
    ("01", "Generator",    "src/agents/generator.py",    "role_generator"),
    ("02", "Transmitter",  "src/agents/transmitter.py",  "role_transmitter"),
    ("03", "Collector",    "src/agents/collector.py",    "role_collector"),
    ("04", "ML Processor", "src/agents/ml_processor.py", "role_ml"),
    ("05", "Decision",     "src/agents/decision.py",     "role_decision"),
    ("06", "Dashboard",    "dashboard/app.py",           "role_dashboard"),
]


def tab_pipeline(stats: dict, decisions: list[dict]) -> None:
    zones = stats.get("zones", {}) or {}
    worker = stats.get("worker") or {}
    received = sum(z.get("received", 0) for z in zones.values())
    missing = sum(z.get("missing", 0) for z in zones.values())
    last_dec = decisions[0]["decided_at"] if decisions else None
    last_dec_h = datetime.fromtimestamp(last_dec).strftime("%H:%M:%S") if last_dec else "—"

    kpis = {
        "Generator":    {"k1": (t("kp_truth_rows"), f"{stats.get('total_truth', 0):,}"),
                         "k2": (t("kp_cadence"),    f"{PIPELINE.sample_interval_s:.1f}s")},
        "Transmitter":  {"k1": (t("kp_received"),   f"{received:,}"),
                         "k2": (t("kp_dropped"),    f"{missing:,}")},
        "Collector":    {"k1": (t("kp_zones"),      f"{len(zones)}"),
                         "k2": (t("kp_database"),   PIPELINE.db_path.split('/')[-1])},
        "ML Processor": {"k1": (t("kp_window"),     t("win_rows", n=PIPELINE.window_size)),
                         "k2": (t("kp_zthr"),       f"{PIPELINE.zscore_threshold}")},
        "Decision":     {"k1": (t("kp_decisions"),  f"{worker.get('decisions_made', 0):,}"),
                         "k2": (t("kp_last_tick"),  last_dec_h)},
        "Dashboard":    {"k1": (t("kp_refresh"),    t("render_live")),
                         "k2": (t("kp_render"),     "Streamlit + Plotly")},
    }
    status_kind = {
        "Generator":    "ok" if stats.get("total_truth", 0) > 0 else "muted",
        "Transmitter":  "ok" if received > 0 else "muted",
        "Collector":    "ok",
        "ML Processor": "ok" if worker.get("decisions_made", 0) > 0 else "muted",
        "Decision":     "crit" if worker.get("last_error") else ("ok" if worker.get("running") else "muted"),
        "Dashboard":    "ok",
    }
    status_label = {"ok": t("st_operational"), "muted": t("st_idle"), "crit": t("st_error")}

    st.markdown(f"<div class='section-title'>{t('agent_topology')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-sub'>{t('agent_topology_sub')}</div>", unsafe_allow_html=True)

    for i in (0, 2, 4):
        cols = st.columns(2, gap="large")
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(AGENT_CARDS):
                continue
            num, name, path, role_key = AGENT_CARDS[idx]
            kind = status_kind.get(name, "muted")
            k1 = kpis[name]["k1"]; k2 = kpis[name]["k2"]
            with col:
                st.markdown(
                    f"""
                    <div class='card' style='margin-bottom:12px;'>
                      <div class='card-head'>
                        <div style='display:flex; align-items:center; gap:10px;'>
                          <span style='font-family:ui-monospace,monospace; font-size:0.78rem;
                                       color:{C_PRIMARY}; background:{C_PRIMARY_BG};
                                       padding:3px 8px; border-radius:4px; font-weight:700;'>{num}</span>
                          <span class='card-title'>{name}</span>
                        </div>
                        {_pill(kind, status_label.get(kind, kind))}
                      </div>
                      <div style='color:{C_TEXT2}; font-size:0.86rem; line-height:1.5; margin:8px 0 12px 0;'>{t(role_key)}</div>
                      <div style='display:flex; gap:12px;'>
                        <div style='flex:1; padding:8px 12px; background:{C_SURFACE2}; border-radius:6px;'>
                          <div style='font-size:0.68rem; color:{C_MUTED}; text-transform:uppercase; letter-spacing:0.06em; font-weight:600;'>{k1[0]}</div>
                          <div style='font-size:1.05rem; color:{C_TEXT}; font-weight:700; font-variant-numeric:tabular-nums;'>{k1[1]}</div>
                        </div>
                        <div style='flex:1; padding:8px 12px; background:{C_SURFACE2}; border-radius:6px;'>
                          <div style='font-size:0.68rem; color:{C_MUTED}; text-transform:uppercase; letter-spacing:0.06em; font-weight:600;'>{k2[0]}</div>
                          <div style='font-size:1.05rem; color:{C_TEXT}; font-weight:700; font-variant-numeric:tabular-nums;'>{k2[1]}</div>
                        </div>
                      </div>
                      <div style='font-size:0.74rem; color:{C_MUTED}; margin-top:10px;'>
                        {t('source_label')}: <code style='background:{C_SURFACE2}; padding:2px 6px; border-radius:4px;'>{path}</code>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────── tab: Alerts
def tab_alerts(decisions: list[dict]) -> None:
    if not decisions:
        st.info(t("no_alerts"))
        return

    df = pd.DataFrame(decisions)
    df["time"] = pd.to_datetime(df["decided_at"], unit="s")

    k = st.columns(4)
    k[0].metric(t("al_total"), len(df))
    k[1].metric(t("al_critical"), int((df["severity"] == "Critical").sum()))
    k[2].metric(t("al_warning"), int((df["severity"] == "Warning").sum()))
    k[3].metric(t("al_normal"), int((df["severity"] == "Normal").sum()))

    st.markdown("<br>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1.5, 1.5, 1])
    sev_filter = f1.multiselect(t("f_severity"), ["Critical", "Warning", "Normal"],
                                default=["Critical", "Warning"], key="sev_filter")
    zone_filter = f2.multiselect(t("f_zone"), sorted(df["zone"].unique().tolist()),
                                 default=sorted(df["zone"].unique().tolist()), key="zone_filter")
    limit = f3.slider(t("f_max_rows"), 10, 200, 50, 10, key="alerts_limit")

    filt = df[df["severity"].isin(sev_filter) & df["zone"].isin(zone_filter)].head(limit)
    if filt.empty:
        st.caption(t("no_match"))
        return

    csv_buf = io.StringIO()
    filt[["time", "zone", "seq", "severity", "diagnosis", "action",
          "detector", "alert"]].to_csv(csv_buf, index=False)
    st.download_button(t("export_csv"), csv_buf.getvalue(),
                       file_name="bems_alerts.csv", mime="text/csv")

    st.markdown("<br>", unsafe_allow_html=True)
    for _, rec in filt.iterrows():
        sev = rec["severity"]
        color = SEVERITY_COLOR.get(sev, C_MUTED)
        ts = datetime.fromtimestamp(rec["decided_at"]).strftime("%H:%M:%S")
        date = datetime.fromtimestamp(rec["decided_at"]).strftime("%Y-%m-%d")
        chips = " ".join(
            f"<span class='pill pill-muted' style='font-size:0.7rem;'>"
            f"{tt['sensor']} = {tt['value']}{tt['unit']} (z={tt['z']})</span>"
            for tt in (rec.get("triggered") or [])
        )
        kind = {"Critical": "crit", "Warning": "warn", "Normal": "ok"}.get(sev, "muted")
        st.markdown(
            f"""
            <div class='alert-row' style='border-left-color:{color};'>
              <div class='alert-meta-col'>
                <div class='time'>{ts}</div>
                <div>{date}</div>
              </div>
              <div class='alert-meta-col'>
                {_pill(kind, sev)}
                <div><code>{rec['zone']}</code></div>
                <div>seq <code>{rec['seq']}</code></div>
              </div>
              <div class='alert-meta-col'>
                <div style='color:{C_MUTED};'>{t('detector')}</div>
                <div><code>{rec.get('detector','—')}</code></div>
              </div>
              <div>
                <div class='alert-diag'>{rec.get('diagnosis','—')}</div>
                <div class='alert-action'><b>{t('rec_action')}</b> {rec.get('action','—')}</div>
                <div class='alert-evidence'>{chips}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────── tab: Scenario Lab
def _classify_value(name: str, v: float) -> str:
    """'crit' if past a hard limit, 'warn' if outside comfort, else 'ok'."""
    spec = SENSORS[name]
    if spec.anomaly_high is not None and v > spec.anomaly_high:
        return "crit"
    if spec.anomaly_low is not None and v < spec.anomaly_low:
        return "crit"
    if v < spec.normal_min or v > spec.normal_max:
        return "warn"
    return "ok"


def _predict_severity(readings: dict) -> str:
    """Mirror the Decision Agent's hard-threshold rule for an instant preview."""
    for name, v in readings.items():
        spec = SENSORS[name]
        if spec.anomaly_high is not None and v > spec.anomaly_high:
            return "Critical"
        if spec.anomaly_low is not None and v < spec.anomaly_low:
            return "Critical"
    return "Normal"


def _result_card(zone: str, seq: int) -> None:
    """Show the decision the pipeline produced for a just-injected sample."""
    recs = _get("/decisions", zone=zone, last_n=20).get("records", [])
    match = next((r for r in recs if r.get("seq") == seq), None)
    if not match:
        st.markdown(
            f"<div style='padding:12px 16px; background:{C_SURFACE2}; border:1px solid {C_BORDER}; "
            f"border-radius:8px; color:{C_MUTED}; font-size:0.88rem;'>⏳ {t('result_wait')}</div>",
            unsafe_allow_html=True)
        return
    sev = match["severity"]
    color = SEVERITY_COLOR.get(sev, C_MUTED)
    kind = {"Critical": "crit", "Warning": "warn", "Normal": "ok"}.get(sev, "ok")
    chips = " ".join(
        f"<span class='pill pill-muted' style='font-size:0.7rem;'>"
        f"{tt['sensor']}={tt['value']}{tt['unit']} (z={tt['z']})</span>"
        for tt in (match.get("triggered") or [])
    )
    st.markdown(
        f"<div style='padding:14px 18px; background:{C_SURFACE}; border:1px solid {C_BORDER}; "
        f"border-left:5px solid {color}; border-radius:10px; box-shadow:0 1px 2px rgba(9,30,66,0.05);'>"
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:700;'>{t('result_title')} · {zone} · seq {seq}</div>"
        f"<div style='margin:6px 0;'>{_pill(kind, sev)} "
        f"<b style='color:{C_TEXT};'>{match.get('diagnosis','—')}</b></div>"
        f"<div style='color:{C_TEXT2}; font-size:0.86rem; margin-bottom:6px;'>"
        f"<b>{t('rec_action')}</b> {match.get('action','—')}</div>"
        f"<div>{chips}</div></div>",
        unsafe_allow_html=True,
    )


def tab_scenario_lab(scenarios_resp: dict, zones_seen: list[str]) -> None:
    st.markdown(f"<div class='section-title'>{t('ci_title')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-sub'>{t('ci_sub')}</div>", unsafe_allow_html=True)

    scenarios = scenarios_resp.get("scenarios", [])
    zones_for_inject = ZONE_NAMES

    # ── result of the most recent injection, shown right at the top
    last = st.session_state.get("lab_last_inject")
    if last:
        _result_card(last["zone"], last["seq"])
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-weight:700; color:{C_TEXT}; margin:4px 0 10px 0; font-size:0.92rem;'>"
        f"1 · {t('preset_scenarios')}</div>", unsafe_allow_html=True)

    rows = [scenarios[i:i + 3] for i in range(0, len(scenarios), 3)]
    for row in rows:
        cols = st.columns(3, gap="large")
        for col, sc in zip(cols, row):
            with col:
                st.markdown(
                    f"""
                    <div class='preset'>
                      <div class='preset-id'>{sc['tag']}</div>
                      <div class='preset-name'>{sc['label']}</div>
                      <div class='preset-desc'>{sc['description']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                zone = st.selectbox(t("target_zone"), zones_for_inject,
                                    key=f"inj_zone_{sc['tag']}", label_visibility="collapsed")
                if st.button(t("inject_into", zone=zone), key=f"inj_btn_{sc['tag']}",
                             use_container_width=True, type="primary"):
                    res = _post("/inject", json={
                        "zone": zone, "scenario": sc["tag"], "label_as_anomaly": True})
                    if res.get("ok"):
                        st.session_state["lab_last_inject"] = {
                            "zone": zone, "seq": res.get("seq")}
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-weight:700; color:{C_TEXT}; margin:4px 0 4px 0; font-size:0.92rem;'>"
        f"2 · {t('custom_sample')}</div>", unsafe_allow_html=True)

    cz, cl = st.columns([1, 1])
    zone = cz.selectbox(t("sel_zone"), zones_for_inject, key="manual_zone")
    label = cl.checkbox(t("label_anomaly"), value=True)

    SLIDER = {
        "power":       (0.0, 16.0, 2.5, 0.1),
        "temperature": (0.0, 50.0, 23.0, 0.5),
        "humidity":    (0.0, 100.0, 50.0, 1.0),
        "co2":         (300.0, 2500.0, 600.0, 10.0),
    }
    cols = st.columns(4)
    vals: dict[str, float] = {}
    for i, name in enumerate(SENSOR_NAMES):
        spec = SENSORS[name]
        lo, hi, default, step = SLIDER[name]
        with cols[i]:
            vals[name] = st.slider(f"{name.title()} ({spec.unit})", lo, hi, default, step,
                                   key=f"sld_{name}")

    # live preview chips that recolor as the sliders move
    prev = ""
    for name in SENSOR_NAMES:
        spec = SENSORS[name]; v = vals[name]
        kind = _classify_value(name, v)
        c = {"ok": C_OK, "warn": C_WARN, "crit": C_CRIT}[kind]
        bg = {"ok": C_OK_BG, "warn": C_WARN_BG, "crit": C_CRIT_BG}[kind]
        hi_txt = "—" if spec.anomaly_high is None else f">{spec.anomaly_high}"
        lo_txt = "" if spec.anomaly_low is None else f" / <{spec.anomaly_low}"
        prev += (
            f"<div style='flex:1; min-width:150px; padding:9px 12px; border-radius:9px; "
            f"background:{bg}; border:1px solid {c}33;'>"
            f"<div style='font-size:0.66rem; color:{C_MUTED}; text-transform:uppercase; "
            f"letter-spacing:0.05em; font-weight:700;'>{name}</div>"
            f"<div style='font-size:1.15rem; font-weight:800; color:{c};'>{v:g}"
            f"<span style='font-size:0.72rem; color:{C_MUTED}; font-weight:600;'> {spec.unit}</span></div>"
            f"<div style='font-size:0.66rem; color:{C_MUTED};'>"
            f"{t('norm_label', lo=spec.normal_min, hi=spec.normal_max, u=spec.unit)} · "
            f"limit {hi_txt}{lo_txt}</div></div>"
        )
    pred = _predict_severity(vals)
    pkind = {"Critical": "crit", "Warning": "warn", "Normal": "ok"}.get(pred, "ok")
    st.markdown(
        f"<div style='font-size:0.78rem; color:{C_MUTED}; margin:8px 0 6px 0;'>{t('preview')}</div>"
        f"<div style='display:flex; gap:10px; flex-wrap:wrap;'>{prev}</div>"
        f"<div style='margin-top:10px; font-size:0.9rem;'>{t('expected_sev')}: {_pill(pkind, pred)}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button(t("inject_custom"), type="primary", key="manual_inject_btn"):
        res = _post("/inject", json={
            "zone": zone,
            "readings": {k: float(v) for k, v in vals.items()},
            "label_as_anomaly": bool(label)})
        if res.get("ok"):
            st.session_state["lab_last_inject"] = {"zone": zone, "seq": res.get("seq")}
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-weight:700; color:{C_TEXT}; margin:4px 0 10px 0; font-size:0.92rem;'>"
        f"3 · {t('recent_injections')}</div>", unsafe_allow_html=True)
    seen = (zones_seen or zones_for_inject)
    rows2: list[dict] = []
    for z in seen:
        for r in _get("/raw", zone=z, last_n=200).get("records", []):
            if r.get("source") == "manual":
                rows2.append(r)
    if not rows2:
        st.caption(t("no_injections"))
        return
    rows2.sort(key=lambda r: r.get("received_at", 0), reverse=True)
    show = pd.DataFrame(rows2[:12])
    show["time"] = pd.to_datetime(show["received_at"], unit="s").dt.strftime("%H:%M:%S")
    st.dataframe(
        show[["time", "zone", "seq", *SENSOR_NAMES]].rename(columns={
            "time": t("col_time"), "zone": t("col_zone"), "seq": t("col_seq"),
            **{n: n.title() for n in SENSOR_NAMES}}),
        use_container_width=True, hide_index=True,
    )


# ─────────────────────────────────────────────────── tab: Quality Metrics
def tab_metrics(zones_seen: list[str]) -> None:
    if not zones_seen:
        st.info(t("no_data_eval"))
        return
    bar = st.columns([1.2, 4])
    zone = bar[0].selectbox(t("sel_zone"), zones_seen, key="metrics_zone")
    data = _get("/evaluation", zone=zone) or {}

    interp = (data.get("interpolation") or {})
    det = (data.get("detection") or {})

    st.markdown(f"<div class='section-title'>{t('interp_quality')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-sub'>{t('interp_sub')}</div>", unsafe_allow_html=True)

    per_sensor = interp.get("per_sensor") or {}
    avg_mae = (sum(v["mae_recovered_only"] for v in per_sensor.values()) / len(per_sensor)
               if per_sensor else 0.0)
    k = st.columns(3)
    k[0].metric(t("m_truth_rows"), interp.get("n_truth", 0))
    k[1].metric(t("m_recovered_gaps"), interp.get("n_missing", 0))
    k[2].metric(t("m_avg_mae"), f"{avg_mae:.2f}")

    if per_sensor:
        rows = []
        for name, v in per_sensor.items():
            spec = SENSORS[name]
            rows.append({
                t("col_sensor"):      f"{name} ({spec.unit})",
                t("col_mae_rec"):     v["mae_recovered_only"],
                t("col_mae_all"):     v["mae_overall"],
                t("col_rec_samples"): v["n_gap_samples"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption(t("not_enough_overlap"))

    st.markdown(f"<br><div class='section-title'>{t('detection_perf')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-sub'>{t('detection_sub')}</div>", unsafe_allow_html=True)

    k = st.columns(3)
    k[0].metric(t("m_labelled"), det.get("support", 0))
    k[1].metric(t("m_prevalence"), f"{(det.get('anomaly_prevalence', 0)*100):.1f}%")
    k[2].metric(t("m_detectors"), len(det.get("detectors") or {}))

    detectors = det.get("detectors") or {}
    if not detectors:
        st.caption(t("need_labelled"))
        return
    rows = []
    for d_name, m in detectors.items():
        rows.append({
            "Detector": d_name,
            "Precision": m["precision"], "Recall": m["recall"], "F1": m["f1"],
            "TP": m["tp"], "FP": m["fp"], "FN": m["fn"], "TN": m["tn"],
        })
    df = pd.DataFrame(rows)

    chart_col, table_col = st.columns([1.4, 1], gap="large")
    with chart_col:
        st.markdown(f"<div class='chart-label'>{t('prf_label')}</div>", unsafe_allow_html=True)
        melted = df.melt(id_vars="Detector", value_vars=["Precision", "Recall", "F1"],
                         var_name="Metric", value_name="Score")
        metric_colors = {"Precision": C_PRIMARY, "Recall": C_ACCENT, "F1": C_OK}
        fig = px.bar(melted, x="Detector", y="Score", color="Metric",
                     barmode="group", range_y=[0, 1.08],
                     color_discrete_map=metric_colors, text="Score")
        fig.update_traces(textposition="outside", texttemplate="%{text:.2f}",
                          marker={"line": {"width": 0}},
                          textfont={"color": C_TEXT, "size": 10}, cliponaxis=False)
        _style_axes(fig, height=360)
        fig.update_layout(
            legend={"orientation": "h", "y": 1.12, "x": 0, "title": "", "font": {"size": 11}},
            bargap=0.28, bargroupgap=0.08)
        fig.update_xaxes(title_text="")
        fig.update_yaxes(title_text="score")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with table_col:
        st.markdown(f"<div class='chart-label'>{t('confusion_counts')}</div>", unsafe_allow_html=True)
        st.dataframe(
            df[["Detector", "Precision", "Recall", "F1", "TP", "FP", "FN", "TN"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Precision": st.column_config.ProgressColumn("Precision", min_value=0, max_value=1, format="%.2f"),
                "Recall": st.column_config.ProgressColumn("Recall", min_value=0, max_value=1, format="%.2f"),
                "F1": st.column_config.ProgressColumn("F1", min_value=0, max_value=1, format="%.2f"),
            },
        )
        best = df.loc[df["F1"].idxmax()]
        best_f1_val = f"{best['F1']:.2f}"
        st.markdown(
            f"<div style='margin-top:8px; padding:10px 14px; background:{C_OK_BG}; "
            f"border:1px solid #c2e5d3; border-radius:6px; font-size:0.82rem; color:{C_TEXT};'>"
            f"{t('best_f1', d=best['Detector'], f=best_f1_val)}</div>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────── tab: Building View
# Preferred top→bottom stacking order (rooftop first). Falls back gracefully.
_FLOOR_ORDER = ["Zone-B", "Zone-A", "Zone-C"]


def _fmt_val(name: str, v) -> str:
    if v is None or v == "":
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    return f"{f:.0f}" if name in ("humidity", "co2") else f"{f:.1f}"


def _sparkline_svg(vals, color, w: int = 134, h: int = 28) -> str:
    """Inline SVG mini trend line, normalized to its own min/max."""
    pts = []
    for v in vals:
        try:
            pts.append(float(v))
        except (TypeError, ValueError):
            pass
    if len(pts) < 2:
        return "<div class='spark'></div>"
    mn, mx = min(pts), max(pts)
    rng = (mx - mn) or 1.0
    nn = len(pts)
    coords = " ".join(
        f"{(i/(nn-1))*w:.1f},{(h - ((v-mn)/rng)*(h-6) - 3):.1f}"
        for i, v in enumerate(pts)
    )
    lx = float(w)
    ly = h - ((pts[-1]-mn)/rng)*(h-6) - 3
    return (
        f"<div class='spark'><svg width='100%' height='{h}' viewBox='0 0 {w} {h}' "
        f"preserveAspectRatio='none'>"
        f"<polyline points='{coords}' fill='none' stroke='{color}' stroke-width='1.7' "
        f"stroke-linejoin='round' stroke-linecap='round'/>"
        f"<circle cx='{lx:.1f}' cy='{ly:.1f}' r='2.3' fill='{color}'/></svg></div>"
    )


def _sensor_chips(row: dict, recent: list[dict]) -> str:
    chips = ""
    for name in SENSOR_NAMES:
        spec = SENSORS[name]
        bad = bool(row.get(f"{name}_anom"))
        spark = _sparkline_svg([r.get(name) for r in recent], C_CRIT if bad else C_PRIMARY)
        chips += (
            f"<div class='schip {'bad' if bad else 'ok'}'>"
            f"<div class='schip-top'><span class='dot'></span>"
            f"<span class='sname'>{name}</span>"
            f"<span class='sval'>{_fmt_val(name, row.get(name))}"
            f"<span class='sunit'>{spec.unit}</span></span></div>"
            f"{spark}</div>"
        )
    return chips


def tab_building(zones_seen: list[str]) -> None:
    st.markdown(
        f"<div class='section-title'><span class='livedot'></span>{t('bld_title')}</div>",
        unsafe_allow_html=True)
    st.markdown(f"<div class='section-sub'>{t('bld_sub')}</div>", unsafe_allow_html=True)

    if not zones_seen:
        st.info(t("bld_no_data"))
        return

    order = [z for z in _FLOOR_ORDER if z in zones_seen] + \
            [z for z in zones_seen if z not in _FLOOR_ORDER]
    n = len(order)
    counts = {"Normal": 0, "Warning": 0, "Critical": 0}

    # gather each zone's live state once
    zdata: dict[str, dict] = {}
    for z in order:
        proc = _get("/processed", zone=z, last_n=120).get("records", [])
        dec = _get("/decisions", zone=z, last_n=1).get("records", [])
        sev = dec[0]["severity"] if dec else "Normal"
        diag = dec[0].get("diagnosis", "") if dec else ""
        row = proc[-1] if proc else {}
        counts[sev] = counts.get(sev, 0) + 1
        zdata[z] = {"proc": proc, "sev": sev, "diag": diag, "row": row}

    # ── overall building status banner
    if counts["Critical"]:
        bstat, bkind = t("bld_status_crit"), "crit"
    elif counts["Warning"]:
        bstat, bkind = t("bld_status_warn"), "warn"
    else:
        bstat, bkind = t("bld_status_ok"), "ok"
    bcolor = {"crit": C_CRIT, "warn": C_WARN, "ok": C_OK}[bkind]
    st.markdown(
        f"<div class='bld-summary'>"
        f"<span class='livedot'></span>"
        f"<span class='bs-status' style='color:{bcolor};'>{bstat}</span>"
        f"<span class='bs-counts'>"
        f"{_pill('crit', str(counts['Critical']) + ' CRITICAL')}"
        f"{_pill('warn', str(counts['Warning']) + ' WARNING')}"
        f"{_pill('ok',   str(counts['Normal']) + ' NORMAL')}"
        f"</span></div>",
        unsafe_allow_html=True,
    )

    # ── view toggle: cross-section vs top-down floor plan
    view = st.radio(t("bld_view"), [t("bld_cross"), t("bld_plan")],
                    horizontal=True, key="bld_view", label_visibility="collapsed")
    is_plan = (view == t("bld_plan"))

    def _tint(sev):
        return {"Normal": C_SURFACE, "Warning": "#fff8ec", "Critical": "#fdeeec"}.get(sev, C_SURFACE)

    def _winclass(sev):
        return "crit" if sev == "Critical" else "lit"

    if is_plan:
        # ── top-down floor plan: each zone is a room in the building footprint
        rooms = ""
        for z in order:
            d = zdata[z]; sev = d["sev"]; row = d["row"]
            color = SEVERITY_COLOR.get(sev, C_OK)
            kind = {"Critical": "crit", "Warning": "warn", "Normal": "ok"}.get(sev, "ok")
            pulse = "crit" if sev == "Critical" else ""
            wins = "".join(f"<span class='rwin {_winclass(sev)}'></span>" for _ in range(5))
            metrics = ""
            for name in SENSOR_NAMES:
                bad = bool(row.get(f"{name}_anom"))
                metrics += (
                    f"<div class='pm {'bad' if bad else 'ok'}'><span class='pmdot'></span>"
                    f"{name} <b>{_fmt_val(name, row.get(name))}</b>{SENSORS[name].unit}</div>"
                )
            label = ZONES.get(z, {}).get("label", "")
            diag_html = (f"<div class='floor-diag'>{d['diag']}</div>"
                         if (sev != "Normal" and d["diag"]) else "")
            rooms += (
                f"<div class='plan-room {pulse}' style='border-top:6px solid {color}; background:{_tint(sev)};'>"
                f"<div class='room-windows'>{wins}</div>"
                f"<div class='room-name'>{z}</div>"
                f"<div class='room-fn'>{label}</div>"
                f"{_pill(kind, sev)}{diag_html}"
                f"<div class='room-metrics'>{metrics}</div>"
                f"</div>"
            )
        st.markdown(
            f"<div class='plan'><div class='plan-compass'>↑ {t('bld_north')}</div>"
            f"<div class='plan-grid'>{rooms}</div></div>",
            unsafe_allow_html=True,
        )
    else:
        # ── side cross-section with exterior windows
        floors_html = ""
        for i, z in enumerate(order):
            d = zdata[z]; sev = d["sev"]; row = d["row"]
            color = SEVERITY_COLOR.get(sev, C_OK)
            pulse = "crit" if sev == "Critical" else ""
            kind = {"Critical": "crit", "Warning": "warn", "Normal": "ok"}.get(sev, "ok")
            chips = _sensor_chips(row, d["proc"][-40:])
            label = ZONES.get(z, {}).get("label", "")
            diag_html = (f"<div class='floor-diag'>{d['diag']}</div>"
                         if (sev != "Normal" and d["diag"]) else "")
            facade = "".join(
                f"<span class='win {_winclass(sev)}'></span>" for _ in range(6))
            floors_html += (
                f"<div class='floor {pulse}' style='border-left:6px solid {color}; background:{_tint(sev)};'>"
                f"<div class='floor-left'>"
                f"<div class='floor-num'>F{n - i}</div>"
                f"<div class='floor-name'>{z}</div>"
                f"<div class='floor-fn'>{label}</div>"
                f"{_pill(kind, sev)}{diag_html}"
                f"</div>"
                f"<div class='floor-sensors'>{chips}</div>"
                f"<div class='facade'>{facade}</div>"
                f"</div>"
            )
        st.markdown(
            f"<div class='bld-wrap'>"
            f"<div class='bld-roof'>▲ {t('bld_rooftop')}</div>"
            f"{floors_html}"
            f"<div class='bld-ground'></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='max-width:940px; margin:10px auto 0 auto; font-size:0.78rem; "
        f"color:{C_TEXT2}; display:flex; gap:6px; align-items:center; flex-wrap:wrap;'>"
        f"<span style='color:#16a34a;'>●</span> {('sensor normal' if _lang()=='en' else '센서 정상')}"
        f"&nbsp;&nbsp;<span style='color:#ef4444;'>●</span> "
        f"{('sensor breached' if _lang()=='en' else '센서 위반')}"
        f"&nbsp;&nbsp;·&nbsp;&nbsp;{('line = ' + t('bld_trend') if _lang()=='en' else '선 = ' + t('bld_trend'))}"
        f"&nbsp;&nbsp;·&nbsp;&nbsp;{('floor tint = severity' if _lang()=='en' else '층 색 = 심각도')}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── drill-down: click a zone to open its live sensor charts inline
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='max-width:940px; margin:0 auto 4px auto; font-weight:700; "
        f"color:{C_TEXT}; font-size:0.92rem;'>{t('bld_drill')}</div>",
        unsafe_allow_html=True)
    dcols = st.columns(len(order))
    for idx, z in enumerate(order):
        sev = zdata[z]["sev"]
        mark = "🔴" if sev == "Critical" else ("🟠" if sev == "Warning" else "🟢")
        if dcols[idx].button(f"{mark}  {z}", key=f"bld_insp_{z}",
                             use_container_width=True):
            st.session_state["bld_inspect"] = z

    insp = st.session_state.get("bld_inspect")
    if insp in order:
        hc = st.columns([4, 1])
        hc[0].markdown(
            f"<div style='font-size:1.05rem; font-weight:800; color:{C_TEXT}; padding-top:6px;'>"
            f"🔍 {t('bld_inspecting')}: {insp} · {ZONES.get(insp,{}).get('label','')}</div>",
            unsafe_allow_html=True)
        if hc[1].button(t("bld_close"), key="bld_insp_close", use_container_width=True):
            st.session_state["bld_inspect"] = None
        else:
            raw = _get("/raw", zone=insp, last_n=200)
            proc = _get("/processed", zone=insp, last_n=200)
            raw_df = pd.DataFrame(raw.get("records", []))
            proc_df = pd.DataFrame(proc.get("records", []))
            ccs = st.columns(2, gap="large")
            for i, name in enumerate(SENSOR_NAMES):
                with ccs[i % 2]:
                    fig = _sensor_chart(name, raw_df, proc_df, show_raw=False)
                    fig.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True,
                                    key=f"bldins_{insp}_{name}",
                                    config={"displayModeBar": False})

    # ── live demo controls: inject a fault and watch the floor react
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='max-width:940px; margin:0 auto; font-weight:700; color:{C_TEXT}; "
        f"font-size:0.92rem;'>{t('bld_demo')}</div>",
        unsafe_allow_html=True)
    scen = (_get("/scenarios") or {}).get("scenarios", [])
    scen_tags = [s["tag"] for s in scen] or ["fire_risk"]
    cc = st.columns([1.2, 1.6, 1, 3])
    z_sel = cc[0].selectbox(t("sel_zone"), order, key="bld_zone",
                            label_visibility="collapsed")
    s_sel = cc[1].selectbox(t("bld_scenario"), scen_tags, key="bld_scen",
                            label_visibility="collapsed")
    if cc[2].button(t("bld_inject"), key="bld_inject_btn", type="primary",
                    use_container_width=True):
        res = _post("/inject", json={"zone": z_sel, "scenario": s_sel,
                                     "label_as_anomaly": True})
        if res.get("ok"):
            st.success(t("inject_success", tag=s_sel, zone=z_sel,
                         seq=res.get("seq"),
                         s=f"{PIPELINE.decision_worker_interval_s:.0f}"))


# ─────────────────────────────────────────────────────────────── main
def main() -> None:
    settings = _sidebar()

    stats = _get("/stats") or {}
    decisions = (_get("/decisions", last_n=200) or {}).get("records", []) or []
    scenarios_resp = _get("/scenarios") or {}
    zones_seen = (_get("/zones") or {}).get("seen", []) or []

    _app_bar(stats)

    tabs = st.tabs([
        t("tab_building"), t("tab_operations"), t("tab_telemetry"),
        t("tab_pipeline"), t("tab_alerts"), t("tab_scenario"), t("tab_metrics"),
    ])
    with tabs[0]: tab_building(zones_seen or ZONE_NAMES)
    with tabs[1]: tab_operations(stats, decisions)
    with tabs[2]: tab_telemetry(zones_seen or ZONE_NAMES)
    with tabs[3]: tab_pipeline(stats, decisions)
    with tabs[4]: tab_alerts(decisions)
    with tabs[5]: tab_scenario_lab(scenarios_resp, zones_seen)
    with tabs[6]: tab_metrics(zones_seen or ZONE_NAMES)

    st.markdown(
        f"<div style='margin-top:20px; padding-top:14px; border-top:1px solid {C_BORDER}; "
        f"display:flex; justify-content:space-between; font-size:0.76rem; color:{C_MUTED};'>"
        f"<div>BEMS Anomaly Operations Center · v2.0</div>"
        f"<div>{t('footer_refresh', ts=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if settings["auto"]:
        time.sleep(settings["refresh"])
        st.rerun()


if __name__ == "__main__":
    main()
