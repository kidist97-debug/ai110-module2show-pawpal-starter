from pawpal_system import (
    Owner, Pet, Task, Scheduler, Priority, Status, Recurrence,
)


def show(title: str, tasks) -> None:
    """Helper to print a labeled list of tasks."""
    print(f"\n{title}")
    for task in tasks:
        stamp = task.time if task.time else "  --  "
        repeat = f" [{task.recurrence.name.lower()}]" if task.recurrence is not Recurrence.NONE else ""
        print(f"  [{stamp}] {task.description} ({task.duration_minutes} min)"
              f" due {task.due_date}{repeat}")


def main() -> None:
    owner = Owner(name="Kidist", email="ktakele@nd.edu")

    rex = Pet(id="p1", name="Rex", species="dog", age=4)
    milo = Pet(id="p2", name="Milo", species="cat", age=2)
    owner.add_pet(rex)
    owner.add_pet(milo)

    # Add tasks intentionally OUT OF ORDER (times are not chronological).
    rex.add_task(Task("Evening walk", duration_minutes=30, time="18:00",
                      recurrence=Recurrence.DAILY))
    rex.add_task(Task("Morning walk", duration_minutes=30, time="07:30",
                      recurrence=Recurrence.DAILY))
    rex.add_task(Task("Feed", duration_minutes=5, time="12:00"))
    milo.add_task(Task("Give medication", duration_minutes=10, time="08:00",
                       priority=Priority.HIGH))
    milo.add_task(Task("Nail trim", duration_minutes=15, time="16:00",
                       recurrence=Recurrence.WEEKLY))

    # Two intentional CLASHES to exercise conflict detection:
    #   - "Brush teeth" (Rex) at 07:30 collides with Rex's morning walk  (same pet)
    #   - "Give vitamin" (Rex) at 08:00 collides with Milo's medication  (different pets)
    rex.add_task(Task("Brush teeth", duration_minutes=5, time="07:30"))
    rex.add_task(Task("Give vitamin", duration_minutes=5, time="08:00"))

    scheduler = Scheduler()

    print("=" * 44)
    print("1. SORTING BY TIME")
    print("=" * 44)

    all_tasks = owner.get_all_tasks()
    show("Insertion order (out of order):", all_tasks)
    show("After sort_by_time():", scheduler.sort_by_time(all_tasks))

    print("\n" + "=" * 44)
    print("2. CONFLICT DETECTION (same-time clashes)")
    print("=" * 44)

    warnings = scheduler.conflict_warnings(owner)
    if warnings:
        print(f"\nFound {len(warnings)} conflict(s):")
        for message in warnings:
            print(f"  {message}")
    else:
        print("\nNo scheduling conflicts.")

    print("\n" + "=" * 44)
    print("3. FILTERING")
    print("=" * 44)

    # Filter by pet name.
    show("Only Rex's tasks:", scheduler.filter_tasks(owner, pet_name="Rex"))

    # Mark one task done, then filter by completion status.
    scheduler.mark_done(owner, milo.tasks[0])  # medication done (one-off, no repeat)
    show("Still pending:", scheduler.filter_tasks(owner, status=Status.PENDING))
    show("Completed:", scheduler.filter_tasks(owner, status=Status.DONE))

    print("\n" + "=" * 44)
    print("4. RECURRING TASKS AUTO-REGENERATE ON COMPLETE")
    print("=" * 44)

    morning_walk = rex.tasks[1]           # daily
    nail_trim = milo.tasks[1]             # weekly
    print(f"\nCompleting '{morning_walk.description}' (daily, due {morning_walk.due_date})...")
    next_walk = scheduler.mark_done(owner, morning_walk)
    print(f"  -> auto-created next: due {next_walk.due_date} (today + 1 day)")

    print(f"\nCompleting '{nail_trim.description}' (weekly, due {nail_trim.due_date})...")
    next_trim = scheduler.mark_done(owner, nail_trim)
    print(f"  -> auto-created next: due {next_trim.due_date} (today + 7 days)")

    show("Rex's tasks now (note the fresh pending walk):",
         scheduler.filter_tasks(owner, pet_name="Rex"))


if __name__ == "__main__":
    main()
