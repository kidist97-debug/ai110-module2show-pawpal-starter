from datetime import date, timedelta

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
