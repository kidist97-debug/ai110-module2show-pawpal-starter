from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


# ---------------------------------------------------------------------------
# Times are stored as "HH:MM" strings (e.g. "08:00"). Zero-padded 24-hour
# strings sort correctly with a plain string comparison, so sorting is easy.
# For time math (recurrence, conflict windows) we convert to minutes.
# ---------------------------------------------------------------------------
def hhmm_to_minutes(hhmm: str) -> int:
    """Convert an 'HH:MM' string into minutes since midnight ('08:30' -> 510)."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def minutes_to_hhmm(minutes: int) -> str:
    """Convert minutes since midnight back into an 'HH:MM' string (wraps at 24h)."""
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class Status(Enum):
    """A task's lifecycle state (richer than a plain done/not-done flag)."""

    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"


class Priority(Enum):
    """How important a task is. Lower value = higher priority (sorts first)."""

    HIGH = 1
    MEDIUM = 2
    LOW = 3


class Recurrence(Enum):
    """How often a task repeats. The value is the day gap to the next due date."""

    NONE = 0     # one-off; does not regenerate
    DAILY = 1    # next due date = today + 1 day
    WEEKLY = 7   # next due date = today + 7 days


@dataclass
class Task:
    """A single pet-care activity."""

    description: str
    duration_minutes: int              # how long one occurrence takes
    time: str = ""                     # preferred start as "HH:MM" ("" = no set time)
    times_per_day: int = 1             # frequency within a day (1, 2, ...)
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    recurrence: Recurrence = Recurrence.NONE   # does this task repeat day-to-day?
    due_date: date = field(default_factory=date.today)  # the day this task is due

    def total_daily_minutes(self) -> int:
        """Total time this task needs per day (duration x times_per_day)."""
        return self.duration_minutes * self.times_per_day

    def next_occurrence(self) -> "Task | None":
        """Build the next repeat of this task, or None if it does not recur.

        The new task is a fresh PENDING copy whose due date is advanced by the
        recurrence gap using timedelta (daily -> +1 day, weekly -> +7 days).
        """
        if self.recurrence is Recurrence.NONE:
            return None
        return Task(
            description=self.description,
            duration_minutes=self.duration_minutes,
            time=self.time,
            times_per_day=self.times_per_day,
            priority=self.priority,
            status=Status.PENDING,
            recurrence=self.recurrence,
            due_date=self.due_date + timedelta(days=self.recurrence.value),
        )

    @property
    def completed(self) -> bool:
        """Backwards-compatible view of status for older callers."""
        return self.status is Status.DONE

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.status = Status.DONE

    def mark_skipped(self) -> None:
        """Mark this task as skipped for today."""
        self.status = Status.SKIPPED

    def occurrence_starts(self, day_start_min: int, day_end_min: int) -> list[int]:
        """Expand a recurring task into concrete start times (in minutes).

        A task that happens ``times_per_day`` times is spread across the
        waking window [day_start_min, day_end_min]. If a preferred
        ``time`` is set, the first occurrence anchors there and the
        rest are spaced evenly through the remaining window.
        """
        n = max(1, self.times_per_day)

        # Step 1: decide where the first occurrence starts.
        if self.time:
            start = hhmm_to_minutes(self.time)      # anchor to the preferred time
        elif n == 1:
            start = (day_start_min + day_end_min) // 2   # park a lone task midday
        else:
            start = day_start_min                   # spread from the start of the day

        # Step 2: spread n occurrences evenly from `start` to the end of the day.
        if n == 1:
            return [start]
        gap = (day_end_min - start) // (n - 1)
        return [start + i * gap for i in range(n)]


@dataclass
class Occurrence:
    """One concrete instance of a task on the timeline (start + end)."""

    task: Task
    pet_name: str
    start_minutes: int

    @property
    def end_minutes(self) -> int:
        """Minute (since midnight) at which this occurrence finishes."""
        return self.start_minutes + self.task.duration_minutes

    @property
    def start(self) -> str:
        """Start time formatted as an 'HH:MM' string."""
        return minutes_to_hhmm(self.start_minutes)

    @property
    def end(self) -> str:
        """End time formatted as an 'HH:MM' string."""
        return minutes_to_hhmm(self.end_minutes)

    def label(self) -> str:
        """One-line timeline label, e.g. '08:00-08:30  Rex: Morning walk'."""
        return f"{self.start}-{self.end}  {self.pet_name}: {self.task.description}"


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    id: str
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        return self.tasks


@dataclass
class Owner:
    """An owner who manages multiple pets."""

    name: str
    email: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


class Scheduler:
    """The 'brain': retrieves, organizes, and manages tasks across pets."""

    # Default waking window ("HH:MM") used when placing tasks on the timeline.
    DAY_START = "07:00"
    DAY_END = "21:00"

    def get_all_tasks(self, owner: Owner) -> list[Task]:
        """Retrieve every task for all of the owner's pets."""
        return owner.get_all_tasks()

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their "HH:MM" time attribute.

        Uses sorted() with a lambda key. Because 24-hour times are zero-padded
        (e.g. "08:00"), comparing them as strings orders them chronologically.
        Untimed tasks (time == "") sort to the end via the "99:99" fallback.
        """
        return sorted(tasks, key=lambda task: task.time or "99:99")

    def filter_tasks(
        self,
        owner: Owner,
        *,
        pet_id: str | None = None,
        pet_name: str | None = None,
        status: Status | None = None,
        priority: Priority | None = None,
    ) -> list[Task]:
        """Flexible filter across all of an owner's tasks.

        Any combination of filters can be supplied; unset filters are ignored.
        """
        results: list[Task] = []
        for pet in owner.pets:
            if pet_id is not None and pet.id != pet_id:
                continue
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.get_tasks():
                if status is not None and task.status is not status:
                    continue
                if priority is not None and task.priority is not priority:
                    continue
                results.append(task)
        return results

    def pending_tasks(self, owner: Owner) -> list[Task]:
        """Return the tasks that still need to be done."""
        return self.filter_tasks(owner, status=Status.PENDING)

    def mark_done(self, owner: Owner, task: Task) -> "Task | None":
        """Mark a task complete and, if it recurs, schedule its next occurrence.

        The new instance (due today+1 for daily, today+7 for weekly) is appended
        to the same pet that owned the original task and returned to the caller.
        Returns None for one-off (non-recurring) tasks.
        """
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is None:
            return None
        for pet in owner.pets:
            if task in pet.tasks:
                pet.add_task(follow_up)
                break
        return follow_up

    def build_day(self, owner: Owner, today: date | None = None) -> list[Occurrence]:
        """Expand every pending task due today into timed occurrences, time-ordered.

        Recurring tasks (times_per_day > 1) become several occurrences spread
        across the waking window. Tasks whose due_date is in the future (e.g. a
        regenerated daily/weekly follow-up) are skipped so they don't show today.
        """
        today = today or date.today()
        day_start = hhmm_to_minutes(self.DAY_START)
        day_end = hhmm_to_minutes(self.DAY_END)

        occurrences: list[Occurrence] = []
        for pet in owner.pets:
            for task in pet.get_tasks():
                if task.status is not Status.PENDING:
                    continue
                if task.due_date > today:
                    continue  # not due yet
                for start in task.occurrence_starts(day_start, day_end):
                    occurrences.append(Occurrence(task, pet.name, start))

        occurrences.sort(key=lambda occ: (occ.start_minutes, occ.task.priority.value))
        return occurrences

    def find_conflicts(
        self, occurrences: list[Occurrence]
    ) -> list[tuple[Occurrence, Occurrence]]:
        """Detect overlapping occurrences via a sorted interval sweep.

        Two occurrences conflict when one starts before the other ends. The
        list is sorted by start time so we can stop comparing as soon as a
        later occurrence begins after the current one ends (O(n log n)).
        """
        ordered = sorted(occurrences, key=lambda occ: occ.start_minutes)
        conflicts: list[tuple[Occurrence, Occurrence]] = []
        for i, first in enumerate(ordered):
            for second in ordered[i + 1:]:
                if second.start_minutes >= first.end_minutes:
                    break  # nothing later can overlap `first`
                conflicts.append((first, second))
        return conflicts

    def conflict_warnings(self, owner: Owner, today: date | None = None) -> list[str]:
        """Lightweight check for tasks scheduled at the SAME start time.

        Groups the day's occurrences by start time and returns a friendly
        warning string for every time slot that has more than one task. This
        never raises — an empty list means "no clashes" — so callers can print
        the warnings without any risk of crashing the program.
        """
        occurrences = self.build_day(owner, today=today)

        by_time: dict[str, list[Occurrence]] = {}
        for occ in occurrences:
            by_time.setdefault(occ.start, []).append(occ)

        warnings: list[str] = []
        for start in sorted(by_time):
            group = by_time[start]
            if len(group) < 2:
                continue
            tasks = ", ".join(f"'{o.task.description}' ({o.pet_name})" for o in group)
            same_pet = len({o.pet_name for o in group}) == 1
            scope = "same pet" if same_pet else "different pets"
            warnings.append(
                f"⚠️  Conflict at {start}: {len(group)} tasks ({scope}) — {tasks}"
            )
        return warnings
