// BEMS Anomaly Operations Center — ICT Module 4 presentation builder.
// Usage: node build_ppt.js   →   BEMS_Presentation.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";          // 13.3" × 7.5"
pres.author  = "김성현 · 2021271250";
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

const FONT  = "맑은 고딕";  // PowerPoint cross-platform Korean
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
  slide.addText("BEMS Anomaly Operations Center · ICT Module 4 · 김성현 2021271250", {
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
    { text: "김성현  · 2021271250\n", options: { fontFace: FONT, fontSize: 22, color: C.white, bold: true } },
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
  pageHeader(s, "AGENDA", "발표 순서", "오늘 발표는 시스템의 동작 원리와 각 컴포넌트의 기능을 차례로 살펴봅니다.");

  const items = [
    ["01", "프로젝트 개요",         "문제 정의와 해결 접근"],
    ["02", "시스템 아키텍처",        "6단계 에이전트 파이프라인"],
    ["03", "기술 스택",             "사용 라이브러리와 코드 통계"],
    ["04", "Stage 1·2  데이터 생성",  "Generator + Transmitter"],
    ["05", "Stage 3  Collector",     "FastAPI + SQLite 허브"],
    ["06", "Stage 4  ML Processor",  "보간 + 3-detector 앙상블"],
    ["07", "Stage 5  Decision",      "결정론적 룰 엔진"],
    ["08", "Stage 6  Dashboard",     "엔터프라이즈 운영 콘솔"],
    ["09", "핵심 기능 정리",          "이 시스템으로 할 수 있는 일"],
    ["10", "결론 + 향후 과제",        "성과와 다음 단계"],
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
  pageHeader(s, "01  ·  PROJECT OVERVIEW", "스마트 빌딩 에너지 이상 탐지 시스템",
             "왜 이 문제를 풀어야 하고, 어떻게 풀었는가");

  // Two columns: Problem | Solution
  const left = MARGIN;
  const colW = (W - 2 * MARGIN - 0.4) / 2;

  // ── Problem
  card(s, left, 2.3, colW, 4.4);
  s.addShape(pres.shapes.RECTANGLE, {
    x: left, y: 2.3, w: 0.08, h: 4.4, fill: { color: C.crit }, line: { width: 0 },
  });
  s.addText("문제 (Problem)", {
    x: left + 0.3, y: 2.4, w: colW - 0.4, h: 0.4,
    fontFace: FONT, fontSize: 16, color: C.text, bold: true, margin: 0,
  });
  s.addText("스마트 빌딩의 IoT 센서 네트워크는 무선 간섭, 층간 신호 감쇠, 네트워크 혼잡에 시달립니다.", {
    x: left + 0.3, y: 2.85, w: colW - 0.5, h: 0.7,
    fontFace: FONT, fontSize: 12, color: C.text2, margin: 0,
  });

  const problems = [
    ["⚠", "패킷 손실",       "전송 중 데이터가 사라져 분석에 공백이 생긴다"],
    ["⏱", "변동 지연",       "WiFi 혼잡으로 0.5–3초 사이의 불규칙한 지연이 발생"],
    ["📉", "센서 노이즈",    "EM 간섭으로 측정값에 가우시안 잡음이 섞임"],
    ["🔥", "이상 상황 누락",  "운영자가 알아채기 전에 화재, HVAC 고장 등이 진행됨"],
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
  s.addText("해결 (Solution)", {
    x: rx + 0.3, y: 2.4, w: colW - 0.4, h: 0.4,
    fontFace: FONT, fontSize: 16, color: C.text, bold: true, margin: 0,
  });
  s.addText("6단계 에이전트 파이프라인 — 실제 네트워크 열화를 의도적으로 주입하고, ML로 복구하고, 룰 엔진으로 진단합니다.", {
    x: rx + 0.3, y: 2.85, w: colW - 0.5, h: 0.7,
    fontFace: FONT, fontSize: 12, color: C.text2, margin: 0,
  });

  const solutions = [
    ["✓", "복구",     "선형 보간으로 손실 시퀀스를 채워 단절 없는 시계열 확보"],
    ["✓", "탐지",     "Z-score · 하드 임계 · IsolationForest 3-detector 앙상블"],
    ["✓", "진단",     "센서 발생 패턴을 9개 룰과 매칭하여 근본 원인 추정"],
    ["✓", "운영",     "Streamlit 콘솔 — 6탭 운영 화면과 시나리오 주입 기능"],
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
  pageHeader(s, "02  ·  ARCHITECTURE", "6단계 에이전트 파이프라인",
             "각 단계는 독립된 프로세스이며, REST API로만 통신합니다.");

  const stages = [
    { n: "①", name: "Generator",    role: "센서 시뮬레이션",     color: C.primary },
    { n: "②", name: "Transmitter",  role: "네트워크 열화",       color: C.primary },
    { n: "③", name: "Collector",    role: "FastAPI 허브 + DB",   color: C.accent  },
    { n: "④", name: "ML Processor", role: "보간 + 이상 탐지",    color: C.accent  },
    { n: "⑤", name: "Decision",     role: "룰 엔진 진단",        color: C.ok      },
    { n: "⑥", name: "Dashboard",    role: "운영 콘솔",           color: C.ok      },
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
  s.addText("핵심 설계 원칙", {
    x: MARGIN + 0.3, y: 5.5, w: 4, h: 0.32,
    fontFace: FONT, fontSize: 12, color: C.text, bold: true, margin: 0,
  });
  const notes = [
    ["🔌", "REST API 통신",    "에이전트 간 결합도가 낮아 개별 교체·분산 배치 가능"],
    ["💾", "SQLite 영속화",   "WAL 모드로 동시 읽기/쓰기 · 재시작 후 데이터 유지"],
    ["⚙",  "백그라운드 워커",  "Decision은 1초 주기로 push, 대시보드 폴링에 의존하지 않음"],
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
  pageHeader(s, "03  ·  TECH STACK", "기술 스택과 코드 통계",
             "외부 LLM 의존성 없는 순수 룰 엔진 구현");

  // Left: tech stack table-like grid
  const layers = [
    ["언어",           "Python 3.11+",                "타입 힌트 활용 모던 파이썬"],
    ["에이전트 통신",   "FastAPI · httpx",             "REST API · 자동 OpenAPI 문서"],
    ["영속화",         "SQLite (WAL)",                "트랜잭션 · 동시 읽기/쓰기 지원"],
    ["데이터/ML",      "NumPy · pandas · scikit-learn", "롤링 윈도우 · IsolationForest"],
    ["대시보드",       "Streamlit + Plotly",           "라이브 새로고침 · 인터랙티브 차트"],
    ["테스트",         "Pytest",                      "24개 케이스 · 데드락 회귀 포함"],
    ["버전 관리",      "Git",                         "—"],
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
             "센서 데이터를 합성하고, 현실의 네트워크 열화를 의도적으로 주입합니다.");

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
  s.addText("agents/generator.py", {
    x: MARGIN + 0.8, y: 2.75, w: colW - 1, h: 0.3,
    fontFace: FONTm, fontSize: 10, color: C.muted, margin: 0,
  });

  s.addText("3개 zone에 대해 4채널 BEMS 센서를 1초마다 합성", {
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

  s.addText("• 일일 점유율 사이클 (sin) + Gaussian 노이즈\n• 매 샘플마다 ground-truth label (is_anomaly, scenario)\n• 4% 확률로 5개 시나리오 중 하나를 자동 주입", {
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
  s.addText("agents/transmitter.py", {
    x: rx + 0.8, y: 2.75, w: colW - 1, h: 0.3,
    fontFace: FONTm, fontSize: 10, color: C.muted, margin: 0,
  });

  s.addText("Generator 샘플을 받아 의도적으로 망가뜨려 Collector로 전송", {
    x: rx + 0.3, y: 3.15, w: colW - 0.5, h: 0.32,
    fontFace: FONT, fontSize: 11, color: C.text, bold: true, margin: 0,
  });

  // constraints
  const cons = [
    ["⏱", "Transmission Delay", "0.2 – 1.5s 랜덤 지연", "WiFi 혼잡 모사"],
    ["✖", "Packet Drop",         "10% 확률로 패킷 폐기", "층간 신호 감쇠 모사"],
    ["≈", "Sensor Noise",        "Gaussian noise × 1.2", "전자파 간섭 모사"],
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
  pageHeader(s, "05  ·  STAGE 3", "Collector — FastAPI 허브",
             "모든 데이터의 진입점이자 영속 저장소, 그리고 백그라운드 워커의 호스트.");

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
    ["POST", "/truth",       "Generator의 clean 샘플 (평가용)",        "accent"],
    ["POST", "/ingest",      "Transmitter의 열화된 패킷",              "info"],
    ["POST", "/inject",      "사용자 시나리오 또는 커스텀 샘플",        "info"],
    ["POST", "/reset",       "운영 저장소 초기화",                     "crit"],
    ["GET",  "/raw",         "버퍼링된 readings + 결측 seq 리스트",     "ok"],
    ["GET",  "/processed",   "ML 복구 + 이상 플래그 프레임",            "ok"],
    ["GET",  "/decisions",   "Severity + diagnosis + action 히스토리",  "ok"],
    ["GET",  "/stats",       "Zone별 패킷 통계 + 워커 상태",            "ok"],
    ["GET",  "/evaluation",  "보간 MAE + 탐지 P/R/F1",                  "ok"],
    ["GET",  "/scenarios",   "프리셋 시나리오 라이브러리",              "ok"],
    ["GET",  "/health",      "라이브니스 프로브",                       "ok"],
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
    ["truth",     "Generator가 만든 원본 (ground truth)"],
    ["readings",  "Transmitter가 보낸 degraded data"],
    ["decisions", "Severity · diagnosis · action 결과"],
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
  s.addText("1초 주기 · push 방식", {
    x: rx + 0.25, y: 5.0, w: rw - 0.4, h: 0.3,
    fontFace: FONTm, fontSize: 9.5, color: C.muted, margin: 0,
  });
  s.addText("Stage 4 + 5를 백그라운드 스레드에서 실행. 대시보드가 꺼져 있어도 결정은 계속 만들어지고 DB에 영구 기록됨.\n\n• 새 readings만 골라서 처리\n• 예외 발생 시 last_error에 기록 후 계속 동작\n• 별도 lock으로 store와 안전하게 공유", {
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
  pageHeader(s, "06  ·  STAGE 4", "ML Processor — 보간 + 3-Detector 앙상블",
             "잃어버린 데이터는 복구하고, 남은 데이터에서 이상을 잡아냅니다.");

  // Pipeline flow inside the stage
  const fx = MARGIN; const fy = 2.30;
  const fw = W - 2 * MARGIN;
  card(s, fx, fy, fw, 1.20);
  const steps = [
    ["01", "Reindex",   "결측 seq 행을 NaN으로 채워 연속화"],
    ["02", "Interpolate","선형 보간으로 NaN 값 추정"],
    ["03", "Detect",     "3개 detector 병렬 실행"],
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
      sub: "통계 기반 · 단변량",
      color: C.primary, bg: C.primaryBg,
      desc: "MAD(Median Absolute Deviation)로 강건하게 σ를 추정. |z| > 2.5 시 플래그.",
      pros: "• 빠름, 윈도우 단위로 즉시 계산\n• 단일 이상치에 통계가 오염되지 않음",
    },
    {
      icon: "H", name: "Hard Threshold",
      sub: "물리 규격 기반",
      color: C.crit, bg: C.critBg,
      desc: "센서 사양의 하드 임계 (예: power > 8 kW, temp > 30°C)를 직접 비교.",
      pros: "• 설명 가능, 도메인 룰 그대로\n• Critical 등급 판정의 1차 기준",
    },
    {
      icon: "F", name: "IsolationForest",
      sub: "다변량 · ML",
      color: C.accent, bg: C.accentBg,
      desc: "scikit-learn IsolationForest, contamination=0.05. 여러 센서의 결합 패턴이 비정상이면 플래그.",
      pros: "• 단일 센서로는 못 잡는 패턴 포착\n• n_estimators=80 · zone별 학습",
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
    s.addText("강점", {
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
  pageHeader(s, "07  ·  STAGE 5", "Decision — 결정론적 룰 엔진",
             "어느 센서가 어느 방향으로 발화했는지 패턴을 매칭하여 근본 원인을 추정합니다.");

  // Top: severity classification
  card(s, MARGIN, 2.3, W - 2 * MARGIN, 1.10);
  s.addText("SEVERITY CLASSIFICATION", {
    x: MARGIN + 0.3, y: 2.4, w: 3.0, h: 0.25,
    fontFace: FONT, fontSize: 9, color: C.muted, bold: true, charSpacing: 3, margin: 0,
  });
  const sevs = [
    { name: "Normal",    desc: "트리거 없음",                                  bg: C.okBg,   fg: C.ok   },
    { name: "Warning",   desc: "Z-score 또는 IForest만 발화",                  bg: C.warnBg, fg: C.warn },
    { name: "Critical",  desc: "하드 임계 위반  또는  |z| > 4.0",              bg: C.critBg, fg: C.crit },
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
  s.addText("RULE ENGINE  ·  9개 규칙, 위에서부터 매칭, 첫 매치 승", {
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
  pageHeader(s, "08  ·  STAGE 6", "Dashboard — 엔터프라이즈 운영 콘솔",
             "6개 탭으로 분리된 Streamlit 콘솔. 실시간 데이터를 시각화하고 사용자 조작을 받습니다.");

  const tabs = [
    { num: "01", name: "Operations",    desc: "시스템 헬스 보드 · 6개 서비스 상태 · 결정 타임라인 · zone별 카드",
      color: C.primary, bg: C.primaryBg, icon: "▦" },
    { num: "02", name: "Telemetry",     desc: "Zone 선택 · 4센서 실시간 차트 · raw vs interpolated · 이상치 오버레이",
      color: C.primary, bg: C.primaryBg, icon: "📈" },
    { num: "03", name: "Pipeline",      desc: "6개 에이전트 위상도 · 각 에이전트의 상태/KPI/책임/소스 파일",
      color: C.accent,  bg: C.accentBg,  icon: "◆" },
    { num: "04", name: "Alerts",        desc: "Severity · zone 필터 · 진단/권고/증거 컬럼 · CSV 내보내기",
      color: C.crit,    bg: C.critBg,    icon: "🚨" },
    { num: "05", name: "Scenario Lab",  desc: "5개 프리셋 시나리오 원클릭 주입 · 커스텀 센서값 폼 · 최근 주입 이력",
      color: C.ok,      bg: C.okBg,      icon: "🧪" },
    { num: "06", name: "Quality Metrics",desc: "보간 MAE 표 · 4-detector P/R/F1 표 · F1 비교 막대 차트",
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
             "운영자가 시스템을 모니터링하고 알림을 조치하는 두 화면.");

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
    s.addText("권고: " + a.act, {
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
             "사용자가 직접 시나리오를 주입하고, 시스템 품질을 정량적으로 평가합니다.");

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
  pageHeader(s, "09  ·  CAPABILITIES", "이 시스템으로 할 수 있는 일",
             "사용자가 실제로 수행 가능한 작업 8가지");

  const caps = [
    ["📡", "실시간 모니터링",        "3개 zone의 4센서 데이터를 1초 단위 라이브 차트로 관찰"],
    ["📦", "패킷 손실 복구",         "10% 드롭된 시퀀스를 자동으로 보간하여 시계열 단절 제거"],
    ["🔍", "다중 탐지기 비교",       "Z-score · 하드 임계 · IsolationForest 3개를 동시에 적용하고 결과 비교"],
    ["🧠", "근본 원인 자동 추정",     "9개 룰을 매칭하여 어떤 유형의 사고인지 진단 + 권고 조치 출력"],
    ["🧪", "시나리오 주입 테스트",   "5개 프리셋(화재/HVAC/피크/저온/점유) 원클릭, 또는 임의 센서값 직접 입력"],
    ["📐", "정량적 품질 평가",       "보간 MAE와 각 detector의 P/R/F1을 ground truth와 비교"],
    ["📤", "알림 내보내기",          "필터링한 알림 목록을 CSV로 다운로드 (운영 보고서 생성)"],
    ["🗄", "데이터 영속화 및 리셋",   "SQLite로 재시작 후에도 이력 유지, 사이드바에서 원클릭 초기화"],
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
  s.addText("성과와 향후 과제", {
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
  s.addText("프로젝트가 달성한 것", {
    x: lx + 0.3, y: ly + 0.60, w: colW - 0.6, h: 0.4,
    fontFace: FONT, fontSize: 17, color: C.white, bold: true, margin: 0,
  });
  const achieved = [
    "6단계 에이전트 파이프라인 — 모두 독립 프로세스로 분리",
    "10% 패킷 손실 + 0.2–1.5s 지연 환경에서 시계열 무결성 유지",
    "3-detector 앙상블로 단변량/다변량 이상 모두 포착",
    "9개 룰 엔진으로 결정론적·감사 가능한 진단 (블랙박스 X)",
    "엔터프라이즈 톤의 6탭 운영 콘솔",
    "Pytest 24개 — 데드락 회귀 테스트 포함",
    "ground-truth 라벨 기반 P/R/F1 정량 평가 내장",
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
  s.addText("앞으로의 확장 방향", {
    x: rx + 0.3, y: ly + 0.60, w: colW - 0.6, h: 0.4,
    fontFace: FONT, fontSize: 17, color: C.white, bold: true, margin: 0,
  });
  const future = [
    "실제 ASHRAE 데이터셋으로 분포 fit (현재는 sin 근사)",
    "시계열 모델 추가 — LSTM/AR로 IsolationForest와 비교",
    "WebSocket으로 실시간 push (지금은 폴링)",
    "멀티 건물 (multi-site) 확장과 권한 분리",
    "Alert 전송 채널 — Slack / 이메일 / 페이지",
    "Grafana / Prometheus 메트릭 export",
    "에이전트 인증 (현재 /ingest 공개)",
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
  s.addText("BEMS Anomaly Operations Center · ICT Module 4 · 김성현 2021271250", {
    x: MARGIN, y: H - 0.30, w: 8, h: 0.25,
    fontFace: FONT, fontSize: 9, color: "8FA0C8", margin: 0,
  });
  s.addText(`${TOTAL} / ${TOTAL}`, {
    x: W - MARGIN - 1.0, y: H - 0.30, w: 1.0, h: 0.25,
    fontFace: FONT, fontSize: 9, color: "8FA0C8", align: "right", margin: 0,
  });
}

pres.writeFile({ fileName: "BEMS_Presentation.pptx" }).then(p => {
  console.log("wrote", p);
});
