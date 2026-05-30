# Troubleshooting Log

Real bugs I hit while building the system and how I fixed them. Listed in chronological order — the deadlock was first and most painful.

---

## 1. Collector hangs after ~30 seconds — *every* HTTP endpoint times out

### Symptom

Right after the dashboard connected, the Collector started returning timeouts on **every** endpoint, even ones that should be trivial. The transmitter's `httpx.Client` would log `post failed: timed out` over and over. `curl http://127.0.0.1:8000/stats` would never return. Restarting the collector "fixed" it for ~30 seconds, then it would freeze again.

```
[transmitter] post failed: timed out
[transmitter] sent=18 dropped=5 failed=38
```

But the collector log showed plenty of successful `POST /ingest 200 OK` lines from before the freeze — so uvicorn *was* serving requests, then suddenly stopped.

### Root cause — non-reentrant `threading.Lock` deadlock

In `agents/collector.py` (v1) the `_Store` class used a `threading.Lock()` and the `/stats` endpoint did this:

```python
def stats():
    with self.lock:                    # acquire lock
        buffered = len(self.buffer)
        missing  = len(self.missing()) # ← calls a method that ALSO tries
        ...                            #   to acquire the same lock
```

`threading.Lock` is **not reentrant**: the second `with self.lock:` inside `self.missing()` blocks forever on the same thread that already owns it. The dashboard polled `/stats` every 2 s, so every poll permanently consumed one worker from FastAPI's threadpool. After ~30 calls every worker was stuck → the whole server hung.

### Fix

One-line change:

```python
# was: self.lock = threading.Lock()
self.lock = threading.RLock()   # re-entrant
```

I also added a regression test so this never silently comes back:

```python
# tests/test_store.py
def test_stats_does_not_deadlock(tmp_db):
    """/stats acquired the lock and then called missing_seqs() which also
    took the lock. With a plain Lock this deadlocks forever — must return
    promptly with RLock."""
    for s in [0, 1, 3]:
        tmp_db.insert_reading(_mk("Zone-A", s))
    done: list[dict] = []
    t = threading.Thread(target=lambda: done.append(tmp_db.stats()))
    t.start()
    t.join(timeout=3.0)
    assert not t.is_alive(), "Store.stats() deadlocked"
```

### Lesson

Any class that holds a `Lock` and exposes methods that call **its own other methods** is a deadlock waiting to happen. Default to `RLock` unless you have a specific reason to enforce non-reentrance.

---

## 2. Manual injections quietly created duplicate `seq=0` and the second one was lost

### Symptom

I wiped the store with `/reset`, then `POST /inject` returned `seq=0`. Then I started the transmitter — and a few seconds later the manual injection's data had vanished from `/raw`. The `decisions` table also no longer showed it.

### Root cause — `(row["m"] or -1) + 1` treats `0` as falsy

`store.next_seq()` was supposed to pick the next free seq for a zone:

```python
row = cur.execute("SELECT MAX(seq) AS m FROM readings WHERE zone = ?", (zone,)).fetchone()
base = (row["m"] or -1) + 1
```

When the store was empty `row["m"]` was `None`, so `(None or -1) + 1 = 0`. Good. But after inserting one row at seq=0, `row["m"]` became the integer `0`. In Python, **`0 or -1`** evaluates to `-1` (because `0` is falsy). So `base = -1 + 1 = 0` — the function returned the same seq again, and `INSERT OR REPLACE` happily overwrote the previous row.

### Fix

Stop using the truthy-check shortcut. Be explicit about `None`:

```python
r = cur.execute("SELECT MAX(seq) AS m FROM readings WHERE zone = ?", (zone,)).fetchone()
t = cur.execute("SELECT MAX(seq) AS m FROM truth    WHERE zone = ?", (zone,)).fetchone()
# don't use `... or -1` — seq=0 is falsy and would re-collide.
r_max = r["m"] if r and r["m"] is not None else -1
t_max = t["m"] if t and t["m"] is not None else -1
return int(max(r_max, t_max) + 1)
```

Added a test to lock the behaviour:

```python
def test_next_seq_advances_across_zones(tmp_db):
    assert tmp_db.next_seq("Zone-A") == 0
    tmp_db.insert_reading(_mk("Zone-A", 0))
    assert tmp_db.next_seq("Zone-A") == 1     # ← was 0 before the fix
    assert tmp_db.next_seq("Zone-B") == 0
```

### Lesson

`x or default` is shorthand for "if `x` is **falsy**", not "if `x` is `None`". For numeric values where `0` is a legitimate result, always write `x if x is not None else default`.

---

## 3. Z-score detector poisoned by the very anomalies it was supposed to find

### Symptom

When a sample obviously exceeded a sensor's hard threshold (e.g. `power = 12 kW`, limit `8 kW`), the **hard-threshold** detector correctly flagged it, but the **Z-score** detector did not. After enough anomalies accumulated in the rolling window, even later, smaller spikes stopped triggering. Detection F1 trended down as the window grew.

### Root cause — non-robust mean and stddev

I was using the textbook formula:

```python
mu = series.mean()
sigma = series.std(ddof=0)
z = (series - mu) / sigma
```

The mean and standard deviation are **not robust** — one big outlier pulls `mu` toward itself and inflates `sigma`. With `sigma` inflated, future spikes' z-scores stay below the 2.5 threshold and slip through. Classic *masking effect*.

### Fix

Switched to median and MAD (median absolute deviation), which are robust to up to ~50 % outlier contamination:

```python
med = sub.median()
mad = (sub - med).abs().median().replace(0, np.nan)
sigma = 1.4826 * mad                # MAD → consistent estimator of σ
sigma = sigma.fillna(sub.std(ddof=0)).replace(0, np.nan)
z = (sub - med) / sigma
```

The constant `1.4826` makes MAD an unbiased estimator of standard deviation under a normal distribution. Fallback to the classical stddev only when MAD is exactly zero (i.e. the window is all-equal — never happens with real sensor noise).

### Lesson

Any anomaly detector that uses its own input to estimate "normal" needs to be robust. Mean/stddev are the wrong default for noisy real-world data.

---

## 4. Dashboard timeline rendered Critical alerts as invisible specks

### Symptom

The Operations tab's **Decision Timeline** showed ~150 dots packed across the time axis. Because Normal events outnumbered Critical by 30:1, all of the visual real estate was green dots. The one or two red dots that mattered were the same size and easy to miss entirely.

### Root cause — Plotly Express defaulted to identical marker styles per category

```python
fig = px.scatter(df, x="time", y="zone", color="severity", ...)
fig.update_traces(marker={"size": 12, "opacity": 0.9})
```

Every category gets the same marker recipe. Color alone wasn't enough at this density.

### Fix

Replaced `px.scatter` with explicit `go.Scatter` traces, one per severity, layered from background (Normal) to foreground (Critical), each with **its own size and shape**:

```python
layers = [
    ("Normal",   {"size": 6,  "opacity": 0.30, "symbol": "circle",
                  "line": {"width": 0}}),
    ("Warning",  {"size": 14, "opacity": 0.95, "symbol": "diamond",
                  "line": {"width": 1.5, "color": "white"}}),
    ("Critical", {"size": 18, "opacity": 1.00, "symbol": "star",
                  "line": {"width": 1.8, "color": "#5a1610"}}),
]
```

Plus a toggle to **hide Normal entirely** by default — the operationally relevant view is "show me only what's not normal".

### Lesson

When the cardinality of one category dominates another by 10× or more, color alone won't separate them. Use shape *and* size, and consider a default filter that suppresses the noise.

---

## 5. Streamlit `use_container_width` deprecation noise in the logs

### Symptom

Every dashboard rerender produced 5-10 lines of warning in `logs/dashboard.log`:

```
Please replace `use_container_width` with `width`.
`use_container_width` will be removed after 2025-12-31.
```

### Status

Cosmetic only — the dashboard renders correctly. The replacement (`width='stretch'` / `width='content'`) isn't supported on older Streamlit installs the school lab might have, so I left the deprecated call in place until I can pin a newer Streamlit version everywhere. Will switch in a follow-up.

### Lesson

Not every warning is a bug. Triage by impact: does it break the user? If not, log it and move on.

---

## 6. LibreOffice rendered Korean text with monospaced-looking fonts in the PPT preview

### Symptom

When converting `BEMS_Presentation.pptx` to JPG via `soffice --headless --convert-to pdf` for visual QA, all Korean glyphs rendered with weird wide character spacing that looked like Courier.

### Root cause

LibreOffice on the dev machine didn't have **맑은 고딕** (Malgun Gothic) installed. The font was specified in the pptxgenjs script (`fontFace: "맑은 고딕"`), so LibreOffice silently fell back to a generic monospace.

### Status

**Not a real bug** — it's a preview artifact. In actual PowerPoint on macOS the font falls back to *Apple SD Gothic Neo*, and on Windows it uses the real *맑은 고딕*. Both render cleanly. Only the LibreOffice-based PDF rendering looks off, and that PDF is only used for me to QA the deck, not for the final deliverable.

### Lesson

When rendering tooling differs from the target environment, separate "the deliverable looks wrong" from "the QA preview looks wrong". Verify in the actual target before fixing.
