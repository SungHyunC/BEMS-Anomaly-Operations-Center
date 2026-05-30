// BEMS Anomaly Operations Center — ICT Module 4 presentation builder.
// Usage: node build_ppt.js   →   BEMS_Presentation.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";          // 13.3" × 7.5"
pres.author  = "Kim Sung-hyun · 2021271250";
pres.title   = "BEMS Anomaly Operations Center";
pres.company = "ICT Module 4";

// ───────────────── palette (matches the dashboard) ─────────────────
const C = {
  navy:        "0F1B3D",
  navy2:       "1A2A5E",
  primary:     "1F5DDE",
  primaryBg:   "E8F0FF",
  accent:      "6A4CFF",
  accentBg:    "EDE7FF",
  text:        "172B4D",
  text2:       "42526E",
  muted:       "6B778C",
  border:      "E1E4E8",
  surface:     "FFFFFF",
  surface2:    "F5F7FA",
  ok:          "1F7A4D",
  okBg:        "E3F5EC",
  warn:        "9A5B00",
  warnBg:      "FFF4E0",
  crit:        "A1271D",
  critBg:      "FDE4E1",
  white:       "FFFFFF",
};

const FONT  = "Segoe UI";   // English deck font
const FONTm = "Consolas";   // monospace

const W = 13.3, H = 7.5;
const MARGIN = 0.55;

// ───────────────── helpers ─────────────────
const shadow = () => ({ type: "outer", color: "0F1B3D",
                        blur: 10, offset: 2, angle: 90, opacity: 0.08 });

function lightBg(slide) {
  slide.background = { color: C.surface2 };
}
function darkBg(slide) {
  slide.background = { color: C.navy };
}

function pageHeader(slide, kicker, title, sub) {
  slide.addText(kicker, {
    x: MARGIN, y: 0.40, w: W - 2 * MARGIN, h: 0.28,
    fontFace: FONT, fontSize: 11, color: C.primary, bold: true,
    charSpacing: 4, margin: 0,
  });
  slide.addText(title, {
    x: MARGIN, y: 0.70, w: W - 2 * MARGIN, h: 0.7,
    fontFace: FONT, fontSize: 30, color: C.text, bold: true, margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: MARGIN, y: 1.42, w: W - 2 * MARGIN, h: 0.4,
      fontFace: FONT, fontSize: 14, color: C.muted, margin: 0,
    });
  }
  // thin divider
  slide.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: sub ? 1.90 : 1.55, w: W - 2 * MARGIN, h: 0.012,
    fill: { color: C.border }, line: { color: C.border, width: 0 },
  });
}

function pageFooter(slide, page, total) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: H - 0.45, w: W - 2 * MARGIN, h: 0.01,
    fill: { color: C.border }, line: { color: C.border, width: 0 },
  });
  slide.addText("BEMS Anomaly Operations Center · ICT Module 4 · Kim Sung-hyun 2021271250", {
    x: MARGIN, y: H - 0.36, w: 8, h: 0.3,
    fontFace: FONT, fontSize: 9, color: C.muted, margin: 0,
  });
  slide.addText(`${page} / ${total}`, {
    x: W - MARGIN - 1.0, y: H - 0.36, w: 1.0, h: 0.3,
    fontFace: FONT, fontSize: 9, color: C.muted, align: "right", margin: 0,
  });
}

function card(slide, x, y, w, h, fillColor = C.surface) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor },
    line: { color: C.border, width: 0.75 },
    shadow: shadow(),
  });
}

function pill(slide, x, y, label, kind = "info", opts = {}) {
  const palette = {
    ok:    { bg: C.okBg,      fg: C.ok      },
    warn:  { bg: C.warnBg,    fg: C.warn    },
    crit:  { bg: C.critBg,    fg: C.crit    },
    info:  { bg: C.primaryBg, fg: C.primary },
    muted: { bg: "EEF0F3",    fg: C.text2   },
    accent:{ bg: C.accentBg,  fg: C.accent  },
  }[kind];
  // generous width so long labels like OPERATIONAL never wrap
  const fontSize = opts.fontSize || 8.5;
  const charW = fontSize * 0.012;  // empirical
  const w = opts.w || Math.max(0.55, 0.30 + label.length * charW);
  const h = opts.h || 0.26;
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: palette.bg }, line: { width: 0 },
  });
  slide.addText(label, {
    x, y, w, h,
    fontFace: FONT, fontSize, color: palette.fg, bold: true,
    align: "center", valign: "middle", margin: 0, charSpacing: 2,
  });
  return w;
}

const TOTAL = 14;

// ════════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); darkBg(s);

  // big diamond accent
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.05,
    fill: { color: C.primary }, line: { width: 0 },
  });
  // logo mark
  s.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: 0.7, w: 0.55, h: 0.55,
    fill: { color: C.primary }, line: { width: 0 },
    rotate: 45,
  });
  s.addText("◆", {
    x: MARGIN, y: 0.7, w: 0.55, h: 0.55,
    fontFace: FONT, fontSize: 22, color: C.white,
    align: "center", valign: "middle", margin: 0, bold: true,
  });
  s.addText("BEMS · Operations Console", {
    x: MARGIN + 0.75, y: 0.78, w: 6, h: 0.45,
    fontFace: FONT, fontSize: 13, color: "B6C4E5", bold: true, charSpacing: 3,
  });

  // title
  s.addText("Smart Building Energy", {
    x: MARGIN, y: 2.0, w: W - 2 * MARGIN, h: 0.9,
    fontFace: FONT, fontSize: 44, color: C.white, bold: true, margin: 0,
  });
  s.addText("Anomaly Detection & Response System", {
    x: MARGIN, y: 2.9, w: W - 2 * MARGIN, h: 0.9,
    fontFace: FONT, fontSize: 38, color: C.white, bold: true, margin: 0,
  });
  s.addText("6-stage agent pipeline · multi-zone telemetry · ML recovery · rule-engine diagnostics", {
    x: MARGIN, y: 4.0, w: W - 2 * MARGIN, h: 0.5,
    fontFace: FONT, fontSize: 16, color: "B6C4E5", margin: 0,
  });

  // info block
  s.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: 5.2, w: 5.0, h: 1.6,
    fill: { color: C.navy2 }, line: { color: C.primary, width: 1 },
  });
  s.addText([
    { text: "ICT Module 4 · Intermediate Project\n", options: { fontFace: FONT, fontSize: 11, color: "B6C4E5", bold: true, charSpacing: 2 } },
    { text: "Kim Sung-hyun  · 2021271250\n", options: { fontFace: FONT, fontSize: 22, color: C.white, bold: true } },
    { text: "Individual Project", options: { fontFace: FONT, fontSize: 12, color: "B6C4E5" } },
  ], { x: MARGIN + 0.3, y: 5.35, w: 4.7, h: 1.4, margin: 0 });

  // 6 chips on right
  const chips = ["Python 3.11+", "FastAPI", "SQLite", "scikit-learn",
                 "Streamlit", "Plotly", "Pytest"];
  let cx = 7.0; let cy = 5.4;
  chips.forEach((label, i) => {
    const w = 0.3 + label.length * 0.11;
    s.addShape(pres.shapes.RECTANGLE, {
      x: cx, y: cy, w, h: 0.4,
      fill: { color: C.navy2 }, line: { color: C.primary, width: 0.75 },
    });
    s.addText(label, {
      x: cx, y: cy, w, h: 0.4,
      fontFace: FONT, fontSize: 11, color: C.white, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
    cx += w + 0.12;
    if (cx > W - MARGIN - 1.5) { cx = 7.0; cy += 0.55; }
  });

  // bottom date
  s.addText("2026 · Spring Semester", {
    x: MARGIN, y: H - 0.45, w: W - 2 * MARGIN, h: 0.3,
    fontFace: FONT, fontSize: 10, color: "8FA0C8", margin: 0,
  });
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 2 — AGENDA
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "AGENDA", "Agenda", "We'll walk through how the system works and what each component does, in order.");

  const items = [
    ["01", "Project Overview",         "Problem definition and approach"],
    ["02", "System Architecture",        "Six-Stage Agent Pipeline"],
    ["03", "Tech Stack",             "Libraries used and code stats"],
    ["04", "Stage 1·2  Data Generation",  "Generator + Transmitter"],
    ["05", "Stage 3  Collector",     "FastAPI + SQLite hub"],
    ["06", "Stage 4  ML Processor",  "Interpolation + 3-detector ensemble"],
    ["07", "Stage 5  Decision",      "Deterministic rule engine"],
    ["08", "Stage 6  Dashboard",     "Enterprise operations console"],
    ["09", "Key Capabilities",          "What You Can Do With It"],
    ["10", "Conclusion + Future Work",        "Results and next steps"],
  ];
  const colW = (W - 2 * MARGIN - 0.4) / 2;
  items.forEach((it, i) => {
    const col = i < 5 ? 0 : 1;
    const row = i % 5;
    const x = MARGIN + col * (colW + 0.4);
    const y = 2.35 + row * 0.85;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: colW, h: 0.7, fill: { color: C.surface }, line: { color: C.border, width: 0.75 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h: 0.7, fill: { color: C.primary }, line: { width: 0 },
    });
    s.addText(it[0], {
      x: x + 0.18, y, w: 0.55, h: 0.7,
      fontFace: FONTm, fontSize: 16, color: C.primary, bold: true,
      align: "left", valign: "middle", margin: 0,
    });
    s.addText(it[1], {
      x: x + 0.82, y: y + 0.08, w: colW - 1.0, h: 0.32,
      fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
    });
    s.addText(it[2], {
      x: x + 0.82, y: y + 0.36, w: colW - 1.0, h: 0.32,
      fontFace: FONT, fontSize: 10, color: C.muted, margin: 0,
    });
  });

  pageFooter(s, 2, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 3 — PROJECT OVERVIEW (Problem + Solution)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "01  ·  PROJECT OVERVIEW", "Smart Building Energy Anomaly Detection",
             "Why this problem matters, and how it is solved");

  // Two columns: Problem | Solution
  const left = MARGIN;
  const colW = (W - 2 * MARGIN - 0.4) / 2;

  // ── Problem
  card(s, left, 2.3, colW, 4.4);
  s.addShape(pres.shapes.RECTANGLE, {
    x: left, y: 2.3, w: 0.08, h: 4.4, fill: { color: C.crit }, line: { width: 0 },
  });
  s.addText("Problem", {
    x: left + 0.3, y: 2.4, w: colW - 0.4, h: 0.4,
    fontFace: FONT, fontSize: 16, color: C.text, bold: true, margin: 0,
  });
  s.addText("A smart building's IoT sensor network suffers from wireless interference, inter-floor signal attenuation, and congestion.", {
    x: left + 0.3, y: 2.85, w: colW - 0.5, h: 0.7,
    fontFace: FONT, fontSize: 12, color: C.text2, margin: 0,
  });

  const problems = [
    ["⚠", "Packet Loss",       "Data vanishes in transit, leaving gaps in the analysis"],
    ["⏱", "Variable Delay",       "WiFi congestion causes irregular 0.5–3 s delays"],
    ["📉", "Sensor Noise",    "EM interference adds Gaussian noise to readings"],
    ["🔥", "Missed Anomalies",  "Fire, HVAC failure, etc. escalate before the operator notices"],
  ];
  problems.forEach((p, i) => {
    const y = 3.7 + i * 0.62;
    s.addText(p[0], {
      x: left + 0.3, y, w: 0.35, h: 0.5,
      fontFace: FONT, fontSize: 14, color: C.crit,
      align: "center", valign: "top", margin: 0,
    });
    s.addText(p[1], {
      x: left + 0.7, y, w: colW - 0.9, h: 0.26,
      fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
    });
    s.addText(p[2], {
      x: left + 0.7, y: y + 0.24, w: colW - 0.9, h: 0.34,
      fontFace: FONT, fontSize: 10, color: C.muted, margin: 0,
    });
  });

  // ── Solution
  const rx = left + colW + 0.4;
  card(s, rx, 2.3, colW, 4.4);
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: 2.3, w: 0.08, h: 4.4, fill: { color: C.ok }, line: { width: 0 },
  });
  s.addText("Solution", {
    x: rx + 0.3, y: 2.4, w: colW - 0.4, h: 0.4,
    fontFace: FONT, fontSize: 16, color: C.text, bold: true, margin: 0,
  });
  s.addText("Six-Stage Agent Pipeline — 실제 Network degradation를 의도적으로 주입하고, ML로 Recover하고, 룰 엔진으로 Diagnose합니다.", {
    x: rx + 0.3, y: 2.85, w: colW - 0.5, h: 0.7,
    fontFace: FONT, fontSize: 12, color: C.text2, margin: 0,
  });

  const solutions = [
    ["✓", "Recover",     "Linear interpolation fills dropped sequences for a gapless series"],
    ["✓", "Detect",     "Z-score · hard threshold · IsolationForest — a 3-detector ensemble"],
    ["✓", "Diagnose",     "Match the fired-sensor pattern to 9 rules to infer root cause"],
    ["✓", "Operate",     "Streamlit 콘솔 — 6탭 Operate 화면과 시나리오 주입 기능"],
  ];
  solutions.forEach((p, i) => {
    const y = 3.7 + i * 0.62;
    s.addText(p[0], {
      x: rx + 0.3, y, w: 0.35, h: 0.5,
      fontFace: FONT, fontSize: 14, color: C.ok, bold: true,
      align: "center", valign: "top", margin: 0,
    });
    s.addText(p[1], {
      x: rx + 0.7, y, w: colW - 0.9, h: 0.26,
      fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
    });
    s.addText(p[2], {
      x: rx + 0.7, y: y + 0.24, w: colW - 0.9, h: 0.34,
      fontFace: FONT, fontSize: 10, color: C.muted, margin: 0,
    });
  });

  pageFooter(s, 3, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 4 — SYSTEM ARCHITECTURE (6-stage diagram)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "02  ·  ARCHITECTURE", "Six-Stage Agent Pipeline",
             "Each stage is an independent process; they communicate only over REST.");

  const stages = [
    { n: "①", name: "Generator",    role: "Sensor simulation",     color: C.primary },
    { n: "②", name: "Transmitter",  role: "Network degradation",       color: C.primary },
    { n: "③", name: "Collector",    role: "FastAPI hub + DB",   color: C.accent  },
    { n: "④", name: "ML Processor", role: "보간 + 이상 Detect",    color: C.accent  },
    { n: "⑤", name: "Decision",     role: "룰 엔진 Diagnose",        color: C.ok      },
    { n: "⑥", name: "Dashboard",    role: "Operate 콘솔",           color: C.ok      },
  ];

  const stageW = 1.85, stageH = 1.5;
  const totalW = stageW * 6 + 0.30 * 5;
  const startX = (W - totalW) / 2;
  const y = 2.55;

  stages.forEach((st, i) => {
    const x = startX + i * (stageW + 0.30);
    card(s, x, y, stageW, stageH);
    // top accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: stageW, h: 0.12,
      fill: { color: st.color }, line: { width: 0 },
    });
    s.addText(st.n, {
      x, y: y + 0.18, w: stageW, h: 0.5,
      fontFace: FONT, fontSize: 26, color: st.color, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.name, {
      x, y: y + 0.75, w: stageW, h: 0.35,
      fontFace: FONT, fontSize: 13, color: C.text, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.role, {
      x, y: y + 1.08, w: stageW, h: 0.35,
      fontFace: FONT, fontSize: 10, color: C.muted,
      align: "center", valign: "middle", margin: 0,
    });

    // arrow to next
    if (i < stages.length - 1) {
      const ax = x + stageW + 0.04;
      s.addShape(pres.shapes.RIGHT_TRIANGLE, {
        x: ax, y: y + stageH / 2 - 0.10, w: 0.22, h: 0.20,
        fill: { color: C.text2 }, line: { width: 0 }, rotate: 90,
      });
    }
  });

  // bottom: lifecycle labels — span exactly 2 stage columns each
  const groupW = stageW * 2 + 0.30;     // 2 cards + 1 gap between them
  const groupGap = 0.30;                // gap between two paired groups
  const groups = [
    { label: "DATA  GENERATION  &  TRANSPORT",  bg: C.primaryBg, fg: C.primary },
    { label: "INTELLIGENCE  &  PROCESSING",     bg: C.accentBg,  fg: C.accent  },
    { label: "DECISION  &  PRESENTATION",       bg: C.okBg,      fg: C.ok      },
  ];
  groups.forEach((g, i) => {
    const gx = startX + i * (groupW + groupGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x: gx, y: y + stageH + 0.40, w: groupW, h: 0.34,
      fill: { color: g.bg }, line: { width: 0 },
    });
    s.addText(g.label, {
      x: gx, y: y + stageH + 0.40, w: groupW, h: 0.34,
      fontFace: FONT, fontSize: 10, color: g.fg, bold: true,
      align: "center", valign: "middle", margin: 0, charSpacing: 3,
    });
  });

  // Key design notes
  card(s, MARGIN, 5.4, W - 2 * MARGIN, 1.6);
  s.addText("Key Design Principles", {
    x: MARGIN + 0.3, y: 5.5, w: 4, h: 0.32,
    fontFace: FONT, fontSize: 12, color: C.text, bold: true, margin: 0,
  });
  const notes = [
    ["🔌", "REST API comms",    "Loose coupling — agents can be swapped or distributed individually"],
    ["💾", "SQLite persistence",   "WAL mode for concurrent read/write · data survives restart"],
    ["⚙",  "Background worker",  "Decision pushes every 1 s — no dependence on dashboard polling"],
  ];
  const noteW = (W - 2 * MARGIN - 0.6) / 3;
  notes.forEach((nt, i) => {
    const nx = MARGIN + 0.3 + i * noteW;
    s.addText(nt[0], {
      x: nx, y: 5.95, w: 0.35, h: 0.4,
      fontFace: FONT, fontSize: 14, color: C.primary, margin: 0,
    });
    s.addText(nt[1], {
      x: nx + 0.4, y: 5.95, w: noteW - 0.45, h: 0.3,
      fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
    });
    s.addText(nt[2], {
      x: nx + 0.4, y: 6.25, w: noteW - 0.45, h: 0.65,
      fontFace: FONT, fontSize: 9.5, color: C.muted, margin: 0,
    });
  });

  pageFooter(s, 4, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 5 — TECH STACK + STATS
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "03  ·  TECH STACK", "Tech Stack & Code Stats",
             "A pure rule-engine implementation — no external LLM dependency");

  // Left: tech stack table-like grid
  const layers = [
    ["Language",           "Python 3.11+",                "Modern Python with type hints"],
    ["Agent comms",   "FastAPI · httpx",             "REST API · auto OpenAPI docs"],
    ["Persistence",         "SQLite (WAL)",                "Transactions · concurrent read/write"],
    ["Data / ML",      "NumPy · pandas · scikit-learn", "Rolling window · IsolationForest"],
    ["Dashboard",       "Streamlit + Plotly",           "Live refresh · interactive charts"],
    ["Testing",         "Pytest",                      "24 cases · incl. deadlock regression"],
    ["Version control",      "Git",                         "—"],
  ];
  const lx = MARGIN, ly = 2.30;
  const lw = 7.6;
  card(s, lx, ly, lw, 4.6);
  s.addText("LAYER", {
    x: lx + 0.25, y: ly + 0.18, w: 1.6, h: 0.3,
    fontFace: FONT, fontSize: 9, color: C.muted, bold: true, margin: 0, charSpacing: 3,
  });
  s.addText("TECHNOLOGY", {
    x: lx + 1.9, y: ly + 0.18, w: 2.4, h: 0.3,
    fontFace: FONT, fontSize: 9, color: C.muted, bold: true, margin: 0, charSpacing: 3,
  });
  s.addText("USAGE", {
    x: lx + 4.4, y: ly + 0.18, w: 3.1, h: 0.3,
    fontFace: FONT, fontSize: 9, color: C.muted, bold: true, margin: 0, charSpacing: 3,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: lx + 0.25, y: ly + 0.50, w: lw - 0.5, h: 0.01,
    fill: { color: C.border }, line: { width: 0 },
  });
  layers.forEach((row, i) => {
    const y = ly + 0.62 + i * 0.55;
    s.addText(row[0], {
      x: lx + 0.25, y, w: 1.65, h: 0.45,
      fontFace: FONT, fontSize: 12, color: C.text, bold: true,
      valign: "middle", margin: 0,
    });
    s.addText(row[1], {
      x: lx + 1.9, y, w: 2.5, h: 0.45,
      fontFace: FONTm, fontSize: 11, color: C.primary,
      valign: "middle", margin: 0,
    });
    s.addText(row[2], {
      x: lx + 4.4, y, w: 3.1, h: 0.45,
      fontFace: FONT, fontSize: 10.5, color: C.muted,
      valign: "middle", margin: 0,
    });
    if (i < layers.length - 1) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: lx + 0.25, y: y + 0.5, w: lw - 0.5, h: 0.005,
        fill: { color: "F1F2F4" }, line: { width: 0 },
      });
    }
  });

  // Right: KPI cards
  const rx = lx + lw + 0.3;
  const rw = W - rx - MARGIN;
  const kpis = [
    ["2,792",  "Lines of Code",     C.primary],
    ["6",      "Agents",            C.accent],
    ["3",      "Zones",             C.primary],
    ["3",      "ML Detectors",      C.accent],
    ["9",      "Decision Rules",    C.ok],
    ["24",     "Pytest Cases",      C.ok],
  ];
  const kpiH = 0.7;
  kpis.forEach((k, i) => {
    const y = 2.30 + i * (kpiH + 0.05);
    card(s, rx, y, rw, kpiH);
    s.addShape(pres.shapes.RECTANGLE, {
      x: rx, y, w: 0.08, h: kpiH, fill: { color: k[2] }, line: { width: 0 },
    });
    s.addText(k[0], {
      x: rx + 0.25, y, w: 1.6, h: kpiH,
      fontFace: FONT, fontSize: 22, color: C.text, bold: true,
      valign: "middle", align: "left", margin: 0,
    });
    s.addText(k[1], {
      x: rx + 1.85, y, w: rw - 2.0, h: kpiH,
      fontFace: FONT, fontSize: 11, color: C.muted,
      valign: "middle", align: "left", margin: 0, charSpacing: 2,
    });
  });

  pageFooter(s, 5, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 6 — STAGE 1+2 (Generator + Transmitter)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "04  ·  DATA  GENERATION  +  TRANSPORT",
             "Stage 1 · Generator   ▸   Stage 2 · Transmitter",
             "Synthesize sensor data, then deliberately inject real-world network degradation.");

  const colW = (W - 2 * MARGIN - 0.4) / 2;

  // ── Generator ──
  card(s, MARGIN, 2.3, colW, 4.6);
  s.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: 2.3, w: 0.08, h: 4.6, fill: { color: C.primary }, line: { width: 0 },
  });
  s.addText("①", {
    x: MARGIN + 0.25, y: 2.35, w: 0.5, h: 0.5,
    fontFace: FONT, fontSize: 22, color: C.primary, bold: true, margin: 0,
  });
  s.addText("Generator", {
    x: MARGIN + 0.8, y: 2.4, w: colW - 1, h: 0.35,
    fontFace: FONT, fontSize: 17, color: C.text, bold: true, margin: 0,
  });
  s.addText("src/agents/generator.py", {
    x: MARGIN + 0.8, y: 2.75, w: colW - 1, h: 0.3,
    fontFace: FONTm, fontSize: 10, color: C.muted, margin: 0,
  });

  s.addText("Synthesizes 4-channel BEMS sensors for 3 zones every second", {
    x: MARGIN + 0.3, y: 3.15, w: colW - 0.5, h: 0.32,
    fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
  });

  // sensor table
  const sensors = [
    ["Power (kW)",        "0 – 5",     "> 8"],
    ["Temperature (°C)",  "20 – 26",   "> 30  /  < 15"],
    ["Humidity (%)",      "40 – 60",   "> 75  /  < 25"],
    ["CO₂ (ppm)",         "400 – 800", "> 1200"],
  ];
  const tx = MARGIN + 0.3; const ty = 3.55;
  s.addText("SENSOR",  { x: tx,        y: ty, w: 2.2, h: 0.25, fontFace: FONT, fontSize: 8.5, color: C.muted, bold: true, charSpacing: 2, margin: 0 });
  s.addText("NORMAL",  { x: tx + 2.2,  y: ty, w: 1.4, h: 0.25, fontFace: FONT, fontSize: 8.5, color: C.muted, bold: true, charSpacing: 2, margin: 0 });
  s.addText("ANOMALY", { x: tx + 3.6,  y: ty, w: 1.8, h: 0.25, fontFace: FONT, fontSize: 8.5, color: C.muted, bold: true, charSpacing: 2, margin: 0 });
  sensors.forEach((row, i) => {
    const ry = ty + 0.32 + i * 0.32;
    s.addText(row[0], { x: tx,       y: ry, w: 2.2, h: 0.28, fontFace: FONT, fontSize: 10, color: C.text, margin: 0 });
    s.addText(row[1], { x: tx + 2.2, y: ry, w: 1.4, h: 0.28, fontFace: FONT, fontSize: 10, color: C.ok, bold: true, margin: 0 });
    s.addText(row[2], { x: tx + 3.6, y: ry, w: 1.8, h: 0.28, fontFace: FONT, fontSize: 10, color: C.crit, bold: true, margin: 0 });
  });

  s.addText("• Daily occupancy cycle (sin) + Gaussian noise\n• Every sample carries a ground-truth label (is_anomaly, scenario)\n• 4% chance to auto-inject one of 5 scenarios", {
    x: MARGIN + 0.3, y: 5.15, w: colW - 0.5, h: 1.65,
    fontFace: FONT, fontSize: 10.5, color: C.text2, margin: 0, paraSpaceAfter: 4,
  });

  // ── Transmitter ──
  const rx = MARGIN + colW + 0.4;
  card(s, rx, 2.3, colW, 4.6);
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: 2.3, w: 0.08, h: 4.6, fill: { color: C.primary }, line: { width: 0 },
  });
  s.addText("②", {
    x: rx + 0.25, y: 2.35, w: 0.5, h: 0.5,
    fontFace: FONT, fontSize: 22, color: C.primary, bold: true, margin: 0,
  });
  s.addText("Transmitter", {
    x: rx + 0.8, y: 2.4, w: colW - 1, h: 0.35,
    fontFace: FONT, fontSize: 17, color: C.text, bold: true, margin: 0,
  });
  s.addText("src/agents/transmitter.py", {
    x: rx + 0.8, y: 2.75, w: colW - 1, h: 0.3,
    fontFace: FONTm, fontSize: 10, color: C.muted, margin: 0,
  });

  s.addText("Takes Generator samples, deliberately degrades them, forwards to Collector", {
    x: rx + 0.3, y: 3.15, w: colW - 0.5, h: 0.32,
    fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
  });

  // constraints
  const cons = [
    ["⏱", "Transmission Delay", "0.2 – 1.5 s random delay", "Simulates WiFi congestion"],
    ["✖", "Packet Drop",         "Drops 10% of packets", "Simulates inter-floor attenuation"],
    ["≈", "Sensor Noise",        "Gaussian noise × 1.2", "Simulates EM interference"],
  ];
  cons.forEach((c, i) => {
    const y = 3.55 + i * 1.0;
    s.addShape(pres.shapes.RECTANGLE, {
      x: rx + 0.3, y, w: colW - 0.55, h: 0.85,
      fill: { color: C.surface2 }, line: { color: C.border, width: 0.5 },
    });
    s.addText(c[0], {
      x: rx + 0.4, y: y + 0.05, w: 0.4, h: 0.75,
      fontFace: FONT, fontSize: 22, color: C.crit, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(c[1], {
      x: rx + 0.85, y: y + 0.08, w: colW - 1.15, h: 0.28,
      fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
    });
    s.addText(c[2], {
      x: rx + 0.85, y: y + 0.34, w: colW - 1.15, h: 0.26,
      fontFace: FONTm, fontSize: 9.5, color: C.primary, margin: 0,
    });
    s.addText(c[3], {
      x: rx + 0.85, y: y + 0.58, w: colW - 1.15, h: 0.25,
      fontFace: FONT, fontSize: 9.5, color: C.muted, margin: 0,
    });
  });

  pageFooter(s, 6, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 7 — STAGE 3 (Collector)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "05  ·  STAGE 3", "Collector — FastAPI Hub",
             "The entry point for all data, the persistent store, and the host of the background worker.");

  // Left: API endpoints
  const lw = 7.0;
  card(s, MARGIN, 2.3, lw, 4.6);
  s.addText("REST API · /docs", {
    x: MARGIN + 0.3, y: 2.4, w: lw - 0.6, h: 0.35,
    fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
  });
  s.addText("http://127.0.0.1:8000", {
    x: MARGIN + 0.3, y: 2.7, w: lw - 0.6, h: 0.3,
    fontFace: FONTm, fontSize: 10, color: C.primary, margin: 0,
  });

  const apis = [
    ["POST", "/truth",       "Generator's clean sample (for evaluation)",        "accent"],
    ["POST", "/ingest",      "Transmitter's degraded packet",              "info"],
    ["POST", "/inject",      "User scenario or custom sample",        "info"],
    ["POST", "/reset",       "Operate 저장소 초기화",                     "crit"],
    ["GET",  "/raw",         "Buffered readings + missing-seq list",     "ok"],
    ["GET",  "/processed",   "ML Recover + 이상 플래그 프레임",            "ok"],
    ["GET",  "/decisions",   "Severity + diagnosis + action history",  "ok"],
    ["GET",  "/stats",       "Per-zone packet stats + worker state",            "ok"],
    ["GET",  "/evaluation",  "보간 MAE + Detect P/R/F1",                  "ok"],
    ["GET",  "/scenarios",   "Preset scenario library",              "ok"],
    ["GET",  "/health",      "Liveness probe",                       "ok"],
  ];
  const ax = MARGIN + 0.3; const ay = 3.10;
  apis.forEach((a, i) => {
    const y = ay + i * 0.34;
    pill(s, ax, y + 0.04, a[0], a[3] === "crit" ? "crit" : (a[0] === "POST" ? "accent" : "ok"));
    s.addText(a[1], {
      x: ax + 0.75, y, w: 2.0, h: 0.3,
      fontFace: FONTm, fontSize: 11, color: C.text, bold: true,
      valign: "middle", margin: 0,
    });
    s.addText(a[2], {
      x: ax + 2.85, y, w: lw - 3.2, h: 0.3,
      fontFace: FONT, fontSize: 10, color: C.muted,
      valign: "middle", margin: 0,
    });
  });

  // Right: Storage + Worker
  const rx = MARGIN + lw + 0.3;
  const rw = W - rx - MARGIN;

  // Storage card
  card(s, rx, 2.3, rw, 2.15);
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: 2.3, w: 0.08, h: 2.15, fill: { color: C.accent }, line: { width: 0 },
  });
  s.addText("SQLite Store", {
    x: rx + 0.25, y: 2.4, w: rw - 0.4, h: 0.32,
    fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
  });
  s.addText("data/bems.sqlite3  ·  WAL", {
    x: rx + 0.25, y: 2.7, w: rw - 0.4, h: 0.3,
    fontFace: FONTm, fontSize: 9.5, color: C.muted, margin: 0,
  });
  const tables = [
    ["truth",     "Generator's original samples (ground truth)"],
    ["readings",  "Degraded data sent by the Transmitter"],
    ["decisions", "Severity · diagnosis · action results"],
  ];
  tables.forEach((t, i) => {
    const y = 3.10 + i * 0.42;
    s.addText("▸", {
      x: rx + 0.25, y, w: 0.3, h: 0.3,
      fontFace: FONT, fontSize: 11, color: C.accent, bold: true, margin: 0,
    });
    s.addText(t[0], {
      x: rx + 0.5, y, w: 1.3, h: 0.3,
      fontFace: FONTm, fontSize: 11, color: C.text, bold: true, margin: 0,
    });
    s.addText(t[1], {
      x: rx + 0.55, y: y + 0.22, w: rw - 0.8, h: 0.22,
      fontFace: FONT, fontSize: 9, color: C.muted, margin: 0,
    });
  });

  // Worker card
  card(s, rx, 4.6, rw, 2.3);
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: 4.6, w: 0.08, h: 2.3, fill: { color: C.ok }, line: { width: 0 },
  });
  s.addText("Background Worker", {
    x: rx + 0.25, y: 4.7, w: rw - 0.4, h: 0.32,
    fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
  });
  s.addText("1 s interval · push-based", {
    x: rx + 0.25, y: 5.0, w: rw - 0.4, h: 0.3,
    fontFace: FONTm, fontSize: 9.5, color: C.muted, margin: 0,
  });
  s.addText("Runs Stages 4 + 5 on a background thread. Decisions keep being made and persisted to the DB even when the dashboard is closed.\n\n• Processes only new readings\n• On error, records last_error and keeps running\n• Shares the store safely via a dedicated lock", {
    x: rx + 0.25, y: 5.35, w: rw - 0.4, h: 1.55,
    fontFace: FONT, fontSize: 10, color: C.text2, margin: 0, paraSpaceAfter: 3,
  });

  pageFooter(s, 7, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 8 — STAGE 4 (ML Processor)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "06  ·  STAGE 4", "ML Processor — Interpolation + 3-Detector Ensemble",
             "Recover the data that was lost, then catch anomalies in what remains.");

  // Pipeline flow inside the stage
  const fx = MARGIN; const fy = 2.30;
  const fw = W - 2 * MARGIN;
  card(s, fx, fy, fw, 1.20);
  const steps = [
    ["01", "Reindex",   "Fill missing seq rows with NaN to make it continuous"],
    ["02", "Interpolate","Estimate NaN values via linear interpolation"],
    ["03", "Detect",     "Run 3 detectors in parallel"],
    ["04", "Combine",    "Hard OR Z-score OR IForest → anomaly_any"],
  ];
  const stepW = (fw - 0.4) / 4;
  steps.forEach((st, i) => {
    const x = fx + 0.2 + i * stepW;
    s.addText(st[0], {
      x, y: fy + 0.18, w: 0.5, h: 0.35,
      fontFace: FONTm, fontSize: 13, color: C.primary, bold: true, margin: 0,
    });
    s.addText(st[1], {
      x: x + 0.55, y: fy + 0.18, w: stepW - 0.7, h: 0.32,
      fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
    });
    s.addText(st[2], {
      x: x + 0.55, y: fy + 0.50, w: stepW - 0.7, h: 0.55,
      fontFace: FONT, fontSize: 10, color: C.muted, margin: 0,
    });
    if (i < 3) {
      s.addText("→", {
        x: x + stepW - 0.45, y: fy + 0.30, w: 0.4, h: 0.4,
        fontFace: FONT, fontSize: 18, color: C.border, bold: true,
        align: "center", margin: 0,
      });
    }
  });

  // Three detectors
  const dy = 3.7; const dh = 3.2;
  const dw = (W - 2 * MARGIN - 0.6) / 3;
  const detectors = [
    {
      icon: "Z", name: "Robust Z-score",
      sub: "Statistical · univariate",
      color: C.primary, bg: C.primaryBg,
      desc: "Estimates σ robustly via MAD (median absolute deviation). Flags when |z| > 2.5.",
      pros: "• Fast, computed per window\n• A single outlier won't poison the statistics",
    },
    {
      icon: "H", name: "Hard Threshold",
      sub: "Physical-spec based",
      color: C.crit, bg: C.critBg,
      desc: "Directly compares against hard limits from the sensor spec (e.g. power > 8 kW, temp > 30°C).",
      pros: "• Explainable, the domain rule as-is\n• Primary basis for Critical severity",
    },
    {
      icon: "F", name: "IsolationForest",
      sub: "Multivariate · ML",
      color: C.accent, bg: C.accentBg,
      desc: "scikit-learn IsolationForest, contamination=0.05. Flags abnormal multi-sensor patterns.",
      pros: "• Catches patterns no single sensor can\n• n_estimators=80 · trained per zone",
    },
  ];
  detectors.forEach((d, i) => {
    const x = MARGIN + i * (dw + 0.3);
    card(s, x, dy, dw, dh);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: dy, w: dw, h: 0.55, fill: { color: d.bg }, line: { width: 0 },
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.25, y: dy + 0.10, w: 0.4, h: 0.4,
      fill: { color: d.color }, line: { width: 0 },
    });
    s.addText(d.icon, {
      x: x + 0.25, y: dy + 0.10, w: 0.4, h: 0.4,
      fontFace: FONT, fontSize: 14, color: C.white, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(d.name, {
      x: x + 0.75, y: dy + 0.10, w: dw - 0.85, h: 0.25,
      fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
    });
    s.addText(d.sub, {
      x: x + 0.75, y: dy + 0.32, w: dw - 0.85, h: 0.2,
      fontFace: FONT, fontSize: 9.5, color: C.muted, margin: 0, charSpacing: 1,
    });
    s.addText(d.desc, {
      x: x + 0.25, y: dy + 0.75, w: dw - 0.45, h: 1.2,
      fontFace: FONT, fontSize: 10.5, color: C.text2, margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.25, y: dy + 1.95, w: dw - 0.5, h: 0.01,
      fill: { color: C.border }, line: { width: 0 },
    });
    s.addText("Strengths", {
      x: x + 0.25, y: dy + 2.05, w: 2, h: 0.22,
      fontFace: FONT, fontSize: 9, color: C.muted, bold: true, charSpacing: 2, margin: 0,
    });
    s.addText(d.pros, {
      x: x + 0.25, y: dy + 2.3, w: dw - 0.45, h: 0.85,
      fontFace: FONT, fontSize: 10, color: C.text, margin: 0, paraSpaceAfter: 2,
    });
  });

  pageFooter(s, 8, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 9 — STAGE 5 (Decision)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "07  ·  STAGE 5", "Decision — Deterministic Rule Engine",
             "Matches which sensors fired in which direction to infer the root cause.");

  // Top: severity classification
  card(s, MARGIN, 2.3, W - 2 * MARGIN, 1.10);
  s.addText("SEVERITY CLASSIFICATION", {
    x: MARGIN + 0.3, y: 2.4, w: 3.0, h: 0.25,
    fontFace: FONT, fontSize: 9, color: C.muted, bold: true, charSpacing: 3, margin: 0,
  });
  const sevs = [
    { name: "Normal",    desc: "No trigger fired",                                  bg: C.okBg,   fg: C.ok   },
    { name: "Warning",   desc: "Only Z-score or IForest fired",                  bg: C.warnBg, fg: C.warn },
    { name: "Critical",  desc: "Hard-limit breach  or  |z| > 4.0",              bg: C.critBg, fg: C.crit },
  ];
  const sevW = (W - 2 * MARGIN - 0.6) / 3;
  sevs.forEach((sv, i) => {
    const x = MARGIN + 0.3 + i * sevW;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 2.78, w: 1.2, h: 0.42,
      fill: { color: sv.bg }, line: { width: 0 },
    });
    s.addText(sv.name, {
      x, y: 2.78, w: 1.2, h: 0.42,
      fontFace: FONT, fontSize: 11, color: sv.fg, bold: true,
      align: "center", valign: "middle", margin: 0, charSpacing: 2,
    });
    s.addText(sv.desc, {
      x: x + 1.32, y: 2.78, w: sevW - 1.4, h: 0.42,
      fontFace: FONT, fontSize: 11, color: C.text2,
      valign: "middle", margin: 0,
    });
  });

  // Rule engine table — keep clear of the footer (footer divider at y ≈ 7.05)
  card(s, MARGIN, 3.55, W - 2 * MARGIN, 3.0);
  s.addText("RULE ENGINE  ·  9 rules, matched top-down, first match wins", {
    x: MARGIN + 0.3, y: 3.65, w: W - 2 * MARGIN - 0.6, h: 0.3,
    fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
  });

  // table header
  const tx = MARGIN + 0.3; const ty = 4.0;
  const cw = [1.5, 2.6, 1.6, 3.0, 3.4];   // ID, Required, Forbidden, Diagnosis, Action
  let cx = tx;
  const headers = ["RULE ID", "REQUIRED SIGNALS", "FORBIDDEN", "DIAGNOSIS", "RECOMMENDED ACTION"];
  headers.forEach((h, i) => {
    s.addText(h, {
      x: cx, y: ty, w: cw[i], h: 0.28,
      fontFace: FONT, fontSize: 8.5, color: C.muted, bold: true, charSpacing: 2, margin: 0,
    });
    cx += cw[i];
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: tx, y: ty + 0.30, w: W - 2 * MARGIN - 0.6, h: 0.01,
    fill: { color: C.border }, line: { width: 0 },
  });

  const rules = [
    ["fire_risk",        "temp↑ + co2↑",                    "humidity↑",       "Possible fire / thermal event",         "Verify smoke detectors, dispatch inspection"],
    ["hvac_failure",     "temp↑ + humidity↑ + co2↑",        "—",               "HVAC cooling failure",                  "Inspect chiller, switch to backup AHU"],
    ["peak_load",        "power↑",                          "temp↑, co2↑",     "Peak power load event",                 "Identify high-consumption circuit, load shed"],
    ["cold_snap",        "temp↓",                           "—",               "Heating loss / open vent",              "Check heating loop, inspect doors"],
    ["occupancy_spike",  "co2↑ + humidity↑",                "power↑, temp↑",   "Occupancy spike / under-ventilation",   "Raise outdoor-air damper set-point"],
    ["humidity_anomaly", "humidity↑",                       "—",               "Humidity anomaly",                      "Check dehumidifier, water ingress"],
    ["low_humidity",     "humidity↓",                       "—",               "Low humidity / dry air",                "Engage humidifier, check steam pressure"],
    ["co2_only",         "co2↑",                            "—",               "Elevated CO₂",                          "Increase outdoor-air intake"],
    ["temperature_only", "temp↑",                           "—",               "Temperature drift",                     "Verify set-point, inspect VAV box"],
  ];
  const rowH = 0.255;
  rules.forEach((r, i) => {
    const y = ty + 0.40 + i * rowH;
    let x2 = tx;
    s.addText(r[0], {
      x: x2, y, w: cw[0], h: rowH - 0.01,
      fontFace: FONTm, fontSize: 8.5, color: C.primary, bold: true, valign: "middle", margin: 0,
    });
    x2 += cw[0];
    s.addText(r[1], {
      x: x2, y, w: cw[1], h: rowH - 0.01,
      fontFace: FONT, fontSize: 8.5, color: C.text, valign: "middle", margin: 0,
    });
    x2 += cw[1];
    s.addText(r[2], {
      x: x2, y, w: cw[2], h: rowH - 0.01,
      fontFace: FONT, fontSize: 8.5, color: C.muted, valign: "middle", margin: 0,
    });
    x2 += cw[2];
    s.addText(r[3], {
      x: x2, y, w: cw[3], h: rowH - 0.01,
      fontFace: FONT, fontSize: 8.5, color: C.text, bold: true, valign: "middle", margin: 0,
    });
    x2 += cw[3];
    s.addText(r[4], {
      x: x2, y, w: cw[4], h: rowH - 0.01,
      fontFace: FONT, fontSize: 8.5, color: C.text2, valign: "middle", margin: 0,
    });
    if (i < rules.length - 1) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: tx, y: y + rowH - 0.005, w: W - 2 * MARGIN - 0.6, h: 0.004,
        fill: { color: "F4F5F7" }, line: { width: 0 },
      });
    }
  });

  pageFooter(s, 9, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 10 — STAGE 6 (Dashboard overview)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "08  ·  STAGE 6", "Dashboard — Enterprise Operations Console",
             "A six-tab Streamlit console that visualizes live data and accepts user input.");

  const tabs = [
    { num: "01", name: "Operations",    desc: "System health board · 6 service states · decision timeline · per-zone cards",
      color: C.primary, bg: C.primaryBg, icon: "▦" },
    { num: "02", name: "Telemetry",     desc: "Zone selector · 4-sensor live charts · raw vs interpolated · anomaly overlays",
      color: C.primary, bg: C.primaryBg, icon: "📈" },
    { num: "03", name: "Pipeline",      desc: "6-agent topology · each agent's status / KPIs / role / source file",
      color: C.accent,  bg: C.accentBg,  icon: "◆" },
    { num: "04", name: "Alerts",        desc: "Severity · zone 필터 · Diagnose/권고/증거 컬럼 · CSV 내보내기",
      color: C.crit,    bg: C.critBg,    icon: "🚨" },
    { num: "05", name: "Scenario Lab",  desc: "One-click inject of 5 presets · custom sensor-value form · recent injections",
      color: C.ok,      bg: C.okBg,      icon: "🧪" },
    { num: "06", name: "Quality Metrics",desc: "Interpolation MAE table · 4-detector P/R/F1 table · F1 comparison bars",
      color: C.ok,      bg: C.okBg,      icon: "📐" },
  ];

  const tw = (W - 2 * MARGIN - 0.4) / 3;
  const th = 2.10;
  tabs.forEach((t, i) => {
    const col = i % 3; const row = Math.floor(i / 3);
    const x = MARGIN + col * (tw + 0.2);
    const y = 2.30 + row * (th + 0.25);
    card(s, x, y, tw, th);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: tw, h: 0.55, fill: { color: t.bg }, line: { width: 0 },
    });
    s.addText(t.num, {
      x: x + 0.2, y: y + 0.12, w: 0.6, h: 0.32,
      fontFace: FONTm, fontSize: 11, color: t.color, bold: true, margin: 0,
    });
    s.addText(t.name, {
      x: x + 0.7, y: y + 0.10, w: tw - 0.9, h: 0.36,
      fontFace: FONT, fontSize: 15, color: C.text, bold: true,
      valign: "middle", margin: 0,
    });
    s.addText(t.desc, {
      x: x + 0.25, y: y + 0.75, w: tw - 0.45, h: th - 0.85,
      fontFace: FONT, fontSize: 11, color: C.text2,
      valign: "middle", margin: 0,
    });
  });

  pageFooter(s, 10, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 11 — UI MOCKUP: Operations + Alerts
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "UI  TOUR", "Operations  &  Alerts",
             "The two screens operators use to monitor the system and act on alerts.");

  // helper: render an enterprise-style "mock" tab bar inside a card
  const TABS = ["Operations", "Telemetry", "Pipeline", "Alerts", "Lab", "Metrics"];
  const drawMockHeader = (x, y, w, activeIdx) => {
    // appbar
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.1, y: y + 0.1, w: w - 0.2, h: 0.45,
      fill: { color: C.surface2 }, line: { color: C.border, width: 0.5 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.2, y: y + 0.18, w: 0.28, h: 0.28,
      fill: { color: C.primary }, line: { width: 0 },
    });
    s.addText("◆", {
      x: x + 0.2, y: y + 0.18, w: 0.28, h: 0.28,
      fontFace: FONT, fontSize: 11, color: C.white, bold: true, align: "center", valign: "middle", margin: 0,
    });
    s.addText("BEMS · Anomaly Operations Center", {
      x: x + 0.55, y: y + 0.18, w: w - 1.85, h: 0.28,
      fontFace: FONT, fontSize: 10, color: C.text, bold: true, valign: "middle", margin: 0,
    });
    pill(s, x + w - 1.20, y + 0.20, "ALL OK", "ok");
    // tab bar
    const tabBarY = y + 0.65;
    s.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.1, y: tabBarY, w: w - 0.2, h: 0.32,
      fill: { color: C.surface }, line: { color: C.border, width: 0.5 },
    });
    // equal-width tabs across the bar
    const innerW = w - 0.30;
    const tabW = innerW / TABS.length;
    TABS.forEach((t, i) => {
      const tx = x + 0.15 + i * tabW;
      if (i === activeIdx) {
        s.addShape(pres.shapes.RECTANGLE, {
          x: tx, y: tabBarY + 0.03, w: tabW, h: 0.26,
          fill: { color: C.primaryBg }, line: { width: 0 },
        });
      }
      s.addText(t, {
        x: tx, y: tabBarY + 0.03, w: tabW, h: 0.26,
        fontFace: FONT, fontSize: 8,
        color: i === activeIdx ? C.primary : C.muted,
        bold: i === activeIdx,
        align: "center", valign: "middle", margin: 0,
      });
    });
    return tabBarY;
  };

  // === Left mockup: Operations ===
  const lx = MARGIN; const ly = 2.3;
  const lw = (W - 2 * MARGIN - 0.4) / 2;
  card(s, lx, ly, lw, 4.3);
  const tabBarY = drawMockHeader(lx, ly, lw, 0);

  // KPI strip
  const kpis = [
    ["Zones",      "3",   C.primary],
    ["Packets",    "847", C.primary],
    ["Loss",       "11%", C.warn],
    ["Decisions",  "823", C.accent],
    ["Critical",   "12",  C.crit],
    ["Warning",    "47",  C.warn],
  ];
  const kpiY = ly + 1.10;
  const kpiW = (lw - 0.4) / 6;
  kpis.forEach((k, i) => {
    const x = lx + 0.15 + i * kpiW;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: kpiY, w: kpiW - 0.05, h: 0.65,
      fill: { color: C.surface2 }, line: { color: C.border, width: 0.5 },
    });
    s.addText(k[0].toUpperCase(), {
      x, y: kpiY + 0.05, w: kpiW - 0.05, h: 0.22,
      fontFace: FONT, fontSize: 6.5, color: C.muted, bold: true,
      align: "center", margin: 0, charSpacing: 2,
    });
    s.addText(k[1], {
      x, y: kpiY + 0.25, w: kpiW - 0.05, h: 0.38,
      fontFace: FONT, fontSize: 14, color: k[2], bold: true,
      align: "center", valign: "middle", margin: 0,
    });
  });

  // services table mockup
  const svcY = ly + 1.95;
  s.addText("System Services", {
    x: lx + 0.15, y: svcY, w: 3, h: 0.25,
    fontFace: FONT, fontSize: 9.5, color: C.text, bold: true, margin: 0,
  });
  const svcs = [
    ["Generator",    "ok"],
    ["Transmitter",  "ok"],
    ["Collector",    "ok"],
    ["ML Processor", "ok"],
    ["Decision",     "ok"],
    ["Dashboard",    "ok"],
  ];
  svcs.forEach((sv, i) => {
    const y = svcY + 0.30 + i * 0.30;
    s.addShape(pres.shapes.RECTANGLE, {
      x: lx + 0.15, y, w: lw - 0.3, h: 0.26,
      fill: { color: C.surface }, line: { color: C.border, width: 0.4 },
    });
    s.addText(sv[0], {
      x: lx + 0.25, y, w: 2.5, h: 0.26,
      fontFace: FONT, fontSize: 9, color: C.text, bold: true, valign: "middle", margin: 0,
    });
    // pill: explicit width to fit "OPERATIONAL" on a single line
    pill(s, lx + lw - 1.30, y + 0.02, "OPERATIONAL", "ok", { w: 1.10, h: 0.22, fontSize: 7.5 });
  });

  // caption above the card (inside header area), not below colliding with footer
  s.addText("Tab #1  —  Operations View", {
    x: lx, y: ly - 0.30, w: lw, h: 0.26,
    fontFace: FONT, fontSize: 10, color: C.muted, italic: true,
    align: "center", margin: 0,
  });

  // === Right mockup: Alerts ===
  const rx = lx + lw + 0.4;
  card(s, rx, ly, lw, 4.3);
  drawMockHeader(rx, ly, lw, 3);   // Alerts is the 4th tab (index 3)

  // caption above the right card
  s.addText("Tab #4  —  Alerts Feed", {
    x: rx, y: ly - 0.30, w: lw, h: 0.26,
    fontFace: FONT, fontSize: 10, color: C.muted, italic: true,
    align: "center", margin: 0,
  });

  // alert rows
  const alertY = ly + 1.10;
  const alerts = [
    { sev: "Critical", zone: "Zone-A", seq: "33",
      diag: "Possible fire / thermal event",
      act: "Verify smoke detectors; dispatch on-site inspection",
      color: C.crit, kind: "crit" },
    { sev: "Critical", zone: "Zone-B", seq: "28",
      diag: "HVAC cooling failure",
      act: "Inspect chiller, switch to backup AHU",
      color: C.crit, kind: "crit" },
    { sev: "Warning",  zone: "Zone-C", seq: "44",
      diag: "Occupancy spike / under-ventilation",
      act: "Raise outdoor-air damper set-point",
      color: C.warn, kind: "warn" },
    { sev: "Warning",  zone: "Zone-A", seq: "31",
      diag: "Temperature drift",
      act: "Verify set-point, inspect VAV box",
      color: C.warn, kind: "warn" },
  ];
  alerts.forEach((a, i) => {
    const y = alertY + i * 0.74;
    s.addShape(pres.shapes.RECTANGLE, {
      x: rx + 0.15, y, w: lw - 0.3, h: 0.68,
      fill: { color: C.surface }, line: { color: C.border, width: 0.5 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: rx + 0.15, y, w: 0.05, h: 0.68,
      fill: { color: a.color }, line: { width: 0 },
    });
    s.addText("14:23:0" + (5 - i), {
      x: rx + 0.27, y: y + 0.04, w: 0.7, h: 0.22,
      fontFace: FONTm, fontSize: 8, color: C.text, bold: true, margin: 0,
    });
    pill(s, rx + 0.27, y + 0.25, a.sev.toUpperCase(), a.kind,
         { w: 0.9, h: 0.22, fontSize: 7.5 });
    s.addText(`${a.zone} · seq ${a.seq}`, {
      x: rx + 0.27, y: y + 0.48, w: 1.4, h: 0.18,
      fontFace: FONTm, fontSize: 7.5, color: C.muted, margin: 0,
    });
    s.addText(a.diag, {
      x: rx + 1.45, y: y + 0.06, w: lw - 1.65, h: 0.24,
      fontFace: FONT, fontSize: 10, color: C.text, bold: true, margin: 0,
    });
    s.addText("Action: " + a.act, {
      x: rx + 1.45, y: y + 0.30, w: lw - 1.65, h: 0.38,
      fontFace: FONT, fontSize: 8.5, color: C.text2, margin: 0,
    });
  });

  pageFooter(s, 11, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 12 — Scenario Lab + Quality Metrics
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "UI  TOUR", "Scenario Lab  &  Quality Metrics",
             "Inject scenarios yourself and evaluate system quality quantitatively.");

  // === Left: Scenario Lab ===
  const lx = MARGIN; const ly = 2.3;
  const lw = (W - 2 * MARGIN - 0.4) / 2;

  s.addText("Tab #5  —  Scenario Lab", {
    x: lx, y: ly - 0.30, w: lw, h: 0.26,
    fontFace: FONT, fontSize: 10, color: C.muted, italic: true,
    align: "center", margin: 0,
  });
  card(s, lx, ly, lw, 4.4);
  s.addText("Scenario Lab", {
    x: lx + 0.2, y: ly + 0.18, w: lw - 0.4, h: 0.32,
    fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
  });
  s.addText("Controlled Fault Injection", {
    x: lx + 0.2, y: ly + 0.50, w: lw - 0.4, h: 0.25,
    fontFace: FONT, fontSize: 9, color: C.muted, charSpacing: 2, margin: 0,
  });
  s.addText("Push synthetic samples into the pipeline to validate runbooks. Injected samples are labelled as ground-truth anomalies.", {
    x: lx + 0.2, y: ly + 0.80, w: lw - 0.4, h: 0.5,
    fontFace: FONT, fontSize: 9.5, color: C.text2, margin: 0,
  });

  // 5 preset scenarios as cards
  const presets = [
    { tag: "fire_risk",       label: "Fire Risk",        icon: "🔥" },
    { tag: "hvac_failure",    label: "HVAC Failure",     icon: "❄" },
    { tag: "peak_load",       label: "Peak Power Load",  icon: "⚡" },
    { tag: "cold_snap",       label: "Cold Snap",        icon: "🧊" },
    { tag: "occupancy_spike", label: "Occupancy Spike",  icon: "👥" },
  ];
  presets.forEach((p, i) => {
    const y = ly + 1.50 + i * 0.55;
    s.addShape(pres.shapes.RECTANGLE, {
      x: lx + 0.2, y, w: lw - 0.4, h: 0.45,
      fill: { color: C.surface2 }, line: { color: C.border, width: 0.5 },
    });
    s.addText(p.icon, {
      x: lx + 0.3, y, w: 0.5, h: 0.45,
      fontFace: FONT, fontSize: 16, valign: "middle", align: "center", margin: 0,
    });
    s.addText(p.tag, {
      x: lx + 0.85, y: y + 0.06, w: 1.5, h: 0.2,
      fontFace: FONTm, fontSize: 8, color: C.muted, bold: true, charSpacing: 2, margin: 0,
    });
    s.addText(p.label, {
      x: lx + 0.85, y: y + 0.22, w: 2.5, h: 0.22,
      fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
    });
    // "inject" button mock
    s.addShape(pres.shapes.RECTANGLE, {
      x: lx + lw - 1.3, y: y + 0.08, w: 1.0, h: 0.3,
      fill: { color: C.primary }, line: { width: 0 },
    });
    s.addText("Inject", {
      x: lx + lw - 1.3, y: y + 0.08, w: 1.0, h: 0.3,
      fontFace: FONT, fontSize: 9, color: C.white, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
  });

  // === Right: Quality Metrics ===
  const rx = lx + lw + 0.4;

  s.addText("Tab #6  —  Quality Metrics", {
    x: rx, y: ly - 0.30, w: lw, h: 0.26,
    fontFace: FONT, fontSize: 10, color: C.muted, italic: true,
    align: "center", margin: 0,
  });
  card(s, rx, ly, lw, 4.4);
  s.addText("Quality Metrics", {
    x: rx + 0.2, y: ly + 0.18, w: lw - 0.4, h: 0.32,
    fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
  });
  s.addText("Evaluation against ground-truth", {
    x: rx + 0.2, y: ly + 0.50, w: lw - 0.4, h: 0.25,
    fontFace: FONT, fontSize: 9, color: C.muted, charSpacing: 2, margin: 0,
  });

  // section: interpolation MAE table
  s.addText("Interpolation MAE  ·  recovered seqs only", {
    x: rx + 0.2, y: ly + 0.85, w: lw - 0.4, h: 0.25,
    fontFace: FONT, fontSize: 10, color: C.text, bold: true, margin: 0,
  });

  const mae = [
    ["power",       "kW",  "0.31"],
    ["temperature", "°C",  "0.24"],
    ["humidity",    "%",   "1.45"],
    ["co2",         "ppm", "11.8"],
  ];
  const mx = rx + 0.2; const my = ly + 1.15;
  s.addText("SENSOR", { x: mx,        y: my, w: 1.7, h: 0.22, fontFace: FONT, fontSize: 7.5, color: C.muted, bold: true, charSpacing: 2, margin: 0 });
  s.addText("UNIT",   { x: mx + 1.7,  y: my, w: 0.8, h: 0.22, fontFace: FONT, fontSize: 7.5, color: C.muted, bold: true, charSpacing: 2, margin: 0 });
  s.addText("MAE",    { x: mx + 2.5,  y: my, w: 0.8, h: 0.22, fontFace: FONT, fontSize: 7.5, color: C.muted, bold: true, charSpacing: 2, margin: 0 });
  mae.forEach((r, i) => {
    const y = my + 0.28 + i * 0.28;
    s.addText(r[0], { x: mx,       y, w: 1.7, h: 0.25, fontFace: FONT,  fontSize: 9.5, color: C.text, valign: "middle", margin: 0 });
    s.addText(r[1], { x: mx + 1.7, y, w: 0.8, h: 0.25, fontFace: FONT,  fontSize: 9.5, color: C.muted, valign: "middle", margin: 0 });
    s.addText(r[2], { x: mx + 2.5, y, w: 0.8, h: 0.25, fontFace: FONTm, fontSize: 9.5, color: C.primary, bold: true, valign: "middle", margin: 0 });
  });

  // section: F1 bars
  s.addText("Detection F1  ·  vs ground-truth labels", {
    x: rx + 0.2, y: ly + 2.75, w: lw - 0.4, h: 0.25,
    fontFace: FONT, fontSize: 10, color: C.text, bold: true, margin: 0,
  });
  const f1s = [
    ["zscore",         0.72, C.primary],
    ["hard_threshold", 0.91, C.crit],
    ["iforest",        0.68, C.accent],
    ["union",          0.94, C.ok],
  ];
  const bx = rx + 0.2; const by = ly + 3.05;
  const bMax = lw - 0.4 - 1.9;   // leave room for the numeric label
  f1s.forEach((b, i) => {
    const y = by + i * 0.30;
    s.addText(b[0], {
      x: bx, y, w: 1.4, h: 0.26,
      fontFace: FONTm, fontSize: 9, color: C.text, valign: "middle", margin: 0,
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx + 1.4, y: y + 0.05, w: bMax, h: 0.16,
      fill: { color: C.surface2 }, line: { width: 0 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx + 1.4, y: y + 0.05, w: bMax * b[1], h: 0.16,
      fill: { color: b[2] }, line: { width: 0 },
    });
    s.addText(b[1].toFixed(2), {
      x: bx + 1.4 + bMax + 0.05, y, w: 0.4, h: 0.26,
      fontFace: FONTm, fontSize: 9, color: C.text, bold: true, valign: "middle", margin: 0,
    });
  });

  pageFooter(s, 12, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 13 — What you can do (capabilities)
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); lightBg(s);
  pageHeader(s, "09  ·  CAPABILITIES", "What You Can Do With It",
             "Eight things a user can actually do");

  const caps = [
    ["📡", "Real-time monitoring",        "Watch 4-sensor data across 3 zones on 1-second live charts"],
    ["📦", "Packet Loss Recover",         "Auto-interpolate the 10% dropped sequences to remove gaps"],
    ["🔍", "다중 Detect기 비교",       "Apply Z-score · hard threshold · IsolationForest together and compare"],
    ["🧠", "Automatic root-cause inference",     "9개 룰을 매칭하여 어떤 유형의 사고인지 Diagnose + 권고 조치 출력"],
    ["🧪", "시나리오 주입 Testing",   "One-click 5 presets (fire/HVAC/peak/cold/occupancy), or enter custom values"],
    ["📐", "Quantitative quality evaluation",       "Compare interpolation MAE and each detector's P/R/F1 against ground truth"],
    ["📤", "Alert export",          "필터링한 알림 목록을 CSV로 다운로드 (Operate 보고서 생성)"],
    ["🗄", "데이터 Persistence 및 리셋",   "SQLite keeps history across restarts; one-click reset in the sidebar"],
  ];
  const cw = (W - 2 * MARGIN - 0.4) / 2;
  caps.forEach((c, i) => {
    const col = i % 2; const row = Math.floor(i / 2);
    const x = MARGIN + col * (cw + 0.4);
    const y = 2.35 + row * 1.10;
    card(s, x, y, cw, 0.95);
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.20, w: 0.55, h: 0.55,
      fill: { color: C.primaryBg }, line: { width: 0 },
    });
    s.addText(c[0], {
      x: x + 0.2, y: y + 0.20, w: 0.55, h: 0.55,
      fontFace: FONT, fontSize: 18, color: C.primary,
      align: "center", valign: "middle", margin: 0,
    });
    s.addText(c[1], {
      x: x + 0.9, y: y + 0.10, w: cw - 1.1, h: 0.35,
      fontFace: FONT, fontSize: 13, color: C.text, bold: true, margin: 0,
    });
    s.addText(c[2], {
      x: x + 0.9, y: y + 0.42, w: cw - 1.1, h: 0.50,
      fontFace: FONT, fontSize: 10.5, color: C.text2, margin: 0,
    });
  });

  pageFooter(s, 13, TOTAL);
}

// ════════════════════════════════════════════════════════════════════
// SLIDE 14 — Conclusion + Future work
// ════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide(); darkBg(s);
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.05,
    fill: { color: C.primary }, line: { width: 0 },
  });

  s.addText("10  ·  CONCLUSION", {
    x: MARGIN, y: 0.5, w: W - 2 * MARGIN, h: 0.3,
    fontFace: FONT, fontSize: 11, color: "B6C4E5", bold: true, charSpacing: 4, margin: 0,
  });
  s.addText("Achievements & Future Work", {
    x: MARGIN, y: 0.85, w: W - 2 * MARGIN, h: 0.7,
    fontFace: FONT, fontSize: 32, color: C.white, bold: true, margin: 0,
  });

  // Left: Achieved  (height tuned so it doesn't kiss the Thank-you bar)
  const lx = MARGIN; const ly = 2.10;
  const colH = 4.20;
  const colW = (W - 2 * MARGIN - 0.5) / 2;
  s.addShape(pres.shapes.RECTANGLE, {
    x: lx, y: ly, w: colW, h: colH,
    fill: { color: C.navy2 }, line: { color: C.primary, width: 1 },
  });
  s.addText("ACHIEVED", {
    x: lx + 0.3, y: ly + 0.25, w: 3, h: 0.3,
    fontFace: FONT, fontSize: 11, color: C.primary, bold: true, charSpacing: 4, margin: 0,
  });
  s.addText("What the project achieved", {
    x: lx + 0.3, y: ly + 0.60, w: colW - 0.6, h: 0.4,
    fontFace: FONT, fontSize: 17, color: C.white, bold: true, margin: 0,
  });
  const achieved = [
    "Six-Stage Agent Pipeline — 모두 독립 프로세스로 분리",
    "10% Packet Loss + 0.2–1.5s 지연 환경에서 시계열 무결성 유지",
    "3-detector ensemble catches both univariate and multivariate anomalies",
    "9개 룰 엔진으로 결정론적·감사 가능한 Diagnose (블랙박스 X)",
    "엔터프라이즈 톤의 6탭 Operate 콘솔",
    "Pytest 24개 — 데드락 회귀 Testing 포함",
    "Built-in P/R/F1 evaluation against ground-truth labels",
  ];
  achieved.forEach((t, i) => {
    const y = ly + 1.10 + i * 0.40;
    s.addText("✓", {
      x: lx + 0.35, y, w: 0.3, h: 0.34,
      fontFace: FONT, fontSize: 13, color: C.ok, bold: true, valign: "top", margin: 0,
    });
    s.addText(t, {
      x: lx + 0.7, y, w: colW - 0.9, h: 0.38,
      fontFace: FONT, fontSize: 11, color: C.white, valign: "top", margin: 0,
    });
  });

  // Right: Future
  const rx = lx + colW + 0.5;
  s.addShape(pres.shapes.RECTANGLE, {
    x: rx, y: ly, w: colW, h: colH,
    fill: { color: C.navy2 }, line: { color: C.accent, width: 1 },
  });
  s.addText("NEXT", {
    x: rx + 0.3, y: ly + 0.25, w: 3, h: 0.3,
    fontFace: FONT, fontSize: 11, color: "C5B6FF", bold: true, charSpacing: 4, margin: 0,
  });
  s.addText("Where it goes next", {
    x: rx + 0.3, y: ly + 0.60, w: colW - 0.6, h: 0.4,
    fontFace: FONT, fontSize: 17, color: C.white, bold: true, margin: 0,
  });
  const future = [
    "Fit distributions to the real ASHRAE dataset (currently a sin approximation)",
    "Add a time-series model — compare LSTM/AR against IsolationForest",
    "Real-time push over WebSocket (currently polling)",
    "Multi-site expansion and role separation",
    "Alert delivery channels — Slack / email / pager",
    "Grafana / Prometheus metrics export",
    "Agent authentication (/ingest is currently open)",
  ];
  future.forEach((t, i) => {
    const y = ly + 1.10 + i * 0.40;
    s.addText("→", {
      x: rx + 0.35, y, w: 0.3, h: 0.34,
      fontFace: FONT, fontSize: 13, color: C.accent, bold: true, valign: "top", margin: 0,
    });
    s.addText(t, {
      x: rx + 0.7, y, w: colW - 0.9, h: 0.38,
      fontFace: FONT, fontSize: 11, color: C.white, valign: "top", margin: 0,
    });
  });

  // Thank you bar — clearly separated from the columns by ~0.4"
  const tyBar = ly + colH + 0.40;
  s.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: tyBar, w: W - 2 * MARGIN, h: 0.45,
    fill: { color: C.primary }, line: { width: 0 },
  });
  s.addText("Thank you  ·  Q & A", {
    x: MARGIN, y: tyBar, w: W - 2 * MARGIN, h: 0.45,
    fontFace: FONT, fontSize: 14, color: C.white, bold: true,
    align: "center", valign: "middle", margin: 0, charSpacing: 6,
  });

  // dark-mode footer (the standard pageFooter assumes light bg)
  s.addText("BEMS Anomaly Operations Center · ICT Module 4 · Kim Sung-hyun 2021271250", {
    x: MARGIN, y: H - 0.30, w: 8, h: 0.25,
    fontFace: FONT, fontSize: 9, color: "8FA0C8", margin: 0,
  });
  s.addText(`${TOTAL} / ${TOTAL}`, {
    x: W - MARGIN - 1.0, y: H - 0.30, w: 1.0, h: 0.25,
    fontFace: FONT, fontSize: 9, color: "8FA0C8", align: "right", margin: 0,
  });
}

pres.writeFile({ fileName: "BEMS_Presentation_EN.pptx" }).then(p => {
  console.log("wrote", p);
});
