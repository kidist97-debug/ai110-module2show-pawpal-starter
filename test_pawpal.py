from datetime import date, timedelta

import pytest

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    Status,
    Priority,
    Recurrence,
    hhmm_to_minutes,
    minutes_to_hhmm,
)


def make_owner() -> Owner:
    owner = Owner(name="Test", email="test@example.com")
    dog = Pet(id="p1", name="Rex", species="dog", age=4)
    cat = Pet(id="p2", name="Milo", species="cat", age=2)
    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


# --- time helpers ----------------------------------------------------------
def test_minutes_roundtrip():
    assert hhmm_to_minutes("08:30") == 510
    assert minutes_to_hhmm(510) == "08:30"
    assert minutes_to_hhmm(24 * 60 + 15) == "00:15"  # wraps past midnight


# --- sorting by time -------------------------------------------------------
def test_sort_by_time_orders_hhmm_strings():
    tasks = [
        Task("Evening walk", 20, time="18:00"),
        Task("Morning walk", 30, time="07:30"),
        Task("Feed", 5, time="12:00"),
    ]
    ordered = Scheduler().sort_by_time(tasks)
    assert [t.time for t in ordered] == ["07:30", "12:00", "18:00"]


def test_sort_by_time_untimed_tasks_sink_to_end():
    tasks = [Task("Brush", 5, time=""), Task("Walk", 30, time="09:00")]
    ordered = Scheduler().sort_by_time(tasks)
    assert [t.description for t in ordered] == ["Walk", "Brush"]


# --- filtering by pet / status --------------------------------------------
def test_filter_by_pet():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30))
    owner.pets[1].add_task(Task("Litter", 10))
    scheduler = Scheduler()
    assert len(scheduler.filter_tasks(owner, pet_name="Rex")) == 1
    assert len(scheduler.filter_tasks(owner, pet_id="p2")) == 1


def test_filter_by_status():
    owner = make_owner()
    done = Task("Walk", 30)
    done.mark_complete()
    owner.pets[0].add_task(done)
    owner.pets[0].add_task(Task("Feed", 5))
    scheduler = Scheduler()
    assert len(scheduler.pending_tasks(owner)) == 1
    assert len(scheduler.filter_tasks(owner, status=Status.DONE)) == 1


# --- recurring tasks -------------------------------------------------------
def test_recurring_task_expands_to_multiple_occurrences():
    owner = make_owner()
    owner.pets[0].add_task(Task("Feed", 5, time="07:00", times_per_day=3))
    occ = Scheduler().build_day(owner)
    assert len(occ) == 3
    starts = [o.start for o in occ]
    assert starts[0] == "07:00"
    # occurrences are spread out, not stacked on the same time
    assert len(set(starts)) == 3


def test_completed_tasks_excluded_from_timeline():
    owner = make_owner()
    done = Task("Walk", 30, time="08:00")
    done.mark_complete()
    owner.pets[0].add_task(done)
    assert Scheduler().build_day(owner) == []


# --- conflict detection ----------------------------------------------------
def test_find_conflicts_detects_overlap():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="08:00"))   # 08:00-08:30
    owner.pets[1].add_task(Task("Meds", 15, time="08:15"))   # 08:15-08:30
    scheduler = Scheduler()
    conflicts = scheduler.find_conflicts(scheduler.build_day(owner))
    assert len(conflicts) == 1


def test_no_conflict_when_back_to_back():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="08:00"))   # 08:00-08:30
    owner.pets[1].add_task(Task("Meds", 15, time="08:30"))   # 08:30-08:45
    scheduler = Scheduler()
    conflicts = scheduler.find_conflicts(scheduler.build_day(owner))
    assert conflicts == []


# --- lightweight same-time conflict warnings ------------------------------
def test_conflict_warnings_flags_same_time_different_pets():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="08:00"))   # Rex
    owner.pets[1].add_task(Task("Meds", 10, time="08:00"))   # Milo
    warnings = Scheduler().conflict_warnings(owner)
    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "different pets" in warnings[0]


def test_conflict_warnings_flags_same_pet():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="07:30"))
    owner.pets[0].add_task(Task("Brush", 5, time="07:30"))
    warnings = Scheduler().conflict_warnings(owner)
    assert len(warnings) == 1
    assert "same pet" in warnings[0]


def test_conflict_warnings_empty_when_no_clash():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="08:00"))
    owner.pets[1].add_task(Task("Meds", 10, time="09:00"))
    assert Scheduler().conflict_warnings(owner) == []


# --- recurring completion regenerates the task ----------------------------
def test_daily_task_regenerates_one_day_later():
    owner = make_owner()
    walk = Task("Walk", 30, time="08:00", recurrence=Recurrence.DAILY,
                due_date=date(2026, 7, 6))
    owner.pets[0].add_task(walk)
    scheduler = Scheduler()

    follow_up = scheduler.mark_done(owner, walk)

    assert walk.status is Status.DONE
    assert follow_up is not None
    assert follow_up.status is Status.PENDING
    assert follow_up.due_date == date(2026, 7, 7)  # today + 1 day
    # the new instance was appended to the same pet
    assert follow_up in owner.pets[0].tasks
    assert len(owner.pets[0].tasks) == 2


def test_weekly_task_regenerates_seven_days_later():
    owner = make_owner()
    trim = Task("Nail trim", 15, recurrence=Recurrence.WEEKLY,
                due_date=date(2026, 7, 6))
    owner.pets[0].add_task(trim)
    follow_up = Scheduler().mark_done(owner, trim)
    assert follow_up.due_date == date(2026, 7, 6) + timedelta(days=7)


def test_one_off_task_does_not_regenerate():
    owner = make_owner()
    task = Task("Vet visit", 60, recurrence=Recurrence.NONE)
    owner.pets[0].add_task(task)
    follow_up = Scheduler().mark_done(owner, task)
    assert follow_up is None
    assert len(owner.pets[0].tasks) == 1


def test_future_occurrence_excluded_from_today():
    owner = make_owner()
    today = date(2026, 7, 6)
    owner.pets[0].add_task(
        Task("Walk", 30, time="08:00", recurrence=Recurrence.DAILY, due_date=today)
    )
    scheduler = Scheduler()
    scheduler.mark_done(owner, owner.pets[0].tasks[0])
    # tomorrow's regenerated walk must not appear on today's timeline
    assert scheduler.build_day(owner, today=today) == []


# ===========================================================================
# EDGE CASES
# ===========================================================================

# --- empty / degenerate inputs --------------------------------------------
def test_pet_with_no_tasks_produces_empty_day():
    """A pet that has no tasks must not crash build_day or warnings."""
    owner = make_owner()  # two pets, zero tasks
    scheduler = Scheduler()
    assert scheduler.build_day(owner) == []
    assert scheduler.conflict_warnings(owner) == []


def test_owner_with_no_pets_produces_empty_results():
    owner = Owner(name="Nobody", email="nobody@example.com")
    scheduler = Scheduler()
    assert scheduler.get_all_tasks(owner) == []
    assert scheduler.build_day(owner) == []


def test_empty_task_list_sorts_and_finds_no_conflicts():
    scheduler = Scheduler()
    assert scheduler.sort_by_time([]) == []
    assert scheduler.find_conflicts([]) == []


# --- "today" filtering: only PENDING tasks due on/before today -------------
def test_build_day_excludes_done_skipped_and_future_includes_overdue():
    owner = make_owner()
    today = date(2026, 7, 6)

    done = Task("Done walk", 30, time="08:00")
    done.mark_complete()
    skipped = Task("Skipped brush", 5, time="09:00")
    skipped.mark_skipped()
    future = Task("Future vet", 60, time="10:00", due_date=today + timedelta(days=1))
    overdue = Task("Overdue meds", 10, time="11:00", due_date=today - timedelta(days=2))

    for t in (done, skipped, future, overdue):
        owner.pets[0].add_task(t)

    occ = Scheduler().build_day(owner, today=today)
    # only the overdue-but-pending task survives
    assert [o.task.description for o in occ] == ["Overdue meds"]


def test_skipped_task_excluded_from_timeline():
    owner = make_owner()
    task = Task("Brush", 5, time="08:00")
    task.mark_skipped()
    owner.pets[0].add_task(task)
    assert Scheduler().build_day(owner) == []


# --- two tasks at the EXACT same time --------------------------------------
def test_three_tasks_same_time_reported_once_with_count():
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="08:00"))
    owner.pets[0].add_task(Task("Brush", 5, time="08:00"))
    owner.pets[1].add_task(Task("Meds", 10, time="08:00"))
    warnings = Scheduler().conflict_warnings(owner)
    assert len(warnings) == 1
    assert "3 tasks" in warnings[0]
    assert "different pets" in warnings[0]  # Rex + Milo


def test_same_time_flagged_by_both_conflict_paths():
    """A genuine same-time overlap should agree across both detectors."""
    owner = make_owner()
    owner.pets[0].add_task(Task("Walk", 30, time="08:00"))
    owner.pets[1].add_task(Task("Meds", 10, time="08:00"))
    scheduler = Scheduler()
    assert len(scheduler.find_conflicts(scheduler.build_day(owner))) == 1
    assert len(scheduler.conflict_warnings(owner)) == 1


def test_zero_duration_same_time_is_inconsistent_between_detectors():
    """Characterization test for a known inconsistency.

    With duration 0, an occurrence's end == its start. find_conflicts uses
    `second.start >= first.end` and so treats these as NON-overlapping, while
    conflict_warnings (which groups purely by start time) DOES flag them.
    This asserts the current behavior so the gap is visible; if the two
    detectors are ever reconciled, update this test.
    """
    owner = make_owner()
    owner.pets[0].add_task(Task("Instant A", 0, time="08:00"))
    owner.pets[1].add_task(Task("Instant B", 0, time="08:00"))
    scheduler = Scheduler()
    assert scheduler.find_conflicts(scheduler.build_day(owner)) == []      # misses it
    assert len(scheduler.conflict_warnings(owner)) == 1                    # catches it


# --- recurring-task boundaries ---------------------------------------------
def test_times_per_day_zero_yields_single_occurrence():
    owner = make_owner()
    owner.pets[0].add_task(Task("Feed", 5, times_per_day=0))  # no set time
    occ = Scheduler().build_day(owner)
    assert len(occ) == 1
    # a lone untimed task is parked midday within the 07:00-21:00 window
    assert occ[0].start == "14:00"


@pytest.mark.xfail(
    reason="occurrence_starts produces a negative gap when the anchor time is "
    "past DAY_END, so start times run backwards instead of monotonically. "
    "See occurrence_starts() line ~117.",
    strict=True,
)
def test_many_times_per_day_late_anchor_stays_monotonic():
    """times_per_day > 1 anchored after the waking window should not go backwards."""
    task = Task("Feed", 5, time="22:00", times_per_day=3)
    day_start = hhmm_to_minutes(Scheduler.DAY_START)
    day_end = hhmm_to_minutes(Scheduler.DAY_END)
    starts = task.occurrence_starts(day_start, day_end)
    assert starts == sorted(starts), f"start times run backwards: {starts}"


# --- time math crossing midnight -------------------------------------------
def test_late_long_task_end_minutes_do_not_wrap_but_label_does():
    """Characterization test: raw end_minutes stays correct for conflict math,
    but the HH:MM label wraps past midnight (23:00 + 120m -> shows '01:00').
    """
    owner = make_owner()
    owner.pets[0].add_task(Task("Night watch", 120, time="23:00"))
    occ = Scheduler().build_day(owner)[0]
    assert occ.end_minutes == hhmm_to_minutes("23:00") + 120  # 1500, no wrap
    assert occ.end == "01:00"                                 # label wraps
