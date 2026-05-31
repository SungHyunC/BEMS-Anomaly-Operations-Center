# BEMS — English Video Script (Teleprompter)

**Project:** Smart Building Energy — Anomaly Detection & Response System
**Presenter:** Kim Sung-hyun · 2021271250 · ICT Module 4
**Target length:** ~8 minutes (inside the 5–10 min window)
**Pace:** ~145 words/min. Pause one beat at every `||`.
**Stage directions** are in `[brackets]` — do NOT read them aloud.

---

## ① INTRO  [Slide 1 — Title]

Hi everyone, my name is Kim Sung-hyun, student ID 2021271250. ||

For my ICT Module 4 project I built a **Smart Building Energy Anomaly Detection and Response System** — a six-stage agent pipeline that monitors a building's IoT sensors, recovers data lost to network problems, and tells the operator exactly what is going wrong and what to do about it. ||

Over the next eight minutes I'll walk through the architecture, and then run a live demo. ||

[Advance to slide 2.]

---

## ② PROBLEM & SOLUTION  [Slide 3]

[If slide 2 is the agenda, click through it in ~3 seconds, then land on slide 3.]

Modern smart buildings depend on continuous telemetry — power, temperature, humidity, and CO₂. ||

But real wireless networks are not perfect. WiFi gets congested, signals attenuate between floors, and electromagnetic interference adds noise. The result is **packet loss, variable delay, and corrupted readings**. If an anomaly slips through unnoticed, a fire or an HVAC failure can escalate before the operator ever sees it. ||

My system solves this end to end. We **deliberately inject** the same network degradation a real building suffers, we **recover the lost data** with machine learning, and we use a **deterministic rule engine** — no black-box model — to diagnose the root cause and recommend a concrete action. ||

[Advance to slide 4.]

---

## ③ ARCHITECTURE  [Slide 4]

Here is the pipeline. **Six independent agents**, each in its own process, all communicating over REST. ||

On the left, generation and transport. In the middle, intelligence and processing. On the right, decision and presentation. ||

Three design choices matter. First — every agent talks REST, so any stage can be replaced or moved to another machine. Second — SQLite in WAL mode for persistence, so the system survives a restart with its history intact. Third — a background worker that **pushes** decisions every second, so the dashboard never has to poll for anomalies. ||

[Advance to slide 6.]

---

## ④ STAGES 1 AND 2 — Generator & Transmitter  [Slide 6]

The **Generator** simulates four BEMS sensors across three building zones, with normal and anomaly thresholds taken from the operating spec. Every sample carries a ground-truth label — which we'll need later for evaluation. ||

The **Transmitter** then forwards each sample twice — a clean copy for evaluation, and a degraded copy for production. The degradation adds zero-point-two to one-point-five seconds of variable delay, a ten percent packet drop rate, and Gaussian sensor noise. ||

[Advance to slide 7.]

---

## ⑤ STAGE 3 — Collector  [Slide 7]

The **Collector** is a FastAPI service. It persists everything to SQLite and exposes twelve REST endpoints. The most important for the demo is `/inject`, which lets the user push custom test samples into the pipeline. It also runs the background worker that produces decisions. ||

[Advance to slide 8.]

---

## ⑥ STAGE 4 — ML Processor  [Slide 8]

The **ML Processor** does two jobs. ||

First, it reindexes each zone's time series and **linearly interpolates** any sequence numbers the network dropped — so the signal has no gaps. ||

Second, it runs **three anomaly detectors in parallel**: a robust Z-score based on median absolute deviation, the hard physical thresholds from the spec, and **scikit-learn's IsolationForest** for multivariate patterns that no single sensor would catch on its own. ||

[Advance to slide 9.]

---

## ⑦ STAGE 5 — Decision  [Slide 9 — slow down, this is the differentiator]

This is the stage that makes the system **explainable**. ||

The Decision Agent walks a **nine-rule runbook** from top to bottom — first match wins. Each rule lists the sensor signals that must fire, **and** the ones that must not. ||

So, for example — if temperature and CO₂ rise together but humidity stays normal, the engine returns `fire_risk`, with a specific recommended action: verify smoke detectors and dispatch an on-site inspection. ||

Every alert is auditable. There is no neural network making opaque judgments — each decision traces back to exactly which rule fired and why. ||

[Advance to slide 10, hold three seconds, then switch to the browser — ⌘+Tab.]

---

## ⑧ LIVE DEMO — Building View  [Browser · Building tab]

Let me show it running. This is the operations console at localhost:8501. ||

The first thing you see is the **Building tab** — a live floor-plan view of the building. Each zone glows green when nominal, orange for a warning, and red for a critical event. You can also drill into any zone to see its live sensor charts directly here. ||

Right now all three zones are green. Let me click over to the **Operations tab** for the system health overview. ||

---

## ⑨ LIVE DEMO — Operations  [Click "Operations" tab]

Across the top, a KPI strip — three active zones, several thousand packets received, around eleven percent packet loss, and the decisions made in the background. ||

On the left, every service in the pipeline is reporting Operational. On the right, a **decision timeline** that highlights Critical events as red stars and Warnings as orange diamonds. Right now everything is nominal — so let me trigger an anomaly. ||

---

## ⑩ LIVE DEMO — Inject a scenario  [Click "Scenario Lab" tab]

I'll open the **Scenario Lab** tab. There are five preset failure scenarios. ||

I'll inject `fire_risk` into Zone-A. ||

[Click the **Inject into Zone-A** button under fire_risk.]

The dashboard waits briefly, then shows the result card immediately — the background worker processes the sample within one second. ||

---

## ⑪ LIVE DEMO — Alerts  [Click "Alerts" tab]

And here it is — a **Critical event** in Zone-A. ||

The rule engine classified it as a possible fire or thermal event. The recommended action: verify smoke detectors and dispatch an on-site inspection. ||

You can see the exact evidence — which sensors fired, their values, and their Z-scores. The operator can filter the feed by severity or zone, and export it to CSV for the daily report. ||

---

## ⑫ LIVE DEMO — Telemetry  [Click "Telemetry" tab]

The **Telemetry** tab lets the operator pick any zone and inspect all four sensors in real time. ||

The green band is the normal range; the red shading is the danger zone. The blue line is the ML-recovered signal. Hollow diamonds mark the points that were dropped in transit and reconstructed by interpolation. Red crosses are threshold or Z-score anomalies, and purple circles are IsolationForest detections. ||

The spike I just injected is clearly visible. ||

---

## ⑬ LIVE DEMO — Quality Metrics  [Click "Quality Metrics" tab]

Because every sample carries a ground-truth label, I can **quantitatively evaluate** the pipeline. ||

The top table shows per-sensor interpolation error — how close the recovered values are to the truth. The bottom shows precision, recall, and F1 for each detector. As you'd expect, the **union** of all three detectors gives the highest F1, because it combines a statistical, a multivariate, and a rule-based method. ||

[One optional line if you enabled it:] And the whole console can switch between English and Korean from the sidebar. ||

[⌘+Tab back to the slides. Advance to slide 14.]

---

## ⑭ CONCLUSION  [Slide 14]

To wrap up — what I built. ||

A fully decoupled six-stage pipeline that survives ten percent packet loss while keeping the time series intact. An ensemble of three complementary detectors. A nine-rule explainable decision engine. And an enterprise-style operations console — with twenty-four unit tests, including a regression test for a real deadlock bug I found and fixed during development. ||

What's next: fitting the simulator to the real ASHRAE dataset, adding an LSTM detector to compare against IsolationForest, moving from polling to WebSocket push, and wiring up Slack and email alerting. ||

---

## ⑮ CLOSE

That's the BEMS Anomaly Operations Center. ||

Thank you for watching — I'm happy to take questions in the live session. ||

[Hold on the Thank-you slide for three seconds, then stop the recording.]

---

## Voice-coaching cheat sheet

- **Don't rush.** 145 words a minute feels slow when you're nervous but sounds confident.
- **Lower your pitch on numbers** — "ten percent packet drop", "nine-rule engine". They stick.
- **Pause one beat at every `||`.** Half a second. It feels long; it isn't.
- **Don't apologize** for small stumbles — keep going. Graders listen for content, not perfection.
- **Quiet room beats a fancy mic.** Close windows, turn on Do Not Disturb, plug in the charger so the fan stays quiet.

## Words worth rehearsing

| Word | Say it like |
|------|-------------|
| anomaly | uh-NOM-uh-lee |
| interpolation | in-tur-puh-LAY-shun |
| IsolationForest | I-so-LAY-shun for-est |
| scikit-learn | SY-kit learn |
| FastAPI | fast-A-P-I |
| SQLite | sequel-LITE |
| Z-score | zee-score |
| deterministic | dee-ter-MIN-istic |
