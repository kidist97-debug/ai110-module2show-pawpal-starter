# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

================================
Today's Schedule
================================

Rex (dog)
  - Feed: 10 min x2
  - Morning walk: 30 min

Milo (cat)
  - Give medication: 10 min
  - Play / enrichment: 15 min

--------------------------------
Total time needed today: 65 min
================================


## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest
============================= test session starts ==============================
platform darwin -- Python 3.12.7, pytest-7.4.4, pluggy-1.0.0
rootdir: /Users/kidistmandefrotakele/Desktop/CodePath/AI110/project2/ai110-module2show-pawpal-starter
plugins: anyio-4.2.0
collected 29 items                                                             

test_pawpal.py .........................x.                               [ 93%]
tests/test_pawpal.py ..                                                  [100%]

======================== 28 passed, 1 xfailed in 0.02s =========================


 The suite (29 tests) covers the scheduler's
core behaviors: sorting tasks into chronological order (with untimed tasks sinking
to the end), filtering by pet, status, and priority, and building a day's timeline
that includes only pending tasks due today while excluding done, skipped, and
future-dated ones. It verifies recurrence logic — completing a daily or weekly task
regenerates a fresh copy on the correct future date under the same pet — and
conflict detection, flagging overlapping and exact-same-time tasks while leaving
back-to-back tasks alone. Alongside the happy paths, it exercises edge cases like
empty inputs, zero-duration tasks, and a task crossing midnight. One test is marked
`xfail` to document a known bug where a recurring task anchored after the day's end
produces start times in reverse order.
# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

PawPal+ goes beyond a flat task list with four pieces of scheduling logic. Each
feature and the method that implements it (all in `pawpal_system.py`):

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Orders tasks by their `"HH:MM"` time |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.pending_tasks()` | By pet, completion status, or priority |
| Conflict detection | `Scheduler.conflict_warnings()`, `Scheduler.find_conflicts()` | Same-time clashes (warnings) + duration overlaps |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_done()` | Daily/weekly tasks auto-regenerate on completion |

### Sorting behavior — `Scheduler.sort_by_time()`

Sorts tasks chronologically by their `time` attribute. Because times are stored
as zero-padded 24-hour `"HH:MM"` strings (e.g. `"08:00"`), a plain string
comparison via `sorted(tasks, key=lambda task: task.time or "99:99")` already
orders them correctly. Untimed tasks (`time == ""`) fall back to `"99:99"` so
they sort to the end instead of the front.

### Filtering behavior — `Scheduler.filter_tasks()`

A single flexible method filters an owner's tasks by any combination of
**pet** (`pet_name` or `pet_id`), **completion status** (`Status.PENDING`,
`Status.DONE`, `Status.SKIPPED`), and **priority**. Unset filters are ignored,
so one method covers every combination. `Scheduler.pending_tasks()` is a thin
convenience wrapper for the common "what's still to do?" case.

### Conflict detection — `Scheduler.conflict_warnings()`

The lightweight check groups the day's occurrences by start time and returns a
friendly **warning string** for any slot holding more than one task, labeling
it as a `same pet` or `different pets` clash. It never raises — an empty list
means "no conflicts" — so the program can't crash on a conflict. A heavier
`Scheduler.find_conflicts()` also exists for full duration-overlap detection
(e.g. an 08:00–08:30 task colliding with an 08:15 one) via a sorted interval
sweep.

### Recurring task logic — `Task.next_occurrence()` + `Scheduler.mark_done()`

Each task carries a `Recurrence` (`NONE`, `DAILY`, `WEEKLY`) and a `due_date`.
When a recurring task is completed through `Scheduler.mark_done()`, it calls
`Task.next_occurrence()` to spawn a fresh `PENDING` copy whose due date is
advanced with `timedelta` (daily → +1 day, weekly → +7 days), and appends it to
the same pet. One-off tasks (`Recurrence.NONE`) return `None` and do not repeat.
`Scheduler.build_day()` hides future occurrences so tomorrow's regenerated task
doesn't appear on today's timeline.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. **Set the owner and add a pet.** Launch the app with `streamlit run app.py`,
   edit the owner name at the top, then in *Add a Pet* enter a name, species, and
   age and click **Add pet** — a green `st.success` banner confirms it and the pet
   is listed back.
2. **Add tasks.** In *Add a Task*, pick the pet, then set title, duration,
   times-per-day, priority, and an optional preferred start time. Add a `Morning
   walk` and a `Brush teeth`, both at `07:30`, to create a deliberate clash.
3. **Browse tasks (sorting + filtering).** The *Browse Tasks* section shows tasks
   in a sorted `st.table` (chronological by time, untimed last) and the three
   dropdowns — Pet, Priority, Status — filter the table live via
   `Scheduler.filter_tasks()`.
4. **Generate today's schedule (conflict warnings).** Click **Generate schedule**.
   Because both tasks start at `07:30`, a yellow warning appears *above* the plan —
   *"Conflict at 07:30: 2 tasks (same pet)"* — distinguishing same-pet from
   different-pet clashes, followed by the time-ordered plan table and a total-time
   summary.
5. **Complete a recurring task.** Marking a `DAILY` or `WEEKLY` task done
   regenerates it for the next due date (hidden from today's plan). The same logic
   runs non-interactively in `python main.py`, whose output is:

   ```text
   ============================================
   1. SORTING BY TIME
   ============================================

   After sort_by_time():
     [07:30] Morning walk (30 min) due 2026-07-06 [daily]
     [07:30] Brush teeth (5 min) due 2026-07-06
     [08:00] Give vitamin (5 min) due 2026-07-06
     [08:00] Give medication (10 min) due 2026-07-06
     [12:00] Feed (5 min) due 2026-07-06
     [16:00] Nail trim (15 min) due 2026-07-06 [weekly]
     [18:00] Evening walk (30 min) due 2026-07-06 [daily]

   ============================================
   2. CONFLICT DETECTION (same-time clashes)
   ============================================

   Found 2 conflict(s):
     ⚠️  Conflict at 07:30: 2 tasks (same pet) — 'Morning walk' (Rex), 'Brush teeth' (Rex)
     ⚠️  Conflict at 08:00: 2 tasks (different pets) — 'Give medication' (Milo), 'Give vitamin' (Rex)

   ============================================
   4. RECURRING TASKS AUTO-REGENERATE ON COMPLETE
   ============================================

   Completing 'Morning walk' (daily, due 2026-07-06)...
     -> auto-created next: due 2026-07-07 (today + 1 day)

   Completing 'Nail trim' (weekly, due 2026-07-06)...
     -> auto-created next: due 2026-07-13 (today + 7 days)
   ```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## Features

- **Sorting by time** — Tasks are ordered chronologically with a keyed
  `sorted()` on their `"HH:MM"` strings. Because 24-hour times are zero-padded,
  plain string comparison matches clock order; untimed tasks fall back to
  `"99:99"` so they sink to the end.

- **Flexible filtering** — A single `filter_tasks` pass narrows an owner's tasks
  by any combination of pet (name or id), status, and priority; unset filters are
  ignored. `pending_tasks` is a thin wrapper over it.

- **Daily & weekly recurrence** — Completing a task with `mark_done` marks it DONE
  and regenerates a fresh PENDING copy whose due date is advanced by the
  recurrence gap (+1 day for daily, +7 for weekly) via `timedelta`. One-off tasks
  return `None` and do not regenerate.

- **Intra-day expansion** — A task that happens `times_per_day` times is spread
  evenly across the waking window `[DAY_START, DAY_END]`. The first occurrence
  anchors to the preferred time (or midday for a lone untimed task), and the rest
  are spaced by an even gap.

- **Daily plan building** — `build_day` expands every pending task due on or
  before today into timed `Occurrence`s and sorts them by `(start_minutes,
  priority)`, so earlier tasks come first and ties break by importance. Done,
  skipped, and future-dated tasks are excluded.

- **Conflict detection (overlap sweep)** — `find_conflicts` sorts occurrences by
  start time and does an interval sweep, breaking out of the inner loop as soon as
  a later task begins after the current one ends — catching true overlaps
  (including partial ones) in O(n log n).

- **Conflict warnings (same-time clashes)** — `conflict_warnings` groups the day's
  occurrences by exact start time and emits a friendly message for each slot with
  more than one task, noting whether the clash is on the **same pet** or across
  **different pets**. It never raises, so callers can print results safely.

- **Time arithmetic helpers** — `hhmm_to_minutes` / `minutes_to_hhmm` convert
  between `"HH:MM"` strings and minutes-since-midnight for all recurrence and
  conflict math, wrapping cleanly at 24 hours.
