# BEMS Presentation — English Script (Teleprompter)

**Target duration:** 8 minutes · ~1,170 words · pace 145 wpm
**Tone:** confident, conversational. Pause for one beat at every `||`.
**Stage directions** are in `[brackets]` — do NOT read them out loud.

---

## ① INTRO  [Slide 1 — Title]

Hi everyone, my name is Kim Sung-hyun, student ID 2021271250. ||

For my ICT Module 4 project, I built a **Smart Building Energy Anomaly Detection and Response System** — a six-stage agent pipeline that monitors a building's IoT sensors, recovers data lost to network problems, and tells the operator exactly what's going wrong and what to do about it. ||

Over the next eight minutes, I'll walk you through the architecture, and then run a live demo of the system in action. ||

[Advance to slide 3.]

---

## ② PROBLEM & SOLUTION  [Slide 3]

Modern smart buildings depend on continuous telemetry from IoT sensors — power consumption, temperature, humidity, CO₂. ||

But real networks aren't perfect. WiFi gets congested, signals attenuate between floors, and electromagnetic interference adds noise. The result is **packet loss, variable latency, and corrupted readings**. If anomalies slip through unnoticed, a fire or HVAC failure can escalate before the operator even sees it. ||

My system addresses this end-to-end. We **deliberately inject** the same kind of network degradation a real building suffers, we **recover the lost data** using classical machine learning, and we use a **deterministic rule engine** — no black-box LLM — to diagnose the root cause and recommend a specific action. ||

[Advance to slide 4.]

---

## ③ ARCHITECTURE  [Slide 4]

Here's the pipeline. **Six independent agents**, each in its own process, all communicating over REST. ||

On the left, **Generation and Transport**. In the middle, **Intelligence and Processing**. On the right, **Decision and Presentation**. ||

Three design choices are worth highlighting. ||

First — every agent talks REST, so any single stage can be replaced or moved to a different machine without touching the others. ||

Second — SQLite in WAL mode for persistence. The system survives a restart with all of its history intact. ||

Third — a background worker that **pushes** decisions every second. The dashboard never has to poll for anomalies. ||

[Advance to slide 6.]

---

## ④ STAGES 1 AND 2 — Generator and Transmitter  [Slide 6]

The **Generator** simulates four BEMS sensors per zone, with normal and anomaly thresholds taken straight from the operating spec. Every sample carries a ground-truth label, which we'll need later for evaluation. ||

The **Transmitter** then forwards each sample twice — a clean copy for evaluation, and a degraded copy for production. The degradation includes zero-point-two to one-point-five seconds of variable delay, a ten percent packet drop rate, and additional Gaussian noise simulating electromagnetic interference. ||

[Advance to slide 7.]

---

## ⑤ STAGE 3 — Collector  [Slide 7]

The **Collector** is a FastAPI service. It persists everything to SQLite and exposes eleven endpoints. The most important for our demo is `/inject`, which lets the user push custom test samples into the pipeline. ||

[Advance to slide 8.]

---

## ⑥ STAGE 4 — ML Processor  [Slide 8]

The **ML Processor** does two jobs. ||

First, it **reindexes** the per-zone time series and **linearly interpolates** any sequence numbers the network dropped. ||

Second, it runs three anomaly detectors in parallel — a **robust Z-score** based on median absolute deviation, the **hard physical thresholds** from the spec, and **scikit-learn's IsolationForest** for multivariate patterns no single sensor would catch on its own. ||

[Advance to slide 9.]

---

## ⑦ STAGE 5 — Decision  [Slide 9 — slow down here, this is the differentiator]

This is the stage that makes the system **explainable**. ||

The Decision Agent walks a **nine-rule runbook** from top to bottom. First match wins. Each rule lists the sensor signals that must fire, **and** the ones that must NOT fire. ||

So, for example — if temperature and CO₂ go high together, but humidity stays normal, the rule engine returns `fire_risk` with a specific recommended action: verify smoke detectors and dispatch an on-site inspection. ||

Every decision is auditable. There is no neural network making opaque judgments — every alert can be traced back to exactly which rule fired and why. ||

[Advance to slide 10, hold for 3 seconds, then ⌘+Tab to the browser.]

---

## ⑧ LIVE DEMO — Operations  [Switch to browser, Operations tab]

Let me show you this running. This is the operations console at localhost:8501. ||

Across the top, a KPI strip — three active zones, several thousand packets received, around eleven percent packet loss, decisions made in the background by the worker. ||

On the left, every service in the pipeline is reporting Operational. On the right, a **Decision Timeline** that highlights Critical events as red stars and Warnings as orange diamonds. ||

Right now, everything is nominal. So let me trigger an anomaly. ||

---

## ⑨ LIVE DEMO — Inject a scenario  [Click "Scenario Lab" tab]

I'll switch to the **Scenario Lab** tab. Five preset failure scenarios are ready to inject. ||

I'll pick `fire_risk` and inject it into Zone-A. ||

[Click the **Inject** button under fire_risk for Zone-A. Wait three seconds.]

The background worker picks this up within one second. Let's see what it decided. ||

---

## ⑩ LIVE DEMO — Alerts  [Click "Alerts" tab]

And here it is. A **Critical event** in Zone-A. ||

The rule engine has classified it as a **possible fire or thermal event**. The recommended action — verify smoke detectors and dispatch an on-site inspection. ||

You can see the exact evidence: which sensors fired, their values, and their Z-scores. The operator can also filter the feed by severity or zone and export the result to CSV — that's how the daily ops report gets generated. ||

---

## ⑪ LIVE DEMO — Telemetry  [Click "Telemetry" tab]

The **Telemetry tab** lets the operator pick any zone and inspect all four sensors in real time. ||

The gray dots are the raw degraded readings. The blue line is the ML-recovered signal. Red X marks are Z-score or hard-threshold anomalies. Purple circles are IsolationForest detections. The green band is the normal operating range. ||

The spike we just injected is clearly visible. ||

---

## ⑫ LIVE DEMO — Quality Metrics  [Click "Quality Metrics" tab]

Because every sample carries a ground-truth label, I can **quantitatively evaluate** the pipeline. ||

The top table shows per-sensor interpolation MAE — how close the recovered values are to the truth. ||

The bottom table shows **precision, recall, and F1** for each detector. As you'd expect, the **union** of all three detectors gives the highest F1 — combining the strengths of statistical, multivariate, and rule-based methods. ||

[⌘+Tab back to slides. Advance to slide 14.]

---

## ⑬ CONCLUSION  [Slide 14]

To wrap up — what I built. ||

A fully decoupled six-stage pipeline that survives ten percent packet loss while keeping the time series intact. An ensemble of three complementary anomaly detectors. A nine-rule explainable decision engine. An enterprise-style operations console. And twenty-four unit tests, including a regression test for a real deadlock bug I found and fixed during development. ||

What's next. Fitting the simulator to the actual ASHRAE dataset for realistic distributions. Adding an LSTM-based detector to compare against IsolationForest. Switching from polling to WebSocket push. And integrating Slack and email for the alert channel. ||

---

## ⑭ CLOSE

That's the BEMS Anomaly Operations Center. ||

Thank you for watching — I'm happy to take any questions in the live session. ||

[Hold on the Thank-you slide for 3 seconds, then stop recording.]

---

## Voice-coaching cheat sheet

- **Pace**: don't rush. 145 words a minute feels slow when you're nervous, but it sounds confident.
- **Lower your pitch on numbers** — "ten percent packet drop", "nine-rule engine" — they stick better.
- **Pause one beat at every `||`**. Half a second. It feels long; it isn't.
- **Smile slightly** while you speak. The mic picks up the warmth.
- **Don't apologize** for stumbles — keep going. The grader is listening for content, not perfection.

## Words you might want to rehearse

| Word | Phonetic |
|------|----------|
| anomaly | uh-NOM-uh-lee |
| pipeline | PIPE-line |
| interpolation | in-tur-puh-LAY-shun |
| IsolationForest | I-so-LAY-shun for-est |
| scikit-learn | SY-kit learn |
| FastAPI | fast A-P-I |
| SQLite | sequel-LITE  (or S-Q-L-ite) |
| Streamlit | STREAM-lit |
| Z-score | zee-score (US) or zed-score (UK) |
