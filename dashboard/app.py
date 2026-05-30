"""Stage 6 — Dashboard Agent (Enterprise Control Center).

A dense, scannable operations console for the BEMS pipeline. Five sections,
each opened by a left-side navigation:

  • Operations       — system health board: services, packet flow per zone,
                       severity counters, decision throughput
  • Telemetry        — per-zone time-series, raw vs interpolated, anomaly
                       overlays, drop-list, sensor stats
  • Pipeline         — explicit agent topology + per-agent status, KPIs and
                       responsibilities
  • Alerts           — filterable severity feed with diagnosis / action /
                       evidence columns, exportable
  • Scenario Lab     — controlled fault injection (preset library + custom
                       values) for runbook validation
  • Quality Metrics  — interpolation MAE and detection P/R/F1 per detector
                       against ground-truth labels
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
  border-radius: 8px; padding: 14px 16px;
  box-shadow: 0 1px 0 rgba(9,30,66,0.04);
}}
[data-testid="stMetricValue"] {{
  font-size: 1.6rem !important; color: var(--text);
  font-weight: 700; letter-spacing: -0.02em;
}}
[data-testid="stMetricLabel"] {{
  color: var(--muted) !important; font-weight: 600 !important;
  font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 0.06em;
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

/* --- hide chrome --------------------------------------------------- */
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
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
                         "Decider Online" if running else "Decider Idle")
    err = worker.get("last_error")
    error_pill = _pill("crit", "Worker Error") if err else _pill("ok", "All Systems OK")
    st.markdown(
        f"""
        <div class='appbar'>
          <div class='appbar-brand'>
            <div class='appbar-logo'>◆</div>
            <div>
              <div class='appbar-title'>BEMS · Anomaly Operations Center</div>
              <div class='appbar-sub'>Smart Building Energy Management · 6-stage agent pipeline · {n_zones} monitored zones</div>
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
        f"<div style='font-size:0.76rem; color:{C_MUTED}; margin-top:2px;'>v2.0 · operations</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:600; margin:14px 0 6px 0;'>Refresh</div>",
        unsafe_allow_html=True,
    )
    auto = st.sidebar.toggle("Auto-refresh", value=True, label_visibility="collapsed")
    refresh = st.sidebar.slider("Interval (s)", 2.0, 15.0, 4.0, 0.5,
                                label_visibility="collapsed")
    st.sidebar.caption(f"{'Auto-refresh ON' if auto else 'Auto-refresh OFF'} · every {refresh:.1f}s")

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:600; margin:18px 0 6px 0;'>Administration</div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Reset operational store", use_container_width=True):
        _post("/reset")
        st.sidebar.success("Store wiped.")
        time.sleep(0.4)

    st.sidebar.markdown(
        f"<div style='font-size:0.72rem; color:{C_MUTED}; text-transform:uppercase; "
        f"letter-spacing:0.06em; font-weight:600; margin:18px 0 6px 0;'>Sensor thresholds</div>",
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
        margin={"l": 50, "r": 16, "t": 30, "b": 36},
        paper_bgcolor="white", plot_bgcolor="white",
        font={"color": C_TEXT, "family": "-apple-system, sans-serif", "size": 12},
        xaxis={"gridcolor": PLOT["grid"], "linecolor": PLOT["axis"],
               "zeroline": False, "showspikes": True, "spikecolor": "#cbd5e1",
               "spikedash": "dot", "spikethickness": 1},
        yaxis={"gridcolor": PLOT["grid"], "linecolor": PLOT["axis"], "zeroline": False},
        legend={"orientation": "h", "y": -0.22, "x": 0, "bgcolor": "rgba(0,0,0,0)",
                "font": {"size": 11}},
    )
    return fig


# ─────────────────────────────────────────────────── tab: Operations
def tab_operations(stats: dict, decisions: list[dict]) -> None:
    zones = stats.get("zones", {}) or {}
    worker = stats.get("worker") or {}

    # KPI strip
    crit = sum(1 for d in decisions if d.get("severity") == "Critical")
    warn = sum(1 for d in decisions if d.get("severity") == "Warning")
    total_received = sum(z.get("received", 0) for z in zones.values())
    total_missing = sum(z.get("missing", 0) for z in zones.values())
    avg_loss = (total_missing / max(sum(z.get("expected", 0) for z in zones.values()), 1)) * 100

    k = st.columns(6)
    k[0].metric("Active Zones", len(zones))
    k[1].metric("Packets Received", f"{total_received:,}")
    k[2].metric("Packet Loss", f"{avg_loss:.1f}%")
    k[3].metric("Decisions Made", worker.get("decisions_made", 0))
    k[4].metric("Critical Alerts", crit)
    k[5].metric("Warning Alerts", warn)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two-column: services table + decision timeline
    left, right = st.columns([1, 1.2])

    with left:
        st.markdown("<div class='section-title'>System Services</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-sub'>Health of the 6 pipeline stages</div>", unsafe_allow_html=True)
        last_tick = worker.get("last_tick")
        last_tick_str = (datetime.fromtimestamp(last_tick).strftime("%H:%M:%S")
                         if last_tick else "—")
        services = [
            ("Generator",    "synthetic BEMS sample stream",       "ok"   if stats.get("total_truth", 0) > 0 else "muted"),
            ("Transmitter",  "network degradation + forwarding",   "ok"   if total_received > 0 else "muted"),
            ("Collector",    f"FastAPI · {PIPELINE.collector_url}", "ok"),
            ("ML Processor", f"interpolate + Z-score + IForest",   "ok"   if worker.get("decisions_made", 0) > 0 else "muted"),
            ("Decision",     f"rule-based · last tick {last_tick_str}",
                             "crit" if worker.get("last_error") else
                             ("ok"  if worker.get("running") else "muted")),
            ("Dashboard",    "this console",                       "ok"),
        ]
        rows_html = "".join(
            f"<tr><td><b>{n}</b></td><td><code>{d}</code></td>"
            f"<td style='text-align:right;'>{_pill(s, 'Operational' if s=='ok' else ('Idle' if s=='muted' else 'Error'))}</td></tr>"
            for n, d, s in services
        )
        st.markdown(
            f"<table class='svc-table'>"
            f"<thead><tr><th>Service</th><th>Description</th><th style='text-align:right;'>Status</th></tr></thead>"
            f"<tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )
        if worker.get("last_error"):
            st.markdown(
                f"<div style='margin-top:10px; padding:10px 14px; background:{C_CRIT_BG}; "
                f"border:1px solid #f3c4be; border-radius:6px; color:{C_CRIT}; font-size:0.85rem;'>"
                f"<b>Worker error:</b> {worker['last_error']}</div>",
                unsafe_allow_html=True,
            )

    with right:
        # header row with title + toggle
        hdr_l, hdr_r = st.columns([3, 1])
        with hdr_l:
            st.markdown("<div class='section-title'>Decision Timeline</div>", unsafe_allow_html=True)
            st.markdown("<div class='section-sub'>Recent decisions across all zones — Critical/Warning highlighted</div>",
                        unsafe_allow_html=True)
        with hdr_r:
            show_normal = st.toggle(
                "Show Normal", value=False, key="ops_show_normal",
                help="Hide nominal events to make anomalies easier to spot.",
            )

        if not decisions:
            st.info("Awaiting first decision from worker.")
        else:
            df = pd.DataFrame(decisions)
            df["time"] = pd.to_datetime(df["decided_at"], unit="s")
            df = df.head(200)

            # severity counts in the window — shown as chips above the chart
            n_crit = int((df["severity"] == "Critical").sum())
            n_warn = int((df["severity"] == "Warning").sum())
            n_norm = int((df["severity"] == "Normal").sum())
            st.markdown(
                f"<div style='margin: 4px 0 8px 0; display:flex; gap:8px; flex-wrap:wrap; align-items:center;'>"
                f"{_pill('crit', f'{n_crit} CRITICAL')}"
                f"{_pill('warn', f'{n_warn} WARNING')}"
                f"{_pill('ok',   f'{n_norm} NORMAL')}"
                f"<span style='color:{C_MUTED}; font-size:0.8rem;'>"
                f"window: last {len(df)} decisions</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            fig = go.Figure()
            zones_order = sorted(df["zone"].unique())

            # layer ordering: Normal (faint dots) → Warning (mid) → Critical (top, biggest)
            layers = [
                ("Normal",   {"size": 6,  "opacity": 0.30, "symbol": "circle",
                              "line": {"width": 0}}),
                ("Warning",  {"size": 14, "opacity": 0.95, "symbol": "diamond",
                              "line": {"width": 1.5, "color": "white"}}),
                ("Critical", {"size": 18, "opacity": 1.00, "symbol": "star",
                              "line": {"width": 1.8, "color": "#5a1610"}}),
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
                yaxis={
                    "title": "",
                    "categoryorder": "array",
                    "categoryarray": zones_order[::-1],
                    "tickfont": {"size": 12, "color": C_TEXT},
                    "showgrid": False,
                },
                xaxis={
                    "title": "",
                    "tickformat": "%H:%M:%S",
                    "showgrid": True, "gridcolor": "#f1f3f5",
                },
                legend={
                    "orientation": "h", "y": 1.10, "x": 0,
                    "bgcolor": "rgba(0,0,0,0)", "font": {"size": 11, "color": C_TEXT},
                    "itemclick": "toggleothers",
                },
                margin={"l": 70, "r": 20, "t": 50, "b": 30},
                hoverlabel={"bgcolor": "white", "bordercolor": C_BORDER,
                            "font": {"color": C_TEXT, "size": 12}},
            )

            # faint swimlane separators between zones
            for i in range(len(zones_order) - 1):
                fig.add_hline(
                    y=i + 0.5, line={"color": "#f1f3f5", "width": 1},
                    layer="below",
                )

            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Critical은 별 모양, Warning은 다이아몬드, Normal은 작은 점. "
                "범례를 클릭하면 해당 severity만 표시됩니다."
            )

    # Zone status cards
    st.markdown("<br><div class='section-title'>Zone Status</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Per-zone packet flow over the rolling window</div>",
                unsafe_allow_html=True)
    if not zones:
        st.info("No telemetry yet. Awaiting transmitter.")
        return
    cols = st.columns(len(zones))
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
                    {_pill(loss_kind, f'{loss_pct:.1f}% loss')}
                  </div>
                  <div class='card-row'><span class='k'>Received</span>     <span class='v'>{zs.get('received',0):,}</span></div>
                  <div class='card-row'><span class='k'>Expected</span>     <span class='v'>{zs.get('expected',0):,}</span></div>
                  <div class='card-row'><span class='k'>Missing</span>      <span class='v'>{zs.get('missing',0):,}</span></div>
                  <div class='card-row'><span class='k'>Seq range</span>    <span class='v'>{zs.get('first_seq')} → {zs.get('last_seq')}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────── tab: Telemetry
def _sensor_chart(name: str, raw_df: pd.DataFrame, proc_df: pd.DataFrame) -> go.Figure:
    spec = SENSORS[name]
    fig = go.Figure()
    fig.add_hrect(y0=spec.normal_min, y1=spec.normal_max,
                  fillcolor=PLOT["normal_band"], opacity=0.06, line_width=0)
    if not proc_df.empty:
        fig.add_trace(go.Scatter(
            x=proc_df["seq"], y=proc_df[name], mode="lines",
            name="Interpolated",
            line={"color": PLOT["interp"], "width": 2, "shape": "spline"},
        ))
        z_an = proc_df[proc_df[f"{name}_anom"] == True]   # noqa: E712
        if not z_an.empty:
            fig.add_trace(go.Scatter(
                x=z_an["seq"], y=z_an[name], mode="markers",
                name="Z-score / Hard",
                marker={"color": PLOT["z_anom"], "size": 11, "symbol": "x",
                        "line": {"width": 2, "color": PLOT["z_anom"]}},
            ))
        if_an = proc_df[proc_df["iforest_anom"] == True]  # noqa: E712
        if not if_an.empty:
            fig.add_trace(go.Scatter(
                x=if_an["seq"], y=if_an[name], mode="markers",
                name="IsolationForest",
                marker={"color": PLOT["iforest"], "size": 10,
                        "symbol": "circle-open", "line": {"width": 2}},
            ))
    if not raw_df.empty and name in raw_df.columns:
        fig.add_trace(go.Scatter(
            x=raw_df["seq"], y=raw_df[name], mode="markers",
            name="Raw",
            marker={"color": PLOT["raw"], "size": 5, "opacity": 0.6},
        ))
    if spec.anomaly_high is not None:
        fig.add_hline(y=spec.anomaly_high, line_dash="dot",
                      line_color=PLOT["z_anom"], line_width=1.2)
    if spec.anomaly_low is not None:
        fig.add_hline(y=spec.anomaly_low, line_dash="dot",
                      line_color=PLOT["z_anom"], line_width=1.2)
    fig.update_layout(title={
        "text": f"<b>{name.title()}</b> <span style='color:{C_MUTED};font-weight:400;'>({spec.unit})</span>",
        "font": {"size": 13, "color": C_TEXT}, "x": 0.01, "y": 0.97,
    })
    fig.update_yaxes(title_text=spec.unit)
    fig.update_xaxes(title_text="seq")
    return _style_axes(fig, height=290)


def tab_telemetry(zones_seen: list[str]) -> None:
    if not zones_seen:
        st.info("No telemetry has arrived yet.")
        return
    bar = st.columns([1.2, 4])
    with bar[0]:
        zone = st.selectbox("Zone", zones_seen, key="tel_zone")
    raw = _get("/raw", zone=zone, last_n=200)
    proc = _get("/processed", zone=zone, last_n=200)

    raw_records = raw.get("records", [])
    raw_df = pd.DataFrame(raw_records)
    proc_df = pd.DataFrame(proc.get("records", []))

    k = st.columns(4)
    k[0].metric("Raw points",        len(raw_df))
    k[1].metric("Interpolated rows", len(proc_df))
    k[2].metric("Missing in window", len(raw.get("missing_seqs", [])))
    n_anom = int(proc_df.get("anomaly_any", pd.Series(dtype=bool)).sum()) if not proc_df.empty else 0
    k[3].metric("Flagged anomalies", n_anom)

    missing = raw.get("missing_seqs", [])
    if missing:
        st.markdown(
            f"<div style='margin-top:14px; padding:10px 14px; background:{C_WARN_BG}; "
            f"border:1px solid #f3d9a8; border-radius:6px; color:{C_WARN}; font-size:0.85rem;'>"
            f"<b>Packet loss detected</b> — {len(missing)} sequence(s) dropped; "
            f"the ML Processor has interpolated them. "
            f"Recent gaps: <code style='background:white; color:{C_WARN};'>{missing[-20:]}</code>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, name in enumerate(SENSOR_NAMES):
        with cols[i % 2]:
            st.plotly_chart(_sensor_chart(name, raw_df, proc_df),
                            use_container_width=True, key=f"tel_{zone}_{name}")


# ─────────────────────────────────────────────────── tab: Pipeline
AGENT_CARDS = [
    ("01", "Generator",
     "agents/generator.py",
     "Multi-zone BEMS sample stream. Each tick emits one sample per zone with a daily-cycle baseline, "
     "Gaussian noise, and a ground-truth anomaly label that downstream evaluation depends on."),
    ("02", "Transmitter",
     "agents/transmitter.py",
     "Forwards every sample twice — clean copy to /truth (for evaluation), degraded copy (variable delay, "
     "10% packet drop, electromagnetic-interference noise) to /ingest."),
    ("03", "Collector",
     "agents/collector.py",
     "FastAPI service. Persists truth, readings, and decisions to SQLite (WAL mode). Hosts the background "
     "decision worker. Exposes raw, processed, decisions, stats, evaluation, scenarios, inject."),
    ("04", "ML Processor",
     "agents/ml_processor.py",
     "Per-zone reindex and linear interpolation of dropped sequences. Three detectors run in parallel: "
     "robust Z-score (MAD-based, |z|>2.5), IsolationForest (multivariate, contamination=0.05), and the "
     "hard physical thresholds from the operating spec."),
    ("05", "Decision",
     "agents/decision.py",
     "Severity classification (Normal / Warning / Critical). Rule-engine root-cause inference matches the "
     "fired-sensor pattern against a runbook of known events (HVAC failure, fire risk, peak load, cold "
     "snap, occupancy spike, …) and outputs an explainable diagnosis and recommended action."),
    ("06", "Dashboard",
     "agents/dashboard.py",
     "This console. Polls the Collector and renders the operations view, telemetry, alerts, scenario "
     "lab, and quality-metrics surfaces."),
]


def tab_pipeline(stats: dict, decisions: list[dict]) -> None:
    zones = stats.get("zones", {}) or {}
    worker = stats.get("worker") or {}
    received = sum(z.get("received", 0) for z in zones.values())
    missing = sum(z.get("missing", 0) for z in zones.values())
    last_dec = decisions[0]["decided_at"] if decisions else None
    last_dec_h = datetime.fromtimestamp(last_dec).strftime("%H:%M:%S") if last_dec else "—"

    kpis = {
        "Generator":    {"k1": ("Truth rows", f"{stats.get('total_truth', 0):,}"),
                         "k2": ("Cadence",    f"{PIPELINE.sample_interval_s:.1f}s")},
        "Transmitter":  {"k1": ("Received",   f"{received:,}"),
                         "k2": ("Dropped",    f"{missing:,}")},
        "Collector":    {"k1": ("Zones",      f"{len(zones)}"),
                         "k2": ("Database",   PIPELINE.db_path.split('/')[-1])},
        "ML Processor": {"k1": ("Window",     f"{PIPELINE.window_size} rows"),
                         "k2": ("Z-threshold",f"{PIPELINE.zscore_threshold}")},
        "Decision":     {"k1": ("Decisions",  f"{worker.get('decisions_made', 0):,}"),
                         "k2": ("Last tick",  last_dec_h)},
        "Dashboard":    {"k1": ("Refresh",    "live"),
                         "k2": ("Render",     "Streamlit + Plotly")},
    }
    status_kind = {
        "Generator":    "ok" if stats.get("total_truth", 0) > 0 else "muted",
        "Transmitter":  "ok" if received > 0 else "muted",
        "Collector":    "ok",
        "ML Processor": "ok" if worker.get("decisions_made", 0) > 0 else "muted",
        "Decision":     "crit" if worker.get("last_error") else ("ok" if worker.get("running") else "muted"),
        "Dashboard":    "ok",
    }
    status_label = {"ok": "Operational", "muted": "Idle", "crit": "Error"}

    st.markdown("<div class='section-title'>Agent Topology</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Six independent agents communicating via REST. "
                "Each card lists the agent's responsibility, source file, and live KPIs.</div>",
                unsafe_allow_html=True)

    for i in (0, 2, 4):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(AGENT_CARDS): continue
            num, name, path, role = AGENT_CARDS[idx]
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
                      <div style='color:{C_TEXT2}; font-size:0.86rem; line-height:1.5; margin:8px 0 12px 0;'>{role}</div>
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
                        Source: <code style='background:{C_SURFACE2}; padding:2px 6px; border-radius:4px;'>{path}</code>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────── tab: Alerts
def tab_alerts(decisions: list[dict]) -> None:
    if not decisions:
        st.info("No alerts have been generated yet.")
        return

    df = pd.DataFrame(decisions)
    df["time"] = pd.to_datetime(df["decided_at"], unit="s")

    k = st.columns(4)
    k[0].metric("Total decisions", len(df))
    k[1].metric("Critical", int((df["severity"] == "Critical").sum()))
    k[2].metric("Warning",  int((df["severity"] == "Warning").sum()))
    k[3].metric("Normal",   int((df["severity"] == "Normal").sum()))

    st.markdown("<br>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.5, 1.5, 1])
    sev_filter = f1.multiselect(
        "Severity", ["Critical", "Warning", "Normal"],
        default=["Critical", "Warning"], key="sev_filter",
    )
    zone_filter = f2.multiselect(
        "Zone", sorted(df["zone"].unique().tolist()),
        default=sorted(df["zone"].unique().tolist()), key="zone_filter",
    )
    limit = f3.slider("Max rows", 10, 200, 50, 10, key="alerts_limit")

    filt = df[df["severity"].isin(sev_filter) & df["zone"].isin(zone_filter)].head(limit)
    if filt.empty:
        st.caption("No alerts match the current filters.")
        return

    # Export CSV
    csv_buf = io.StringIO()
    filt[["time", "zone", "seq", "severity", "diagnosis", "action",
          "detector", "alert"]].to_csv(csv_buf, index=False)
    st.download_button(
        "Export filtered alerts (CSV)",
        csv_buf.getvalue(), file_name="bems_alerts.csv", mime="text/csv",
        use_container_width=False,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    for _, rec in filt.iterrows():
        sev = rec["severity"]
        color = SEVERITY_COLOR.get(sev, C_MUTED)
        ts = datetime.fromtimestamp(rec["decided_at"]).strftime("%H:%M:%S")
        date = datetime.fromtimestamp(rec["decided_at"]).strftime("%Y-%m-%d")
        chips = " ".join(
            f"<span class='pill pill-muted' style='font-size:0.7rem;'>"
            f"{t['sensor']} = {t['value']}{t['unit']} (z={t['z']})</span>"
            for t in (rec.get("triggered") or [])
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
                <div style='color:{C_MUTED};'>Detector</div>
                <div><code>{rec.get('detector','—')}</code></div>
              </div>
              <div>
                <div class='alert-diag'>{rec.get('diagnosis','—')}</div>
                <div class='alert-action'><b>Recommended action:</b> {rec.get('action','—')}</div>
                <div class='alert-evidence'>{chips}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────── tab: Scenario Lab
def tab_scenario_lab(scenarios_resp: dict, zones_seen: list[str]) -> None:
    st.markdown("<div class='section-title'>Controlled Fault Injection</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Push synthetic samples into the pipeline to validate runbooks "
        "and detector response. Injected samples are labelled as ground-truth anomalies so the "
        "Quality Metrics surface can score them.</div>",
        unsafe_allow_html=True,
    )

    scenarios = scenarios_resp.get("scenarios", [])
    zones_for_inject = ZONE_NAMES

    st.markdown(
        "<div style='font-weight:700; color:" + C_TEXT + "; margin:4px 0 10px 0; "
        "font-size:0.92rem;'>Preset scenarios</div>",
        unsafe_allow_html=True,
    )

    rows = [scenarios[i:i + 3] for i in range(0, len(scenarios), 3)]
    for row in rows:
        cols = st.columns(3)
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
                zone = st.selectbox(
                    "Target zone", zones_for_inject, key=f"inj_zone_{sc['tag']}",
                    label_visibility="collapsed",
                )
                if st.button(f"Inject into {zone}", key=f"inj_btn_{sc['tag']}",
                             use_container_width=True, type="primary"):
                    res = _post("/inject", json={
                        "zone": zone, "scenario": sc["tag"], "label_as_anomaly": True,
                    })
                    if res.get("ok"):
                        st.success(
                            f"Injected {sc['tag']} into {zone} at seq {res.get('seq')}. "
                            f"Decision will appear in the Alerts tab within "
                            f"{PIPELINE.decision_worker_interval_s:.0f}s."
                        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-weight:700; color:" + C_TEXT + "; margin:4px 0 10px 0; "
        "font-size:0.92rem;'>Custom sample</div>",
        unsafe_allow_html=True,
    )
    with st.form("manual_inject", clear_on_submit=False, border=True):
        cz, cl = st.columns([1, 1])
        zone = cz.selectbox("Zone", zones_for_inject, key="manual_zone")
        label = cl.checkbox("Label as ground-truth anomaly", value=True)
        c1, c2, c3, c4 = st.columns(4)
        power = c1.number_input("Power (kW)",       value=2.5,  step=0.5,  format="%.2f")
        temp  = c2.number_input("Temperature (°C)", value=23.0, step=0.5,  format="%.2f")
        hum   = c3.number_input("Humidity (%)",     value=50.0, step=1.0,  format="%.2f")
        co2   = c4.number_input("CO₂ (ppm)",        value=600,  step=20)
        submitted = st.form_submit_button("Inject custom sample", type="primary")
        if submitted:
            res = _post("/inject", json={
                "zone": zone,
                "readings": {"power": float(power), "temperature": float(temp),
                             "humidity": float(hum), "co2": float(co2)},
                "label_as_anomaly": bool(label),
            })
            if res.get("ok"):
                st.success(f"Injected into {zone} at seq {res.get('seq')}.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-weight:700; color:" + C_TEXT + "; margin:4px 0 10px 0; "
        "font-size:0.92rem;'>Recent injections</div>",
        unsafe_allow_html=True,
    )
    seen = (zones_seen or zones_for_inject)
    rows: list[dict] = []
    for z in seen:
        for r in _get("/raw", zone=z, last_n=200).get("records", []):
            if r.get("source") == "manual":
                rows.append(r)
    if not rows:
        st.caption("No manual injections have been recorded yet.")
        return
    rows.sort(key=lambda r: r.get("received_at", 0), reverse=True)
    show = pd.DataFrame(rows[:12])
    show["time"] = pd.to_datetime(show["received_at"], unit="s").dt.strftime("%H:%M:%S")
    st.dataframe(
        show[["time", "zone", "seq", *SENSOR_NAMES]].rename(columns={
            "time": "Time", "zone": "Zone", "seq": "Seq",
            **{n: n.title() for n in SENSOR_NAMES},
        }),
        use_container_width=True, hide_index=True,
    )


# ─────────────────────────────────────────────────── tab: Quality Metrics
def tab_metrics(zones_seen: list[str]) -> None:
    if not zones_seen:
        st.info("No data to evaluate yet.")
        return
    bar = st.columns([1.2, 4])
    zone = bar[0].selectbox("Zone", zones_seen, key="metrics_zone")
    data = _get("/evaluation", zone=zone) or {}

    interp = (data.get("interpolation") or {})
    det = (data.get("detection") or {})

    st.markdown("<div class='section-title'>Interpolation Quality</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Mean absolute error between recovered values and ground-truth. "
        "<b>Recovered-only</b> is the column to optimise — it isolates the dropped sequences "
        "the ML Processor actually had to reconstruct.</div>",
        unsafe_allow_html=True,
    )
    k = st.columns(3)
    k[0].metric("Truth rows",      interp.get("n_truth", 0))
    k[1].metric("Recovered gaps",  interp.get("n_missing", 0))
    k[2].metric("Per-sensor MAE shown below", "")

    if interp.get("per_sensor"):
        rows = []
        for name, v in interp["per_sensor"].items():
            spec = SENSORS[name]
            rows.append({
                "Sensor":            f"{name} ({spec.unit})",
                "MAE (recovered)":   v["mae_recovered_only"],
                "MAE (all rows)":    v["mae_overall"],
                "Recovered samples": v["n_gap_samples"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("Not enough overlap between truth and readings yet.")

    st.markdown("<br><div class='section-title'>Anomaly Detection Performance</div>",
                unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Precision / Recall / F1 of each detector against the "
        "ground-truth anomaly labels. <b>Union</b> combines all three.</div>",
        unsafe_allow_html=True,
    )

    k = st.columns(3)
    k[0].metric("Labelled samples",     det.get("support", 0))
    k[1].metric("Anomaly prevalence",   f"{(det.get('anomaly_prevalence', 0)*100):.1f}%")
    k[2].metric("Detectors evaluated",  len(det.get("detectors") or {}))

    detectors = det.get("detectors") or {}
    if not detectors:
        st.caption("Need a few labelled samples before metrics are meaningful.")
        return
    rows = []
    for d_name, m in detectors.items():
        rows.append({
            "Detector":  d_name,
            "Precision": m["precision"], "Recall": m["recall"], "F1": m["f1"],
            "TP": m["tp"], "FP": m["fp"], "FN": m["fn"], "TN": m["tn"],
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    det_colors = {
        "zscore":         C_PRIMARY, "hard_threshold": C_CRIT,
        "iforest":        C_ACCENT,  "union":          C_OK,
    }
    fig = px.bar(df, x="Detector", y="F1", color="Detector",
                 color_discrete_map=det_colors, range_y=[0, 1], text="F1")
    fig.update_traces(textposition="outside",
                      marker={"line": {"width": 0}},
                      textfont={"color": C_TEXT, "size": 12})
    _style_axes(fig, height=320)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text="")
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────── main
def main() -> None:
    settings = _sidebar()

    stats = _get("/stats") or {}
    decisions = (_get("/decisions", last_n=200) or {}).get("records", []) or []
    scenarios_resp = _get("/scenarios") or {}
    zones_seen = (_get("/zones") or {}).get("seen", []) or []

    _app_bar(stats)

    tabs = st.tabs([
        "Operations", "Telemetry", "Pipeline", "Alerts", "Scenario Lab", "Quality Metrics",
    ])
    with tabs[0]: tab_operations(stats, decisions)
    with tabs[1]: tab_telemetry(zones_seen or ZONE_NAMES)
    with tabs[2]: tab_pipeline(stats, decisions)
    with tabs[3]: tab_alerts(decisions)
    with tabs[4]: tab_scenario_lab(scenarios_resp, zones_seen)
    with tabs[5]: tab_metrics(zones_seen or ZONE_NAMES)

    st.markdown(
        f"<div style='margin-top:20px; padding-top:14px; border-top:1px solid {C_BORDER}; "
        f"display:flex; justify-content:space-between; font-size:0.76rem; color:{C_MUTED};'>"
        f"<div>BEMS Anomaly Operations Center · v2.0</div>"
        f"<div>Last refresh {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if settings["auto"]:
        time.sleep(settings["refresh"])
        st.rerun()


if __name__ == "__main__":
    main()
