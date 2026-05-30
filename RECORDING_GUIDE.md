# Recording Guide — BEMS ICT Module 4

Mac-only recipe. Goal: clean 1080p screen recording with crisp narration, ~8 minutes, ready to upload as YouTube **Unlisted**.

## 1. Tool choice (pick one)

### Option A — QuickTime Player  (simplest, zero install)
Built into macOS. Records screen + mic. Limitation: can't show your webcam overlay or switch mics on the fly.

### Option B — OBS Studio  (recommended)
Free download from <https://obsproject.com>. Lets you:
- show a small webcam circle in the corner (presence is engaging)
- toggle between PowerPoint and the browser as separate scenes
- record at exactly 1920×1080 30 fps
- monitor audio level in real time so you don't clip

If you have 15 minutes to spare, install OBS — the result is noticeably more professional.

### Option C — Loom  (browser-based, easiest sharing)
<https://www.loom.com>. Free tier allows 5 min/video though, so you'd need the paid plan or split into chapters. **Skip unless you already have a paid account.**

## 2. Pre-flight checklist (do in this order)

```
☐ Close every app you don't need (Slack, Mail, Messages, Chrome tabs with personal stuff)
☐ Enable Do Not Disturb:  Control Center → Focus → Do Not Disturb
☐ Hide the menu bar clock notifications:  irrelevant tabs, screenshots
☐ Plug in your charger (laptop fan ramps when on battery — picks up on mic)
☐ Set screen resolution to 1920×1080 (System Settings → Displays → Scaled → "Larger Text" off)
☐ Set dark/light mode the way you want — Light mode makes the dashboard pop
☐ Quit Spotify, iTunes (no autoplay surprises)
☐ Test mic level — say "one two three" → playback should be clear, no clipping
☐ Make sure Caps Lock is off (it changes typing in the dashboard fields)
```

## 3. Stage the recording

```
☐ Start the pipeline:   ./run_all.sh    (in a terminal you can hide later)
☐ Wait 30 seconds so the dashboard has some data already
☐ Open browser to http://localhost:8501  → "Operations" tab
☐ Open BEMS_Presentation.pptx in PowerPoint (or Keynote)
☐ Start slideshow mode (F5 in PowerPoint, ⌘⏎ in Keynote)
☐ Park PowerPoint on slide 1, browser one ⌘+Tab away
☐ Open DEMO_SCRIPT.md in a second display, on your phone, or as a printed page
   — do NOT keep it on the recording screen
```

## 4. Record

### With QuickTime
1. `QuickTime Player` → `File` → `New Screen Recording`.
2. Click the small arrow next to record — set **Microphone: Built-in (or your AirPods)**, **Quality: Maximum**.
3. Click record, then click anywhere to record the **whole screen**.
4. Run through the script (~8 min). Don't restart on a small stumble — keep going.
5. Stop with `⌘⌃Esc` or the menu-bar icon.

### With OBS
1. Settings → Output → Recording Path: `~/Desktop`. Format: MP4. Encoder: hardware (Apple VT).
2. Settings → Video → Base + Output Resolution: `1920×1080`. FPS: 30.
3. Sources → add a **Display Capture** for your main display, then a **Window Capture** for PowerPoint (so you can switch scenes cleanly).
4. Optional: add a **Video Capture Device** for FaceTime HD camera, mask it into a circle, park it bottom-right.
5. Hit **Start Recording**. Output lands in `~/Desktop`.

## 5. Quick edit (optional, 5 min)

If you have a stumble or want to trim:

- **iMovie** (free, built-in): drag the file in, split with `⌘B`, delete the bad chunk, export at 1080p.
- **QuickTime alone**: `Edit` → `Trim…` only lets you cut head/tail.

Don't over-edit. Examiners care about content, not polish.

## 6. Upload — YouTube Unlisted (recommended)

1. Go to <https://studio.youtube.com> → **Create** → **Upload videos**.
2. Drag your MP4.
3. **Title**: `BEMS Anomaly Operations Center — ICT Module 4 (2021271250 Kim Sung-hyun)`
4. **Description**: paste the project summary (suggestion below).
5. **Audience**: "No, it's not made for kids".
6. **Visibility**: choose **Unlisted**. (Anyone with the link can watch; not in search.)
7. Click **Save**. Copy the share URL — that's what you submit.

### Suggested description

```
ICT Module 4 — Intermediate Project
Smart Building Energy Anomaly Detection & Response System

A six-stage agent pipeline that simulates BEMS sensor telemetry, injects realistic
network degradation (delay / packet drop / noise), recovers lost data with linear
interpolation, detects anomalies with three parallel detectors (robust Z-score,
IsolationForest, hard thresholds), and diagnoses root cause with a nine-rule
deterministic engine.

Stack: Python 3.11 · FastAPI · SQLite (WAL) · scikit-learn · Streamlit + Plotly.
24 pytest cases, 2,792 lines of code.

Submitted by: Kim Sung-hyun · 2021271250
```

## 7. Upload — Google Drive (alternative)

1. Drag the MP4 into Drive.
2. Right-click → **Share** → **Anyone with the link** → **Viewer**.
3. Copy link → submit.

## 8. Final submission checklist

```
☐ Video plays start-to-finish in an incognito window (link is actually public)
☐ Audio is audible without earphones
☐ Length is between 5:00 and 10:00
☐ Korean did not slip in anywhere
☐ Live demo segment is visible (~1.5 min of dashboard footage)
☐ Slide content is readable (no microscopic text)
☐ Link submitted to instructor at least 1 week before Friday presentation
```

## 9. Common gotchas

- **Mic too quiet** → speak ~15 cm from mouth, not 50 cm. If using AirPods, the laptop mic might still grab fan noise. Force AirPods in System Settings → Sound → Input.
- **Cursor moves jerky** → enable "Reduce motion" off, and use the trackpad slowly. Don't ping-pong between apps.
- **Dashboard shows zero data** → you forgot `./run_all.sh`, or you reset the DB right before recording.
- **PowerPoint shows presenter view on the recording** → switch to "Use Presenter View" OFF in the Slide Show menu, or move presenter notes to a second display.
- **Recording too long (over 10 min)** → cut the rule-engine narration in half, and skip the "future work" half of slide 14. Most graders won't watch past 8 min.
