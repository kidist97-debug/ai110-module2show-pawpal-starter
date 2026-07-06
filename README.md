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

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
