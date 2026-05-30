# BEMS Presentation — English Recording Script

Target length: **8 minutes** (sweet spot inside the 5–10 min window).
Tone: confident, conversational, not over-rehearsed. Pause briefly between sections.

| Time | Section | Slide / View |
|------|---------|--------------|
| 0:00 – 0:30 | Intro & Title | Slide 1 |
| 0:30 – 1:15 | Problem & Solution | Slide 3 |
| 1:15 – 2:00 | System Architecture | Slide 4 |
| 2:00 – 3:00 | Pipeline stages 1–4 (fast tour) | Slides 6, 7, 8 |
| 3:00 – 3:45 | Decision rule engine | Slide 9 |
| 3:45 – 4:15 | Switch to live dashboard | Browser |
| 4:15 – 5:30 | **LIVE DEMO** — inject scenario | Browser tabs |
| 5:30 – 6:30 | Telemetry + Quality Metrics | Browser tabs |
| 6:30 – 7:30 | What I learned / Future work | Slide 14 |
| 7:30 – 8:00 | Close + thanks | Slide 14 |

---

## 0:00 — Intro (Slide 1)

> "Hi everyone, I'm Kim Sung-hyun, student ID 2021271250. This is my ICT Module 4 intermediate project: a Smart Building Energy Anomaly Detection and Response System. Over the next eight minutes I'll walk through how it works, then run a live demo."

(Click to slide 3.)

---

## 0:30 — Problem & Solution (Slide 3)

> "Smart buildings depend on continuous IoT telemetry — power, temperature, humidity, CO₂. But real networks aren't perfect: WiFi congestion, inter-floor signal attenuation, and electromagnetic interference cause **packet loss, variable delay, and noisy readings**. If anomalies slip through, a fire or HVAC failure can escalate before the operator even sees it."

> "My system solves this with a six-stage agent pipeline. We deliberately inject network degradation, recover lost data with machine learning, and use a deterministic rule engine to diagnose root cause and recommend an action."

(Click to slide 4.)

---

## 1:15 — Architecture (Slide 4)

> "Here's the pipeline. Six independent agents, each in its own process, all communicating over REST. Generation and transport on the left, intelligence and processing in the middle, decision and presentation on the right."

> "Three key design choices: REST API between every agent so they can be replaced or distributed; SQLite in WAL mode for persistence across restarts; and a background worker that pushes decisions every second — the dashboard never has to poll."

(Click to slide 6.)

---

## 2:00 — Stages 1 + 2 (Slide 6)

> "Stage one, the **Generator**, simulates four BEMS sensors per zone, with normal and anomaly thresholds from the operating spec. Every sample carries a ground-truth label."

> "Stage two, the **Transmitter**, intentionally degrades the network: zero-point-two to one-point-five second variable delay, ten percent packet drop, and Gaussian sensor noise."

(Click to slide 7. Keep this fast — 25 seconds.)

---

## 2:25 — Stage 3 Collector (Slide 7)

> "Stage three is the **Collector** — a FastAPI service. It persists everything to SQLite and exposes eleven endpoints. The most important is `/inject`, which lets the user push custom test samples into the pipeline."

(Click to slide 8.)

---

## 2:50 — Stage 4 ML Processor (Slide 8)

> "Stage four, the **ML Processor**. It reindexes the per-zone time series, **linearly interpolates** the dropped sequences, then runs three detectors in parallel: a robust Z-score using median absolute deviation, the hard physical thresholds, and **scikit-learn's IsolationForest** for multivariate patterns no single sensor would catch alone."

(Click to slide 9.)

---

## 3:00 — Stage 5 Decision (Slide 9)

> "Stage five is what makes this **explainable**. The Decision Agent walks a nine-rule runbook from top to bottom — first match wins. Each rule lists the sensor signals that must fire and the ones that must NOT fire."

> "So if temperature and CO₂ go high together but humidity stays normal, the rule engine returns `fire_risk` with a specific recommended action: verify smoke detectors, dispatch on-site inspection. No black-box LLM — everything is auditable."

(Click to slide 10, hold for 5 seconds, then **Cmd+Tab to the browser**.)

---

## 3:45 — Switch to Live Dashboard

> "Let me show this running. Here's the operations console at localhost:8501."

(You should already be on the **Operations** tab.)

---

## 4:00 — LIVE DEMO: Operations tab

> "Top row — KPI strip: three active zones, eight thousand packets received, eleven percent packet loss, decisions made in the background."

> "Left side: every service in the pipeline is operational. Right side: a decision timeline that highlights Critical events as red stars and Warning as orange diamonds. Right now everything is nominal."

(Pause 2 seconds.)

---

## 4:20 — LIVE DEMO: inject a scenario

> "Let me trigger an anomaly. I'll go to the **Scenario Lab** tab."

(Click **Scenario Lab** tab.)

> "Five preset scenarios. I'll inject `fire_risk` into Zone-A."

(Click the **Inject** button under fire_risk for Zone-A.)

> "The background worker picks this up within one second."

(Wait ~3 seconds, then click **Alerts** tab.)

---

## 4:45 — LIVE DEMO: Alerts tab

> "And here it is in the Alerts feed: a Critical event in Zone-A. The rule engine has classified it as a possible fire or thermal event. The recommended action is to verify smoke detectors and dispatch an on-site inspection. You can also see the exact evidence — which sensors fired, with their Z-scores."

(Hover briefly over the new alert.)

> "Below the filters, the operator can export the entire filtered list to CSV — that's the daily ops report."

---

## 5:15 — LIVE DEMO: Telemetry

(Click **Telemetry** tab.)

> "On the Telemetry tab I can pick any zone and see all four sensors in real time. Gray dots are the raw degraded readings. The blue line is the ML-recovered signal. Red X marks are Z-score or hard-threshold anomalies. Purple circles are IsolationForest detections. The green band is the normal operating range."

(Briefly scroll or point at the charts.)

---

## 5:45 — LIVE DEMO: Quality Metrics

(Click **Quality Metrics** tab.)

> "Because every sample carries a ground-truth label, I can quantitatively evaluate the pipeline. Top table: per-sensor interpolation MAE — how close the recovered values are to the truth. Bottom: precision, recall, and F1 for each detector, plus the union. As you'd expect, the union has the highest F1 because it combines the strengths of all three."

---

## 6:30 — Back to slides — Conclusion (Slide 14)

(**Cmd+Tab back to slides**, advance to slide 14.)

> "To wrap up — what I built: a fully decoupled six-stage pipeline that survives ten percent packet loss while keeping the time series intact, an ensemble of three detectors, an auditable nine-rule decision engine, and an enterprise-style operations console. Twenty-four unit tests including a regression test for a real deadlock bug I found and fixed."

> "What's next: fitting the simulator to the actual ASHRAE dataset, adding LSTM-based anomaly detection for comparison, moving from polling to WebSocket push, and integrating Slack and email alerting."

---

## 7:30 — Close

> "That's the BEMS Anomaly Operations Center. Thank you — happy to take questions."

(Hold on Thank-you slide for 3 seconds, then stop recording.)

---

## Voice-coaching notes

- **Pace**: ~145 words per minute. The full script is ~1,100 words → ~7:30 reading time, which gives you breathing room.
- **Pauses**: leave half a beat after each section title above. Helps the editor and the listener.
- **Cadence**: lower your pitch on numbers ("ten percent packet drop"). Makes them memorable.
- **Avoid**: filler words ("um", "like"), reading too fast in the rule-engine section (slide 9 is the meat).
- **Mic**: a quiet room beats a fancy mic. Close windows, turn off fans, mute notifications (Do Not Disturb).
